# Getting Started

This guide walks through setting up the HABIT benchmark from scratch, running your first evaluation, and understanding the results.

## Prerequisites

- **Operating System:** Ubuntu 18.04 or later
- **Python:** 3.7 or later
- **GPU:** NVIDIA GPU with compatible drivers (required for CARLA rendering)
- **Docker:** Installed and configured with NVIDIA Container Toolkit (`nvidia-docker`)
- **Disk Space:** approximately 10 GB (CARLA docker image, motion data, and dependencies)

## 1. CARLA 0.9.14 Docker Setup

Pull and start the CARLA 0.9.14 simulator in a Docker container:

```bash
docker pull carlasim/carla:0.9.14
docker run --privileged --gpus all --net=host -e DISPLAY=$DISPLAY carlasim/carla:0.9.14 /bin/bash ./CarlaUE4.sh -RenderOffScreen
```

This launches CARLA in offscreen rendering mode, listening on the default port 2000. Keep this terminal running while you execute the benchmark in a separate terminal.

To verify CARLA is running, you can test the connection from Python:

```python
import carla
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)
print(client.get_server_version())
```

## 2. Clone the Repository and Install Dependencies

```bash
git clone <repository-url> habit
cd habit
pip install -r requirements.txt
```

You also need the CARLA Python API package, which must match the server version:

```bash
pip install carla==0.9.14
```

## 3. Set the PYTHONPATH

The benchmark depends on both the CARLA PythonAPI and the local `scenario_runner` package. Set the required paths before running any evaluation:

```bash
export CARLA_ROOT=/path/to/carla
export PYTHONPATH=$CARLA_ROOT/PythonAPI/carla:$(pwd):$(pwd)/scenario_runner:$PYTHONPATH
```

If you are using the Docker-based CARLA setup without a local CARLA installation, you only need the local paths:

```bash
export PYTHONPATH=$(pwd):$(pwd)/scenario_runner:$PYTHONPATH
```

## 4. Download Motion Data

Download the CARLA-ready motion files from the project's data release (link TBD) and place them in the `data/motions/` directory:

```
habit/
  data/
    motions/          <-- place motion .npy files here
    routes/
      town10_routes.xml
    csvs/
      Crossing.csv
      Attempting.csv
      Not_Crossing.csv
    spawn_points/
      Town10__spawn_points.pkl
```

The `data/routes/`, `data/csvs/`, and `data/spawn_points/` directories are included in the repository.

## 5. Run an Evaluation with the Dummy Agent

The simplest way to verify your setup is to run the included dummy agent, which outputs zero controls (the vehicle remains stationary):

```bash
bash scripts/run_evaluation.sh leaderboard/autoagents/dummy_agent.py
```

This will:
1. Connect to the running CARLA server
2. Load Town10HD routes
3. Spawn pedestrians with motion-captured animations
4. Run the dummy agent through each route
5. Write results to `results/results.json`

## 6. Run with InterFuser or BEVDriver

The paper results use [InterFuser](https://github.com/opendilab/InterFuser) and BEVDriver as the evaluated AD agents. To reproduce these results:

**InterFuser:**

1. Clone and install InterFuser following its repository instructions.
2. Download the InterFuser pretrained weights.
3. Run the evaluation, pointing to the InterFuser agent file and config:

```bash
bash scripts/run_evaluation.sh /path/to/interfuser/agent.py --agent-config /path/to/interfuser/config.yaml
```

**BEVDriver:**

1. Clone and install BEVDriver following its repository instructions.
2. Download the BEVDriver pretrained weights.
3. Run similarly:

```bash
bash scripts/run_evaluation.sh /path/to/bevdriver/agent.py --agent-config /path/to/bevdriver/config.yaml
```

Both agents must implement the `AutonomousAgent` interface described in [custom_agents.md](custom_agents.md).

## 7. Understanding Results

After evaluation completes, results are written to the checkpoint file (default: `results/results.json`). This JSON file contains:

- **Global record:** aggregated scores across all routes
  - `score_composed`: the overall driving score (route completion * infraction penalty)
  - `score_route`: average route completion percentage
  - `score_penalty`: average infraction penalty multiplier
  - Per-km infraction counts (collisions with pedestrians, vehicles, static objects, red lights, stop signs, etc.)
- **Per-route records:** individual route scores, infractions, and metadata (route length, duration)
- **Progress:** how many routes have been completed out of the total

The `StatisticsManager` (in `leaderboard/utils/statistics_manager.py`) handles all scoring computation. See [metrics.md](metrics.md) for a detailed explanation of each metric and how penalties are applied.

A live results file is also written during evaluation (default: `live_results.txt`) showing the current route's score, ego vehicle state, and recent infractions in real time.
