# HABIT - Human Action Benchmark for Interactive Traffic in CARLA

HABIT is a research benchmark for evaluating autonomous driving (AD) agents against realistic, motion-captured pedestrian behaviors in the CARLA 0.9.14 simulator. Unlike standard benchmarks that rely on scripted or ragdoll pedestrian models, HABIT populates the simulation with 4730 CARLA-ready motion files derived from real human motion-capture data, enabling rigorous assessment of how AD agents respond to naturalistic pedestrian crossings, hesitations, and near-miss interactions across 111 routes in CARLA's Town10 map.

## Quick Start

**1. Start CARLA 0.9.14 via Docker**

```bash
docker pull carlasim/carla:0.9.14
docker run --privileged --gpus all --net=host -e DISPLAY=$DISPLAY carlasim/carla:0.9.14 /bin/bash ./CarlaUE4.sh -RenderOffScreen
```

**2. Download motion data**

Download the CARLA-ready motion files and place them in `data/motions/`.

**3. Run evaluation**

```bash
pip install -r requirements.txt
pip install carla==0.9.14
bash scripts/run_evaluation.sh leaderboard/autoagents/dummy_agent.py
```

See [docs/getting_started.md](docs/getting_started.md) for the full setup guide.

## Key Features

- **4730 CARLA-ready motion files** -- motion-captured pedestrian animations converted for CARLA's skeletal system
- **111 Town10 routes** -- diverse evaluation routes across CARLA's Town10HD map with varied weather conditions
- **Motion-captured pedestrian behaviors** -- realistic crossing, attempting-to-cross, and not-crossing behaviors driven by real human motion data
- **Realistic injury metrics (pMAIS3+)** -- probability of Maximum Abbreviated Injury Scale >= 3, computed from collision dynamics using the Yanagisawa logistic model
- **Standard AD metrics** -- driving score, route completion, infraction penalties, collisions per km, and false positive braking rate
- **Behavior CSVs** -- categorized pedestrian behavior labels (Crossing, Attempting, Not_Crossing) for scenario control

## Documentation

- [Getting Started](docs/getting_started.md) -- prerequisites, installation, and first evaluation run
- [Custom Agents](docs/custom_agents.md) -- how to implement and run your own autonomous agent
- [Metrics](docs/metrics.md) -- detailed description of all evaluation metrics and the penalty system

## Citation

```bibtex
@inproceedings{habit2025,
  title={HABIT: Human Action Benchmark for Interactive Traffic in CARLA},
  author={Placeholder Authors},
  booktitle={Proceedings of Placeholder Conference},
  year={2025}
}
```

## Roadmap

1. **Data Processing Pipeline** -- Tools for converting HumanML3D/AMASS motions to CARLA-ready format
2. **Benchmark Generation Tools** -- Scripts for generating new routes, spawn points, behavior CSVs
3. **Animation Improvements** -- Optimized skeletal animation with matrix-based rotation composition

## License

This project is licensed under the MIT License. See [LICENSE](https://opensource.org/licenses/MIT) for details.
