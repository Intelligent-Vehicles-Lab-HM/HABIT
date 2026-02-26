# Getting Started

This guide walks through setting up the HABIT benchmark from scratch, running your first evaluation, and understanding the results.

## Prerequisites

- **Operating System:** Ubuntu 18.04 or later
- **Python:** 3.8
- **GPU:** NVIDIA GPU with compatible drivers (required for CARLA rendering)
- **CARLA 0.9.14:** Docker or native installation (see below)
- **Disk Space:** approximately 10 GB (CARLA, motion data, and dependencies)

## 0. Create the Conda Environment

```bash
conda env create -f environment.yml
conda activate habit
```

This creates a `habit` environment with Python 3.8 and installs all pip dependencies from `requirements.txt`.

> **Note:** If you prefer not to use conda, you can install dependencies directly with `pip install -r requirements.txt` in a Python 3.8 virtualenv.

## 1. CARLA 0.9.14 Setup

### Option A: Docker (recommended)

Pull and start the CARLA 0.9.14 simulator in a Docker container:

```bash
docker pull carlasim/carla:0.9.14
docker run --privileged --gpus all --net=host -e DISPLAY=$DISPLAY \
  carlasim/carla:0.9.14 /bin/bash ./CarlaUE4.sh -RenderOffScreen
```

This launches CARLA in offscreen rendering mode, listening on the default port 2000. Keep this terminal running while you execute the benchmark in a separate terminal.

### Option B: Native installation

If you have a local CARLA 0.9.14 build:

```bash
DISPLAY= ./CarlaUE4.sh -RenderOffScreen -carla-rpc-port=2000
```

To verify CARLA is running, test the connection from Python:

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
conda activate habit
pip install -r requirements.txt
```

## 3. Set the PYTHONPATH

The benchmark depends on both the CARLA PythonAPI and the local `scenario_runner` package. The CARLA PythonAPI is **not** pip-installable — it ships as an `.egg` file inside the CARLA installation directory.

**With a local CARLA installation or Docker volume mount:**

```bash
export CARLA_ROOT=/path/to/carla
export SCENARIO_RUNNER_ROOT=$(pwd)/scenario_runner
export LEADERBOARD_ROOT=$(pwd)
export PYTHONPATH="${CARLA_ROOT}/PythonAPI/carla/:${SCENARIO_RUNNER_ROOT}:${LEADERBOARD_ROOT}:${PYTHONPATH}"
```

**With Docker-only CARLA (no local install):**

You need to extract the CARLA PythonAPI egg from the Docker image:

```bash
# Copy the egg from the container
docker cp <container_id>:/home/carla/PythonAPI/carla/dist/carla-0.9.14-py3.7-linux-x86_64.egg .

# Add it to PYTHONPATH
export PYTHONPATH=$(pwd)/carla-0.9.14-py3.7-linux-x86_64.egg:$(pwd):$(pwd)/scenario_runner:$PYTHONPATH
```

## 4. Download Motion Data

> **Coming soon** — The motion data release is being finalized. The benchmark includes 4,730 curated .pkl files derived from HumanML3D/AMASS motion-capture data. Star & watch this repository for the release announcement.

Once available, download the motion files and place them in the `data/motions/` directory:

```
habit/
  data/
    motions/          <-- place motion .pkl files here
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

> **Without motion data**, the `PedBackgroundBehavior` component will not function (it requires motion files to animate pedestrians). You can still explore the codebase, study the evaluation framework, prepare your agent against the `AutonomousAgent` interface, and run the evaluator with pedestrian spawning disabled.

## 5. Run an Evaluation

### Dummy agent (vehicle stays stationary)

The simplest way to verify your setup is to run the included dummy agent:

```bash
bash scripts/run_evaluation.sh leaderboard/autoagents/dummy_agent.py
```

### NPC agent (drives at 30 km/h using BasicAgent)

```bash
bash scripts/run_evaluation.sh leaderboard/autoagents/npc_agent.py
```

### With a custom config

You can pass a YAML configuration file that controls motion data paths, pedestrian parameters, and other settings:

```bash
CONFIG=path/to/config.yaml bash scripts/run_evaluation.sh leaderboard/autoagents/npc_agent.py
```

Or call the evaluator directly:

```bash
python3 leaderboard/leaderboard_evaluator.py \
    --routes=data/routes/town10_routes.xml \
    --repetitions=1 \
    --track=SENSORS \
    --agent=leaderboard/autoagents/npc_agent.py \
    --checkpoint=results/results.json \
    --config=path/to/config.yaml \
    --debug=0
```

This will:
1. Connect to the running CARLA server
2. Load Town10HD routes
3. Spawn pedestrians with motion-captured animations
4. Run the agent through each route
5. Write results to the checkpoint file

## 6. Run with InterFuser, TransFuser, or BEVDriver

The paper evaluates three state-of-the-art AD agents:

| Agent | Repository | Key Dependency |
|-------|-----------|---------------|
| [InterFuser](https://github.com/opendilab/InterFuser) | opendilab/InterFuser | PyTorch 1.12 |
| [TransFuser](https://github.com/autonomousvision/transfuser) | autonomousvision/transfuser | PyTorch 1.12 |
| [BEVDriver](https://github.com/AlanLiangC/BEVDriver) | AlanLiangC/BEVDriver | PyTorch 2.0 |

Each agent requires its own conda environment due to conflicting PyTorch versions. See [agent_environments.md](agent_environments.md) for detailed setup instructions.

> **Coming soon** — Full integration guides for all three agents are being prepared. The agent interface is documented in [custom_agents.md](custom_agents.md).

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
