# Release Notes

## v1.2.0 — Motion Tools (2026-08-02)

This release adds the motion retargeting tools and completes the agent integration guides. Nothing on the roadmap is now outstanding.

### Motion Retargeting Tools

- Added `tools/motion/smpl_to_carla.py` — converts SMPL motion sequences into the runtime `.pkl` format
- Works with any SMPL source: AMASS, HumanML3D, or video lifted with a pose estimator
- Implements Sec. 3.3 of the paper; depends only on NumPy, PyYAML and joblib
- Reads the common `.npz` layouts (AMASS included), retimes clips to the benchmark's 20 Hz, and skips unreadable files rather than aborting a batch
- `--rotation` selects the joint rotation map: `euler` (default) reproduces the released motions, `expmap` applies Eq. 3 literally
- Added `tools/motion/dump_carla_rest_pose.py` for regenerating the rig data for other CARLA versions or walker blueprints

### Documentation

- Added `tools/motion/retargeting_walkthrough.ipynb` — the conversion one equation at a time, with a 3D preview of the result
- Added `tools/motion/README.md`, covering where to obtain SMPL data. HumanML3D cannot be redistributed, so it points at the upstream repository
- Rewrote `docs/agent_environments.md` — third-party agents subclass the CARLA leaderboard's `AutonomousAgent`, which HABIT preserves, so InterFuser, TransFuser and BEVDriver run unmodified. The guides cover the environments and setup each needs instead of shipping copies
- Replaced the roadmap with an "Extending HABIT" section

### Validation

- The five bones with no SMPL counterpart reproduce the rig's rest rotation exactly, matching the released motions
- Converting a known sequence reproduces the pipeline that generated the released set to within float32 rounding
- The released motions were generated against the `male` CARLA rest pose, which is the converter's default

### Removed from Roadmap

- Benchmark generation tools. The generated data ships and is editable in place, and CARLA's own leaderboard tooling covers building new route sets. Results are only comparable across runs sharing a route set, so a fixed benchmark is the intent

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
