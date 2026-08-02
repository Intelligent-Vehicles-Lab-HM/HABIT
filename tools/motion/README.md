# Motion tools

Convert SMPL motion sequences into the `.pkl` files HABIT animates its pedestrians from.

The benchmark ships with 4,730 motions already converted, so these tools are only needed if you
want to add your own. Everything here starts from SMPL: whatever produces your motion — a mocap
dataset, a text-to-motion model, a video — the conversion is the same once it reaches SMPL
axis-angle.

## Getting SMPL data

HABIT's released motions come from HumanML3D. That dataset cannot be redistributed: because of
AMASS licensing it ships as source pointers and processing scripts rather than motion files, so
you build it yourself.

| Source | How to get it |
|---|---|
| **HumanML3D** | Follow the setup in [the HumanML3D repository](https://github.com/EricGuo5513/HumanML3D). Its scripts produce SMPL motions from AMASS. |
| **AMASS** | Download `.npz` sequences from [amass.is.tue.mpg.de](https://amass.is.tue.mpg.de/) under their licence. Readable directly. |
| **Video** | Lift footage to SMPL with a pose estimator such as [WHAM](https://github.com/yohanshin/WHAM), then convert its output. |

Whichever you use, you need the pose in axis-angle form. Anything from 66 values per frame
upward works — extra SMPL-H/X joints are ignored.

## Converting

```bash
# one file
python3 tools/motion/smpl_to_carla.py motion.npz -o data/motions/000001.pkl

# a directory, one .pkl per input
python3 tools/motion/smpl_to_carla.py /path/to/smpl/ -o data/motions/
```

Input is a `.npz` holding an axis-angle pose array and, optionally, root translation and a frame
rate. Common key names are recognised — `poses`/`pose_body`/`pose_world`/`pose`,
`trans`/`transl`/`trans_world`, and `mocap_framerate`/`fps`. AMASS files work as they are.

Clips are retimed to 20 Hz to match the benchmark's animation rate. Retiming picks nearest source
frames rather than blending rotations. Files that cannot be read are reported and skipped, so one
bad file will not stop a batch.

**Frame rate matters.** The runtime advances one animation frame every 0.05 s, so a clip that is
not at 20 Hz plays at the wrong speed — raw AMASS at 120 Hz would walk six times too slowly, over
six times the duration. Retiming handles this whenever the source rate is known. If a file
declares no rate the converter assumes it is already at the target and prints a warning; if that
assumption is wrong, put the rate in the file. Data processed through HumanML3D is already at
20 Hz, so the retiming is a no-op there.

| Option | Default | |
|---|---|---|
| `--rig` | `male` | CARLA rest pose to target. The released motions use `male`. |
| `--rotation` | `euler` | Joint rotation map, see below. |
| `--fps` | `20` | Target animation rate. |

### The rotation map

`--rotation euler` reads each axis-angle triple as three sequential XYZ rotations. This is what
produced the released motions, and is the default so new motions stay consistent with them.

`--rotation expmap` applies Eq. 3 of the paper literally, treating the triple as a rotation vector
via the exponential map — which is what SMPL's format means.

The two agree to first order and separate as angles grow. On pedestrian motion the difference is
around a degree per joint, largest at the shoulders. Neither reproduces the SMPL body measurably
better once retargeted onto CARLA's rig, whose proportions and rest pose differ from SMPL's by
considerably more than that. Change it only if you are converting a fresh set and want the
paper's formulation throughout.

## Registering a motion

Put the `.pkl` in `data/motions/` and add its file ID to one of the CSVs in `data/csvs/`. The
category decides how the benchmark uses it:

- `Crossing.csv`, `Attempting.csv` — triggered when the ego vehicle closes to the activation distance
- `Not_Crossing.csv` — played as ambient idle behaviour

## Files

| | |
|---|---|
| `smpl_to_carla.py` | the converter, usable as a CLI or imported |
| `retargeting_walkthrough.ipynb` | the conversion opened up a step at a time, with the maths from Sec. 3.3 and a 3D preview of the result |
| `dump_carla_rest_pose.py` | regenerate the rig data below from a running CARLA server |
| `data/carla_rest_*.yaml` | CARLA's walker rest pose |
| `data/carla_bone_tree.yaml` | the walker's bone hierarchy |

The rest-pose files were dumped from CARLA 0.9.14's default walkers. Regenerate them with
`dump_carla_rest_pose.py` if you target a different CARLA version or a walker whose rig differs.

## Requirements

NumPy, PyYAML and joblib — all already in the `habit` environment. The notebook additionally uses
matplotlib. Nothing here needs a running CARLA server except `dump_carla_rest_pose.py`.
