"""Driver: classify every perturbed model completion in `results/` into one of the
behaviors defined in `behavior_prompts.py`, using anthropic/claude-sonnet-4.5 via
OpenRouter as the LLM judge. Per-sample output is written to
`behavior_classifications/<model>/<perturbation>/<id>.json` and existing outputs are
skipped (resume support).

Run with the project venv:
    .venv\\Scripts\\activate
    python classify_behaviors.py
Optional CLI args:
    --models <slug> [<slug> ...]      restrict to these model slugs
    --perturbations <name> [<name> ...] restrict to these perturbations
    --batch-size <int>                default 5
    --workers <int>                   default 12
    --dry-run                         print first batch's prompt and exit
"""

import argparse
import json
import os
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from glob import glob

from behavior_prompts import PERTURBATION_SPECS, build_judge_messages
from openrouter import call_openrouter

MODELS = [
    "anthropic_claude_haiku_4_5",
    "anthropic_claude_sonnet_4_5",
    "deepseek_deepseek_v3_2",
    "google_gemini_3_flash_preview",
    "google_gemma_3_4b_it",
    "meta_llama_llama_3_1_8b_instruct",
    "meta_llama_llama_4_scout",
    "mistralai_ministral_3b",
    "mistralai_ministral_8b_2512",
    "mistralai_mistral_large_2512",
    "openai_gpt_4o_mini",
    "openai_gpt_5_2",
    "qwen_qwen3_235b_a22b_2507",
]

PERTURBATIONS = ["MathError", "UnitConvFinal", "Sycophancy", "SkippedSteps", "ExtraSteps"]

JUDGE_MODEL = "anthropic/claude-sonnet-4.5"
RESULTS_DIR = "results"
OUTPUT_DIR = "behavior_classifications"
DEFAULT_BATCH_SIZE = 5
DEFAULT_WORKERS = 12
MAX_RETRIES = 3
BACKOFF_BASE = 2.0

_CLASSIFICATION_RE = re.compile(
    r"<classification>\s*(\[.*?\])\s*</classification>", re.DOTALL
)


def _load_sample(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _output_path(model_slug, perturbation, sample_id):
    return os.path.join(OUTPUT_DIR, model_slug, perturbation, f"{sample_id}.json")


def _extract_classification(raw_response):
    match = _CLASSIFICATION_RE.search(raw_response)
    if not match:
        raise ValueError("no <classification> block found")
    return json.loads(match.group(1))


def _classify_batch(perturbation, batch):
    """Returns (parsed_list, raw_response). Raises on permanent failure."""
    spec = PERTURBATION_SPECS[perturbation]
    valid_labels = {lbl["name"] for lbl in spec["labels"]}
    messages = build_judge_messages(perturbation, batch)

    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            raw = call_openrouter(JUDGE_MODEL, messages)
            parsed = _extract_classification(raw)
            if not isinstance(parsed, list):
                raise ValueError(f"expected list, got {type(parsed).__name__}")
            if len(parsed) != len(batch):
                raise ValueError(
                    f"expected {len(batch)} entries, got {len(parsed)}"
                )
            for entry in parsed:
                if "label" not in entry or "justification" not in entry:
                    raise ValueError(f"entry missing fields: {entry}")
                if entry["label"] not in valid_labels:
                    raise ValueError(
                        f"label '{entry['label']}' not in {sorted(valid_labels)}"
                    )
            return parsed, raw
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE ** attempt)
    raise RuntimeError(f"max retries exhausted; last error: {last_err}")


def _write_sample(model_slug, perturbation, sample, label, justification, raw, batch_id):
    out = {
        "id": sample["id"],
        "model_name": sample.get("model_name"),
        "perturbation_type": sample.get("perturbation_type"),
        "judge_model": JUDGE_MODEL,
        "label": label,
        "justification": justification,
        "batch_id": batch_id,
        "raw_judge_response": raw,
    }
    path = _output_path(model_slug, perturbation, sample["id"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _pending_samples(model_slug, perturbation):
    pattern = os.path.join(RESULTS_DIR, model_slug, perturbation, "*.json")
    paths = sorted(glob(pattern))
    pending = []
    for p in paths:
        sample = _load_sample(p)
        if "completed_solution_perturbed" not in sample:
            continue
        if os.path.exists(_output_path(model_slug, perturbation, sample["id"])):
            continue
        pending.append(sample)
    return pending


def _process_batch(model_slug, perturbation, batch_idx, batch, counters, counters_lock):
    batch_id = f"{model_slug}__{perturbation}__b{batch_idx:04d}"
    try:
        parsed, raw = _classify_batch(perturbation, batch)
        for entry in parsed:
            idx = entry["sample_idx"]
            if not isinstance(idx, int) or idx < 0 or idx >= len(batch):
                raise ValueError(f"bad sample_idx in entry: {entry}")
            sample = batch[idx]
            _write_sample(
                model_slug, perturbation, sample,
                entry["label"], entry["justification"], raw, batch_id,
            )
        with counters_lock:
            counters["ok_batches"] += 1
            counters["ok_samples"] += len(batch)
            for entry in parsed:
                counters["labels"][entry["label"]] = (
                    counters["labels"].get(entry["label"], 0) + 1
                )
        return batch_id, True, None
    except Exception as e:
        for sample in batch:
            _write_sample(
                model_slug, perturbation, sample,
                "JUDGE_FAILED", str(e), "", batch_id,
            )
        with counters_lock:
            counters["fail_batches"] += 1
            counters["fail_samples"] += len(batch)
        return batch_id, False, str(e)


def _process_model_perturbation(model_slug, perturbation, batch_size, workers):
    pending = _pending_samples(model_slug, perturbation)
    if not pending:
        print(f"  [{model_slug} / {perturbation}] no pending samples")
        return

    batches = [pending[i : i + batch_size] for i in range(0, len(pending), batch_size)]
    print(
        f"  [{model_slug} / {perturbation}] {len(pending)} pending samples → "
        f"{len(batches)} batches (workers={workers})"
    )

    counters = {
        "ok_batches": 0, "ok_samples": 0,
        "fail_batches": 0, "fail_samples": 0,
        "labels": {},
    }
    counters_lock = threading.Lock()
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=workers) as exe:
        futures = [
            exe.submit(_process_batch, model_slug, perturbation, i, b, counters, counters_lock)
            for i, b in enumerate(batches)
        ]
        for fut in as_completed(futures):
            batch_id, ok, err = fut.result()
            if not ok:
                print(f"    FAIL {batch_id}: {err[:200]}")

    elapsed = time.time() - t0
    print(
        f"    done in {elapsed:.1f}s | "
        f"ok={counters['ok_samples']} fail={counters['fail_samples']} | "
        f"labels={counters['labels']}"
    )


def _dry_run(perturbation):
    """Print the assembled prompt for the first available batch and exit."""
    for model_slug in MODELS:
        pattern = os.path.join(RESULTS_DIR, model_slug, perturbation, "*.json")
        paths = sorted(glob(pattern))[:DEFAULT_BATCH_SIZE]
        if not paths:
            continue
        batch = [_load_sample(p) for p in paths]
        messages = build_judge_messages(perturbation, batch)
        print(f"=== dry-run: {model_slug} / {perturbation} ({len(batch)} samples) ===\n")
        for m in messages:
            print(f"--- role={m['role']} ---")
            print(m["content"])
            print()
        return
    print(f"no samples found for {perturbation}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=MODELS)
    parser.add_argument("--perturbations", nargs="*", default=PERTURBATIONS)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        _dry_run(args.perturbations[0])
        return

    print(
        f"Judge: {JUDGE_MODEL} | models={len(args.models)} | "
        f"perturbations={args.perturbations} | batch_size={args.batch_size} | "
        f"workers={args.workers}"
    )
    grand_t0 = time.time()
    for model_slug in args.models:
        print(f"\n=== {model_slug} ===")
        for perturbation in args.perturbations:
            _process_model_perturbation(
                model_slug, perturbation, args.batch_size, args.workers,
            )
    print(f"\nTotal wall time: {time.time() - grand_t0:.1f}s")


if __name__ == "__main__":
    main()
