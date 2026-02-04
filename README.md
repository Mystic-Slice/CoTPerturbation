# Fragile Thoughts: How Large Language Models Handle Chain-of-Thought Perturbations
This repository contains code and data for evaluating Large Language Model (LLM) robustness through systematic perturbations on the GSM8K mathematical reasoning benchmark.

## Overview
This project investigates how different perturbation types affect LLM performance on grade school math problems. We introduce controlled modifications to problem statements and solutions to test model sensitivity to various error types.

## Perturbation Types
- **MathError**: Introducing computational errors in reasoning chains
- **UnitConv**: Unit conversion perturbations
- **SkippedSteps**: Omitting intermediate reasoning steps
- **ExtraSteps**: Adding unnecessary intermediate steps to solutions
- **Sycophancy**: Testing model susceptibility to agreeing with incorrect suggestions

## Repository Structure
```
├── completions/
│   ├── results/           # Model outputs organized by provider/model
│   │   ├── anthropic_claude_*/
│   │   ├── deepseek_*/
│   │   ├── google_*/
│   │   ├── meta_llama_*/
│   │   ├── mistralai_*/
│   │   ├── openai_*/
│   │   └── qwen_*/
│   └── result_plots/      # Visualization outputs
│       ├── accuracy_diff_histogram/
│       └── accuracy_vs_model_size/
└── PerturbedDataset_GSM8k/
    ├── gsm_8k/            # Original GSM8K dataset
    ├── ExtraSteps/perturbed/
    ├── MathError/perturbed/
    ├── SkippedSteps/perturbed/
    ├── Sycophancy/perturbed/
    └── UnitConv/perturbed/
```

## Models Evaluated
- **Anthropic**: Claude Haiku 4.5, Claude Sonnet 4.5
- **DeepSeek**: DeepSeek v3.2
- **Google**: Gemini 3 Flash, Gemma 3 4B-it
- **Meta**: Llama 3.1 8B-Instruct, Llama 4 Scout
- **Mistral**: Ministral 3B, Ministral 8B-2512, Mistral Large-2512
- **OpenAI**: GPT 4o-mini, GPT 5.2
- **Qwen**: Qwen3 235B-A22B-2507