# Reproducibility Notes

## Pedestrian Seeding

`PedBackgroundBehavior.initialise()` in `scenario_runner/srunner/scenarios/ped_backgound_activity.py` uses Python's `random` module for:

- `random.sample()` — spawn point selection
- `random.choice()` — walker blueprint, motion file, idle file assignment
- `random.shuffle()` — ambient idle spawn ordering

This is seeded with `random.seed(2000)` at the top of `initialise()`, matching the `CarlaDataProvider._random_seed` convention used elsewhere in the scenario runner.

Animation playback (`update()`) is fully deterministic — once a pedestrian is spawned with a motion file, the frame-by-frame bone animation is identical every time.

**Note:** Python's `random` and `numpy.random` are independent RNGs. The `CarlaDataProvider` uses `numpy.random.RandomState(2000)` for its own scenarios, while `PedBackgroundBehavior` uses Python's built-in `random` module. Both are now seeded to `2000` but are separate streams.

## Seeds in the system

| Component | Seed | Module | Location |
|-----------|------|--------|----------|
| PedBackgroundBehavior | `2000` (Python `random`) | `random.seed(2000)` | `ped_backgound_activity.py:initialise()` |
| CarlaDataProvider RNG | `2000` (`numpy.random.RandomState`) | `CarlaDataProvider._random_seed` | `carla_data_provider.py:67` |
| Traffic Manager | `0` (CLI `--traffic-manager-seed`) | `set_random_device_seed()` | `leaderboard_evaluator.py` |
| World physics | Synchronous mode + fixed 0.05s timestep | `WorldSettings` | `leaderboard_evaluator.py` |
| Deterministic ragdolls | Enabled | `WorldSettings` | `leaderboard_evaluator.py` |
