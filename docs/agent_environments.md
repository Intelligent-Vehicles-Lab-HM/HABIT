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

## How third-party agents fit

HABIT keeps the CARLA leaderboard's `AutonomousAgent` contract — the same `setup()`, `sensors()`,
`run_step()` and `destroy()` methods, with the same sensor specification format. Agents written
against the CARLA leaderboard therefore run here without being rewritten, including InterFuser,
TransFuser and BEVDriver, which all subclass it.

HABIT adds one optional hook, `set_animations()`, which hands the agent the route scenario so it
can read pedestrian ground truth. The base class implements it as a no-op, so agents that ignore
it are unaffected.

This is why we do not ship copies of those agents. Install each from its own repository, where it
is maintained and versioned, and point the evaluator at it. The procedure is the same in every
case:

1. Create the environment for that agent (below) and install it following its own README.
2. Download its pretrained weights from its repository.
3. Put its code on `PYTHONPATH` — these agents import their own `team_code` package.
4. Run the evaluator with `--agent` pointing at its agent file.

Only the dependency set and the location of the weights differ between them.

## InterFuser / TransFuser (`habit-interfuser`)

```bash
conda create -n habit-interfuser python=3.8
conda activate habit-interfuser
pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113
pip install -r requirements.txt
```

Then install the agent from its own repository and download its weights.

Worth knowing before you start:

- Both agents share a dependency set, so one environment covers them.
- InterFuser bundles its own `timm` fork. Install that bundled copy and do **not**
  `pip install timm`, or the model will fail to build.
- InterFuser targets CARLA 0.9.10.1. HABIT runs 0.9.14, so some of its sensor and control calls
  need updating for the newer API.
- InterFuser opens a pygame window for its visualisation. On a headless machine, run it under a
  virtual display or disable that code path.

```bash
export CARLA_ROOT=/path/to/carla
export PYTHONPATH=$CARLA_ROOT/PythonAPI/carla:$(pwd):$(pwd)/scenario_runner:/path/to/InterFuser/leaderboard:$PYTHONPATH

bash scripts/run_evaluation.sh /path/to/InterFuser/leaderboard/team_code/interfuser_agent.py \
    --agent-config /path/to/interfuser_config.py
```

## BEVDriver (`habit-bevdriver`)

```bash
conda create -n habit-bevdriver python=3.8
conda activate habit-bevdriver
pip install torch==2.0.1+cu117 torchvision==0.15.2+cu117 --extra-index-url https://download.pytorch.org/whl/cu117
pip install transformers>=4.28
pip install -r requirements.txt
```

Then install BEVDriver from its own repository and download its checkpoint.

Worth knowing:

- BEVDriver drives a Llama backbone through `transformers` (>= 4.28).
- It needs PyTorch 2.0.1 for the bundled LAVIS library, which is why it cannot share the
  InterFuser environment.
- The language backbone weights are separate from the model checkpoint; both are needed before
  the agent will start.

```bash
export CARLA_ROOT=/path/to/carla
export PYTHONPATH=$CARLA_ROOT/PythonAPI/carla:$(pwd):$(pwd)/scenario_runner:/path/to/BEVDriver:$PYTHONPATH

bash scripts/run_evaluation.sh /path/to/BEVDriver/agent.py \
    --agent-config /path/to/bevdriver_config.yaml
```

These notes describe the setup used for the paper. The upstream repositories will drift over time
— if an agent has moved on, its own README is the authority on installing it, and only steps 3
and 4 above are specific to HABIT.

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
