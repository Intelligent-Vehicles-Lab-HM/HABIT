<div align="center">

# HABIT: Human Action Benchmark for Interactive Traffic in CARLA

**Accepted at WACV 2026** | [Paper](https://openaccess.thecvf.com/content/WACV2026/papers/Ramesh_HABIT_Human_Action_Benchmark_for_Interactive_Traffic_in_CARLA_WACV_2026_paper.pdf) | [arXiv](https://arxiv.org/abs/2511.19109) | [Project Page](https://iv.ee.hm.edu/publications/habit/)

*Realistic motion-captured pedestrian behaviors expose critical failures in autonomous driving agents that remain hidden in scripted simulations.*

<img src="docs/assets/habit_demo.gif" width="600" alt="HABIT benchmark demo showing motion-captured pedestrians in CARLA">

</div>

> **Available** — The benchmark framework, motion data, routes, and behavior labels are ready for evaluation. Agent integration guides are being finalized. Star & watch this repo for updates.

## Why HABIT?

State-of-the-art AD agents achieve near-zero collisions on the CARLA Leaderboard — but when faced with realistic, motion-captured pedestrian behaviors, they fail dramatically:

| Model | Collisions/km | pMAIS3+ (%) | FPBR |
|-------|:---:|:---:|:---:|
| InterFuser | 5.24 | 10.96 | 0.33 |
| TransFuser | 7.43 | 12.94 | 0.12 |
| BEVDriver | 7.19 | 12.35 | — |

*All three agents achieve near-zero collisions/km on standard CARLA benchmarks.*

## Key Features

- **4,730 CARLA-ready motion files** — motion-captured pedestrian animations (from HumanML3D/AMASS) converted for CARLA's skeletal system
- **111 Town10HD routes** — diverse evaluation routes with varied weather conditions
- **Realistic pedestrian behaviors** — crossing, attempting-to-cross, and not-crossing scenarios driven by real human motion data
- **Injury severity metrics (pMAIS3+)** — probability of Maximum Abbreviated Injury Scale >= 3, computed from collision dynamics
- **Standard AD metrics** — driving score, route completion, infraction penalties, collisions per km
- **False Positive Braking Rate (FPBR)** — measures unnecessary braking responses to non-crossing pedestrians
- **Behavior CSVs** — categorized pedestrian behavior labels for scenario control

## Release Status

| Component | Status |
|-----------|--------|
| Benchmark framework (evaluator, scenario runner, metrics) | Available |
| 111 Town10HD routes with weather variations | Available |
| Behavior CSVs (Crossing, Attempting, Not Crossing) | Available |
| Pedestrian spawn points | Available |
| Agent interface + NPC/dummy reference agents | Available |
| pMAIS3+ injury severity + FPBR metrics | Available |
| Motion-capture data (4,730 curated .pkl files) | [Available](https://drive.google.com/file/d/1L_BPWBYE-Ho5ieSKZSN-LRNP2OfDdVIi/view?usp=sharing) |
| InterFuser / TransFuser / BEVDriver integration guides | Coming soon |
| Data processing pipeline (motion retargeting tools) | Coming soon |
| Video-to-motion pipeline | Coming soon |

The benchmark is fully available for evaluation. Download the motion data, start CARLA, and run your agent — see [Getting Started](docs/getting_started.md).

## Quick Start

**1. Create conda environment**

```bash
conda env create -f environment.yml
conda activate habit
```

**2. Start CARLA 0.9.14**

```bash
# Docker
docker pull carlasim/carla:0.9.14
docker run --privileged --gpus all --net=host -e DISPLAY=$DISPLAY \
  carlasim/carla:0.9.14 /bin/bash ./CarlaUE4.sh -RenderOffScreen

# Or native install (see docs/getting_started.md)
```

**3. Set environment and run**

```bash
export CARLA_ROOT=/path/to/carla
export PYTHONPATH=$CARLA_ROOT/PythonAPI/carla:$(pwd):$(pwd)/scenario_runner:$PYTHONPATH

bash scripts/run_evaluation.sh leaderboard/autoagents/npc_agent.py
```

> **Note:** The full benchmark requires motion data in `data/motions/`. Download the 4,730 .pkl files from [Google Drive](https://drive.google.com/file/d/1L_BPWBYE-Ho5ieSKZSN-LRNP2OfDdVIi/view?usp=sharing) and extract them there. See [Getting Started](docs/getting_started.md) for details.

## How It Works

HABIT replaces CARLA's scripted pedestrian AI with motion-captured skeletal animations. Each evaluation route spawns pedestrians at designated points along the ego vehicle's path, playing back real human motion data through CARLA's bone animation system.

```
Route XML + Behavior CSVs + Motion Data
              |
              v
    PedBackgroundBehavior
    (skeletal animation playback)
              |
              v
  CARLA 0.9.14 (Town10HD)  <-->  AD Agent (AutonomousAgent interface)
              |
              v
    Metrics: Driving Score, pMAIS3+, FPBR
```

The evaluator uses the CARLA Leaderboard framework with custom scenario runners that handle pedestrian spawning, animation, and collision-aware injury computation.

## Documentation

- [Getting Started](docs/getting_started.md) — prerequisites, installation, and first evaluation run
- [Custom Agents](docs/custom_agents.md) — how to implement and run your own autonomous agent
- [Agent Environments](docs/agent_environments.md) — separate conda environments for InterFuser, TransFuser, BEVDriver
- [Metrics](docs/metrics.md) — detailed description of all evaluation metrics and the penalty system

## Citation

```bibtex
@InProceedings{Ramesh_2026_WACV,
  author    = {Ramesh, Mohan and Azer, Mark and Flohr, Fabian},
  title     = {{HABIT}: Human Action Benchmark for Interactive Traffic in {CARLA}},
  booktitle = {Proceedings of the IEEE/CVF Winter Conference on Applications of Computer Vision (WACV)},
  month     = {March},
  year      = {2026},
  pages     = {7148-7157}
}
```

## What's New

- **Motion data released** — 4,730 curated .pkl files now [available for download](https://drive.google.com/file/d/1L_BPWBYE-Ho5ieSKZSN-LRNP2OfDdVIi/view?usp=sharing)
- **Paper-matched parameters** — activation distance, collision threshold, and pedestrian counts aligned with WACV 2026 evaluation
- **Reproducible seeding** — deterministic pedestrian spawning via `random.seed(2000)`
- **Semantic segmentation sensor** — agents can now use `sensor.camera.semantic_segmentation`
- **`set_animations()` API** — agents can access pedestrian ground truth for evaluation

## Roadmap

1. **Agent integration guides** — step-by-step setup for InterFuser, TransFuser, BEVDriver
2. **Data processing pipeline** — tools for converting HumanML3D/AMASS motions to CARLA-ready format
3. **Benchmark generation tools** — scripts for generating new routes, spawn points, behavior CSVs
4. **Video-to-motion pipeline** — generate pedestrian motions from video footage

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
