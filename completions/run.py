
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob

# from ollama_completion import  ask_chatollama, ask_kindo
from ollama_completion import ask_openrouter
from functools import partial
from tqdm import tqdm

import json

import os

DATASETS_PATH_BASE = "../../PerturbedDataset_GSM8k/"
DATASETS = [
    ("MathError/perturbed/math_error.csv", "MathError"),
    ("Sycophancy/perturbed/sycophancy.csv", "Sycophancy"),
    ("SkippedSteps/perturbed/skipped_steps.csv", "SkippedSteps"),
    ("ExtraSteps/perturbed/extra_steps.csv", "ExtraSteps"),
    ("UnitConv/perturbed/unit_conv_final.csv", "UnitConvFinal"),
]

def get_df(file_path, perturbation_type):
    df = pd.read_csv(file_path, sep='\t')
    df['perturbation_type'] = perturbation_type
    df = df[:100]
    return df


df = pd.concat([get_df(DATASETS_PATH_BASE + file_path, perturbation_type) for file_path, perturbation_type in DATASETS])


df


df[df['perturbation_type'] == 'SkippedSteps'].iloc[0].perturbed_solution


# Add answer stub to skipped steps
df.loc[df['perturbation_type'] == 'SkippedSteps', 'perturbed_solution'] += "\nTherefore, the answer is:"


df[df['perturbation_type'] == 'SkippedSteps'].iloc[0].perturbed_solution


LLMS = [
    ('openai/gpt-5.2', partial(ask_openrouter, model_name='openai/gpt-5.2')),
    ('anthropic/claude-sonnet-4.5', partial(ask_openrouter, model_name='anthropic/claude-sonnet-4.5')),
    ('anthropic/claude-haiku-4.5', partial(ask_openrouter, model_name='anthropic/claude-haiku-4.5')),
    ('openai/gpt-4o-mini', partial(ask_openrouter, model_name='openai/gpt-4o-mini')),
    ('google/gemini-3-flash-preview', partial(ask_openrouter, model_name='google/gemini-3-flash-preview')),
    ('deepseek/deepseek-v3.2', partial(ask_openrouter, model_name='deepseek/deepseek-v3.2')), # 685B-a37B
    ('mistralai/mistral-large-2512', partial(ask_openrouter, model_name='mistralai/mistral-large-2512')), # 675B-a41B
    ('qwen/qwen3-235b-a22b-2507', partial(ask_openrouter, model_name='qwen/qwen3-235b-a22b-2507')), # 235B-a22B
    ('meta-llama/llama-4-scout', partial(ask_openrouter, model_name='meta-llama/llama-4-scout')), # 109B-a17B
    ('mistralai/ministral-8b-2512', partial(ask_openrouter, model_name='mistralai/ministral-8b-2512')),
    ('meta-llama/llama-3.1-8b-instruct', partial(ask_openrouter, model_name='meta-llama/llama-3.1-8b-instruct')),
    ('google/gemma-3-4b-it', partial(ask_openrouter, model_name='google/gemma-3-4b-it')),
    ('mistralai/ministral-3b', partial(ask_openrouter, model_name='mistralai/ministral-3b')),
]


PROMPT = """
    Complete the solution to the given problem. Think step by step. Provide your final answer within the XML tags <answer>NUMBER</answer> where NUMBER is the final answer. It should be a number without any special characters or spaces or explanations.

    <question>
    {question}
    </question>
    <partial_solution>
    {partial_solution}
    </partial_solution>
"""


PROMPT = """
    Continue and complete the solution to the given problem using the partial solution given to you. Provide your final answer after four hash symbols like this: #### <answer>, where <answer> is the final answer. That final answer should be a number without any special characters or spaces or other explanations.

    Question: {question}
    Partial Solution: {partial_solution}
"""


import re
def extract_answer(s):
    ANS_RE = re.compile(r"#### (\-?[0-9\.\,]+)")
    match = ANS_RE.search(s)
    if match:
        match_str = match.group(1).strip()
        match_str = match_str.replace(",", "")
        return match_str
    else:
        # check if the last part of the string is a number
        match_str = s.split()[-1].strip()
        if re.match(r'(\-?[0-9\.\,]+)', match_str):
            return match_str
    return 'invalid'


def clean_string_for_file_name(s):
    return re.sub(r'[^a-zA-Z0-9]', '_', s)


# idxs = [4240, 4180, 27]

# for idx in idxs:
#     print(len(df[(df['id'] == idx) & (df['perturbation_type'] == 'ExtraSteps')]))
#     row = df[(df['id'] == idx) & (df['perturbation_type'] == 'ExtraSteps')].iloc[0]
#     print(row.perturbation_type)
#     print(row.question)
#     print("-"*50)
#     print(row.clean_solution)
#     print("-"*50)
#     print(row.perturbed_solution)
#     print("="*50)

# idx = int(sys.argv[1])

# llm_name, ask_func = LLMS[idx]

for llm_name, ask_func in LLMS:

    print("Running for LLM:", llm_name)

    output_dir = f"results/{clean_string_for_file_name(llm_name)}"
    for i, row in tqdm(df.iterrows(), total=len(df)):
        d = {
            **row.to_dict(),
            'model_name': llm_name
        }
        save_file_name = f"{output_dir}/{d['perturbation_type']}/{d['id']}.json"

        if os.path.exists(save_file_name):
            print(f"File {save_file_name} already exists. Skipping.")
            continue

        question = row['question']
        clean_partial_solution = row['clean_solution']
        perturbed_partial_solution = row['perturbed_solution']

        response_clean_solution = ask_func(query=PROMPT.format(question=question, partial_solution=clean_partial_solution))
        d['completed_solution_clean'] = response_clean_solution
        d['answer_solution_clean'] = extract_answer(response_clean_solution)

        response_perturbed_solution = ask_func(query=PROMPT.format(question=question, partial_solution=perturbed_partial_solution))
        d['completed_solution_perturbed'] = response_perturbed_solution
        d['answer_solution_perturbed'] = extract_answer(response_perturbed_solution)

        os.makedirs(os.path.dirname(save_file_name), exist_ok=True)
        with open(save_file_name, 'w') as f:
            f.write(json.dumps(d))