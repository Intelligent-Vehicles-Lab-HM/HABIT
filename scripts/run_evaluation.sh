#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

export CARLA_ROOT="${CARLA_ROOT:-/opt/carla}"
export SCENARIO_RUNNER_ROOT="$PROJECT_ROOT/scenario_runner"
export LEADERBOARD_ROOT="$PROJECT_ROOT"
export PYTHONPATH="${CARLA_ROOT}/PythonAPI/carla/:${SCENARIO_RUNNER_ROOT}:${LEADERBOARD_ROOT}:${PYTHONPATH}"

AGENT="${1:-$PROJECT_ROOT/leaderboard/autoagents/dummy_agent.py}"
ROUTES="${ROUTES:-$PROJECT_ROOT/data/routes/town10_routes.xml}"
CHECKPOINT="${CHECKPOINT:-$PROJECT_ROOT/results/results.json}"
REPETITIONS="${REPETITIONS:-1}"
TRACK="${TRACK:-SENSORS}"
RESUME="${RESUME:-False}"

mkdir -p "$(dirname "$CHECKPOINT")"

python3 ${LEADERBOARD_ROOT}/leaderboard/leaderboard_evaluator.py \
    --routes=${ROUTES} \
    --repetitions=${REPETITIONS} \
    --track=${TRACK} \
    --agent=${AGENT} \
    --agent-config="${AGENT_CONFIG:-}" \
    --checkpoint=${CHECKPOINT} \
    --debug=0 \
    --record="${RECORD_PATH:-}" \
    --resume=${RESUME}
