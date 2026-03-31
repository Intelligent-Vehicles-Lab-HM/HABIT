# Release Notes

## v1.1.0 — Paper-Aligned Release (2026-03-31)

This release aligns the benchmark with the exact parameters used in the WACV 2026 paper evaluation and makes the motion data publicly available.

### Motion Data

- **4,730 motion-capture .pkl files** now available via [Google Drive](https://drive.google.com/file/d/1L_BPWBYE-Ho5ieSKZSN-LRNP2OfDdVIi/view?usp=sharing)
- Added `scripts/download_motion_data.sh` for automated download
- The benchmark now runs end-to-end out of the box

### Paper-Matched Evaluation Parameters

- Pedestrian activation distance: **15m** from ego vehicle
- Collision freeze threshold: **1.5m** (pedestrian animation pauses near vehicles)
- Frame freeze behavior: animation frame counter pauses on collision instead of advancing
- Idle-only pedestrians: **10** (spawned near route)
- Idle spawn pool restricted to route-filtered spawn points

### Reproducibility

- Added `random.seed(2000)` for deterministic pedestrian spawning
- Seed matches the `CarlaDataProvider._random_seed` convention (numpy RandomState 2000)
- All runs now produce identical pedestrian layouts

### Agent Integration

- Added `set_animations(route_scenario)` API on `AutonomousAgent` base class
- Agents can access pedestrian ground truth via `route_scenario.ped_behavior`
- Added `sensor.camera.semantic_segmentation` support (icon map, sensor limits, preprocessing)

### Documentation

- Paper link updated to official [WACV 2026 open access proceedings](https://openaccess.thecvf.com/content/WACV2026/papers/Ramesh_HABIT_Human_Action_Benchmark_for_Interactive_Traffic_in_CARLA_WACV_2026_paper.pdf)
- BibTeX updated with official citation key, page numbers (7148-7157), and month
- `docs/reproducibility.md` rewritten with full seed documentation
- `docs/custom_agents.md` updated with `set_animations()` and semantic segmentation sensor
- `docs/getting_started.md` updated with motion data download instructions
- `config.yaml` pedestrian parameters updated to match code

### Cleanup

- Removed `paper/HABIT.pdf` (22 MB) from repository — use the open access link instead
- Removed dead code: `leaderboard/scenarios/pedestrian_motion.py` (unused, zero imports)
- Removed commented-out code blocks in `ped_backgound_activity.py`
- Added `*.pdf` and `*.zip` to `.gitignore`
- Fixed LICENSE copyright year (2024 → 2025)
- Fixed LICENSE link in README to point to local file

---

## v1.0.0 — Initial Release (2026-02-26)

Initial public release of the HABIT benchmark framework.

- Benchmark evaluator, scenario runner, and metrics
- 111 Town10HD routes with weather variations
- Behavior CSVs (Crossing, Attempting, Not Crossing)
- Pedestrian spawn points
- NPC and dummy reference agents
- pMAIS3+ injury severity and FPBR metrics
