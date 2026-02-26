# Agent Environments

The AD agents evaluated in the HABIT paper have conflicting dependency requirements (different PyTorch versions, bundled libraries, etc.). This guide documents the separate conda environments needed to run each agent.

## Why Separate Environments?

- **InterFuser** and **TransFuser** require PyTorch 1.12.x with CUDA 11.3
- **BEVDriver** requires PyTorch 2.0.x with a Llama backbone via the `transformers` library
- These PyTorch versions cannot coexist in a single environment
- The CARLA 0.9.14 PythonAPI is shared across all environments (added via `PYTHONPATH`)

## Environment Overview

| Environment | Python | PyTorch | Use For |
|---|---|---|---|
| `habit` | 3.8 | none | Core benchmark, NPC agent, custom agents |
| `habit-interfuser` | 3.8 | 1.12.1+cu113 | InterFuser (+ TransFuser, same deps) |
| `habit-bevdriver` | 3.8 | 2.0.1 | BEVDriver (LLM backbone) |

## Base Environment (`habit`)

The base environment runs the benchmark framework, NPC agent, and any custom agent that does not require a deep learning backbone.

```bash
conda env create -f environment.yml
conda activate habit
```

This is the only environment needed if you are:
- Developing and testing a custom agent
- Running the NPC or dummy baseline agents
- Studying the evaluation framework and metrics

## InterFuser / TransFuser (`habit-interfuser`)

> **Coming soon** — Full setup instructions are being prepared.

Key details for early adopters:

- Both InterFuser and TransFuser share the same dependency set (PyTorch 1.12.x, timm)
- InterFuser bundles its own `timm` fork — do **not** install timm from pip
- The original InterFuser targets CARLA 0.9.10.1; adaptation to 0.9.14 is required for HABIT
- Pretrained weights need to be downloaded from the respective repositories

```bash
# Placeholder — full instructions coming soon
conda create -n habit-interfuser python=3.8
conda activate habit-interfuser
pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113
pip install -r requirements.txt
# + InterFuser-specific dependencies
```

## BEVDriver (`habit-bevdriver`)

> **Coming soon** — Full setup instructions are being prepared.

Key details for early adopters:

- BEVDriver uses a Llama language model backbone via the `transformers` library (>=4.28)
- Requires PyTorch 2.0.1 for compatibility with the LAVIS library (bundled in BEVDriver)
- Pretrained weights need to be downloaded from the BEVDriver repository

```bash
# Placeholder — full instructions coming soon
conda create -n habit-bevdriver python=3.8
conda activate habit-bevdriver
pip install torch==2.0.1+cu117 torchvision==0.15.2+cu117 --extra-index-url https://download.pytorch.org/whl/cu117
pip install transformers>=4.28
pip install -r requirements.txt
# + BEVDriver-specific dependencies
```

## Running Agents

Regardless of which environment you use, the evaluation command is the same:

```bash
conda activate <environment-name>

export CARLA_ROOT=/path/to/carla
export PYTHONPATH=$CARLA_ROOT/PythonAPI/carla:$(pwd):$(pwd)/scenario_runner:$PYTHONPATH

bash scripts/run_evaluation.sh /path/to/agent.py
```

The `--agent-config` flag can be passed for agent-specific configuration:

```bash
bash scripts/run_evaluation.sh /path/to/agent.py --agent-config /path/to/config.yaml
```

See [custom_agents.md](custom_agents.md) for the full `AutonomousAgent` interface specification.
