# Reproducibility Notes

## Pedestrian Seeding (Open Issue)

`PedBackgroundBehavior.initialise()` in `scenario_runner/srunner/scenarios/ped_backgound_activity.py` uses Python's `random` module for:

- `random.sample()` — spawn point selection (line 99)
- `random.choice()` — walker blueprint, motion file, idle file assignment (lines 100, 105, 106, 145, 150)
- `random.shuffle()` — ambient idle spawn ordering (line 131)

This is **not seeded**. Each run may assign different motions to different spawn points.

Animation playback (`update()`) is fully deterministic — once a pedestrian is spawned with a motion file, the frame-by-frame bone animation is identical every time.

### Fix (not yet applied)

Add `random.seed(42)` at the top of `initialise()` to make spawn/motion assignment reproducible. Consider making the seed configurable via `config.yaml`.

### Other seeds in the system

| Component | Seed | Location |
|-----------|------|----------|
| CarlaDataProvider RNG | `2000` (hardcoded numpy RandomState) | `srunner/scenariomanager/carla_data_provider.py:67` |
| Traffic Manager | `0` (CLI `--traffic-manager-seed`) | `leaderboard/leaderboard_evaluator.py:228` |
| World physics | Synchronous mode + fixed 0.05s timestep | `leaderboard/leaderboard_evaluator.py:177` |
| Deterministic ragdolls | Enabled | `leaderboard/leaderboard_evaluator.py:180` |
