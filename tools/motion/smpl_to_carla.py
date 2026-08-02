#!/usr/bin/env python3
"""Retarget SMPL motion sequences onto CARLA's pedestrian skeleton.

Reads SMPL body poses (axis-angle) and root translation, and writes the .pkl
format the HABIT pedestrian behaviour loads at runtime:

    {'pose_data': (T, 26, 3) float64 Euler degrees,
     'transl':    (1, T, 3)  float32 metres}

The retargeting follows Sec. 3.3 of the HABIT paper. Depends only on NumPy,
PyYAML and joblib.

Examples
--------
Convert a single file:

    python3 tools/motion/smpl_to_carla.py motion.npz -o data/motions/000001.pkl

Convert a directory, writing one .pkl per input:

    python3 tools/motion/smpl_to_carla.py amass/CMU/07/ -o data/motions/
"""

import argparse
import os
import sys

import joblib
import numpy as np
import yaml

# Bone order expected by the runtime. pose_data[t, i] holds the Euler angles of
# CARLA_BONES[i], as (roll, pitch, yaw) in degrees.
CARLA_BONES = [
    'crl_root', 'crl_hips__C', 'crl_spine__C', 'crl_spine01__C',
    'crl_shoulder__L', 'crl_arm__L', 'crl_foreArm__L', 'crl_hand__L',
    'crl_neck__C', 'crl_Head__C', 'crl_eye__L', 'crl_eye__R',
    'crl_shoulder__R', 'crl_arm__R', 'crl_foreArm__R', 'crl_hand__R',
    'crl_thigh__R', 'crl_leg__R', 'crl_foot__R', 'crl_toe__R', 'crl_toeEnd__R',
    'crl_thigh__L', 'crl_leg__L', 'crl_foot__L', 'crl_toe__L', 'crl_toeEnd__L',
]
N_BONES = len(CARLA_BONES)

# SMPL's first 22 joints, in pose-vector order.
SMPL_JOINTS = [
    'Pelvis', 'L_Hip', 'R_Hip', 'Spine1', 'L_Knee', 'R_Knee', 'Spine2',
    'L_Ankle', 'R_Ankle', 'Spine3', 'L_Foot', 'R_Foot', 'Neck', 'L_Collar',
    'R_Collar', 'Head', 'L_Shoulder', 'R_Shoulder', 'L_Elbow', 'R_Elbow',
    'L_Wrist', 'R_Wrist',
]

# CARLA bone <- SMPL joint. The five bones absent here (crl_root, both eyes and
# both toe ends) have no SMPL counterpart and keep their rest rotation.
JOINT_MAP = [
    ('crl_hips__C', 'Pelvis'),
    ('crl_spine__C', 'Spine1'),
    ('crl_spine01__C', 'Spine3'),
    ('crl_shoulder__L', 'L_Collar'), ('crl_shoulder__R', 'R_Collar'),
    ('crl_arm__L', 'L_Shoulder'), ('crl_arm__R', 'R_Shoulder'),
    ('crl_foreArm__L', 'L_Elbow'), ('crl_foreArm__R', 'R_Elbow'),
    ('crl_hand__L', 'L_Wrist'), ('crl_hand__R', 'R_Wrist'),
    ('crl_neck__C', 'Neck'),
    ('crl_Head__C', 'Head'),
    ('crl_thigh__L', 'L_Hip'), ('crl_thigh__R', 'R_Hip'),
    ('crl_leg__L', 'L_Knee'), ('crl_leg__R', 'R_Knee'),
    ('crl_foot__L', 'L_Ankle'), ('crl_foot__R', 'R_Ankle'),
    ('crl_toe__L', 'L_Foot'), ('crl_toe__R', 'R_Foot'),
]
BONE_INDEX = [CARLA_BONES.index(b) for b, _ in JOINT_MAP]
JOINT_INDEX = [SMPL_JOINTS.index(j) for _, j in JOINT_MAP]

# SMPL is Y-up right-handed, CARLA is Z-up left-handed.
BASIS = np.array([[1.0, 0.0, 0.0],
                  [0.0, 0.0, -1.0],
                  [0.0, 1.0, 0.0]])

# Chirality flip, applied to the rotation vector so every matrix downstream
# stays a proper rotation.
MIRROR = np.array([-1.0, 1.0, 1.0])

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# Keys accepted when reading an input file, in order of preference.
POSE_KEYS = ('pose_body', 'pose_world', 'poses', 'pose')
TRANS_KEYS = ('trans_world', 'transl', 'trans', 'translation')
FPS_KEYS = ('fps', 'mocap_framerate', 'mocap_frame_rate', 'frame_rate')


# --------------------------------------------------------------------------- #
# Rotations
# --------------------------------------------------------------------------- #

def axis_angle_to_matrix(w):
    """Exponential map (Rodrigues). w: (..., 3) -> (..., 3, 3)."""
    theta = np.linalg.norm(w, axis=-1, keepdims=True)
    k = w / np.where(theta < 1e-12, 1.0, theta)
    kx, ky, kz = k[..., 0], k[..., 1], k[..., 2]
    zero = np.zeros_like(kx)
    K = np.stack([zero, -kz, ky,
                  kz, zero, -kx,
                  -ky, kx, zero], axis=-1).reshape(*kx.shape, 3, 3)
    theta = theta[..., None]
    identity = np.broadcast_to(np.eye(3), K.shape)
    return identity + np.sin(theta) * K + (1.0 - np.cos(theta)) * (K @ K)


def euler_xyz_to_matrix(e):
    """R = Rx(a) Ry(b) Rz(c). e: (..., 3) radians -> (..., 3, 3)."""
    a, b, c = e[..., 0], e[..., 1], e[..., 2]
    ca, sa = np.cos(a), np.sin(a)
    cb, sb = np.cos(b), np.sin(b)
    cc, sc = np.cos(c), np.sin(c)
    zero, one = np.zeros_like(a), np.ones_like(a)
    rx = np.stack([one, zero, zero, zero, ca, -sa, zero, sa, ca], -1)
    ry = np.stack([cb, zero, sb, zero, one, zero, -sb, zero, cb], -1)
    rz = np.stack([cc, -sc, zero, sc, cc, zero, zero, zero, one], -1)
    shape = (*a.shape, 3, 3)
    return rx.reshape(shape) @ ry.reshape(shape) @ rz.reshape(shape)


def matrix_to_euler_xyz(R):
    """Inverse of euler_xyz_to_matrix. Returns (..., 3) radians."""
    beta = np.arcsin(np.clip(R[..., 0, 2], -1.0, 1.0))
    alpha = np.arctan2(-R[..., 1, 2], R[..., 2, 2])
    gamma = np.arctan2(-R[..., 0, 1], R[..., 0, 0])
    return np.stack([alpha, beta, gamma], -1)


# --------------------------------------------------------------------------- #
# CARLA reference skeleton
# --------------------------------------------------------------------------- #

def load_rest_pose(rig='male', data_dir=DATA_DIR):
    """Load CARLA's rest pose.

    Returns per-bone local offsets in metres, local rotation matrices, and the
    bone hierarchy. Use dump_carla_rest_pose.py to regenerate these files for a
    different CARLA version or walker blueprint.
    """
    rest_file = os.path.join(data_dir, 'carla_rest_{}.yaml'.format(rig))
    tree_file = os.path.join(data_dir, 'carla_bone_tree.yaml')
    if not os.path.exists(rest_file):
        raise FileNotFoundError('no rest pose for rig {!r} at {}'.format(rig, rest_file))

    with open(rest_file) as handle:
        transforms = yaml.safe_load(handle)['transforms']
    with open(tree_file) as handle:
        tree = yaml.safe_load(handle)['structure']

    locations, rotations = [], []
    for bone in CARLA_BONES:
        entry = transforms[bone]
        loc, rot = entry['location'], entry['rotation']
        # centimetres to metres, and into the right-handed frame used here
        locations.append((loc['x'] / 100.0, loc['y'] / 100.0, -loc['z'] / 100.0))
        rotations.append((np.deg2rad(-rot['roll']),
                          np.deg2rad(-rot['pitch']),
                          np.deg2rad(-rot['yaw'])))

    locations = np.array(locations)
    locations[CARLA_BONES.index('crl_hips__C')] = 0.0
    return locations, euler_xyz_to_matrix(np.array(rotations)), tree


def forward_kinematics(local_loc, local_rot, tree):
    """Compose local bone transforms into absolute ones.

    Follows Unreal's row-vector convention: transforms act on row vectors from
    the right, so a bone composes as `child @ parent` and the homogeneous
    matrix carries its translation in the last row.
    """
    frames = local_loc.shape[0]
    abs_loc = np.zeros_like(local_loc)
    abs_rot = np.zeros_like(local_rot)

    def walk(node, parent):
        name, children = list(node.items())[0]
        i = CARLA_BONES.index(name)
        homogeneous = np.concatenate([local_loc[:, i], np.ones((frames, 1))], axis=-1)
        abs_loc[:, i] = np.einsum('tj,tjk->tk', homogeneous, parent)[:, :3]
        abs_rot[:, i] = local_rot[:, i] @ parent[:, :3, :3]

        child_frame = np.tile(np.eye(4), (frames, 1, 1))
        child_frame[:, :3, :3] = abs_rot[:, i]
        child_frame[:, 3, :3] = abs_loc[:, i]
        for child in (children or []):
            walk(child, child_frame)

    walk(tree[0], np.tile(np.eye(4), (frames, 1, 1)))
    return abs_loc, abs_rot


# --------------------------------------------------------------------------- #
# Retargeting
# --------------------------------------------------------------------------- #

def retarget(omega, rig='male', rotation='euler', data_dir=DATA_DIR):
    """Convert SMPL axis-angle poses to CARLA bone Euler angles.

    omega    : (T, 22, 3) SMPL axis-angle, radians
    rig      : which CARLA rest pose to target ('male' or 'female')
    rotation : 'euler' reproduces the released HABIT motions bit for bit;
               'expmap' applies Eq. 3 of the paper literally. The two differ by
               about a degree on pedestrian motion.

    Returns (T, 26, 3) Euler angles in degrees.
    """
    if omega.ndim != 3 or omega.shape[1:] != (22, 3):
        raise ValueError('expected (T, 22, 3) axis-angle, got {}'.format(omega.shape))
    if rotation not in ('euler', 'expmap'):
        raise ValueError("rotation must be 'euler' or 'expmap'")

    frames = omega.shape[0]
    rest_loc, rest_rot, tree = load_rest_pose(rig, data_dir)

    # rest orientation of every bone, expressed in SMPL's basis
    _, rest_abs_rot = forward_kinematics(rest_loc[None], rest_rot[None], tree)
    reference = rest_abs_rot[0] @ BASIS

    mirrored = omega * MIRROR
    joint_rot = (euler_xyz_to_matrix(mirrored) if rotation == 'euler'
                 else axis_angle_to_matrix(mirrored))

    changes = np.tile(np.eye(3), (frames, N_BONES, 1, 1))
    changes[:, BONE_INDEX] = joint_rot[:, JOINT_INDEX]

    # CARLA has one fewer spine bone, so two SMPL joints fold into one.
    changes[:, CARLA_BONES.index('crl_spine01__C')] = (
        joint_rot[:, SMPL_JOINTS.index('Spine3')]
        @ joint_rot[:, SMPL_JOINTS.index('Spine2')]
    )

    # centre each rotation on the rig's rest orientation, then compose onto it
    ref = np.broadcast_to(reference, (frames, N_BONES, 3, 3))
    delta = np.linalg.solve(ref, changes) @ ref
    relative = delta @ np.broadcast_to(rest_rot, (frames, N_BONES, 3, 3))

    return -np.rad2deg(matrix_to_euler_xyz(relative))


# --------------------------------------------------------------------------- #
# Input handling
# --------------------------------------------------------------------------- #

def _first_key(archive, candidates):
    for key in candidates:
        if key in archive:
            return key
    return None


def read_smpl(path):
    """Read SMPL poses and translation from a .npz file.

    Accepts the common layouts: AMASS ('poses', 'trans', 'mocap_framerate') and
    the (T, 66) or (T, 72) axis-angle arrays produced by most SMPL pipelines.
    Returns (omega (T, 22, 3), translation (T, 3), source fps or None).
    """
    with np.load(path, allow_pickle=False) as archive:
        pose_key = _first_key(archive, POSE_KEYS)
        if pose_key is None:
            raise KeyError('{}: no pose array (looked for {})'
                           .format(os.path.basename(path), ', '.join(POSE_KEYS)))
        pose = np.asarray(archive[pose_key], dtype=np.float64)

        trans_key = _first_key(archive, TRANS_KEYS)
        trans = (np.asarray(archive[trans_key], dtype=np.float64)
                 if trans_key else np.zeros((len(pose), 3)))

        fps_key = _first_key(archive, FPS_KEYS)
        fps = float(np.asarray(archive[fps_key]).item()) if fps_key else None

    pose = pose.reshape(len(pose), -1)
    if pose.shape[1] < 66:
        raise ValueError('{}: pose has {} values per frame, need at least 66'
                         .format(os.path.basename(path), pose.shape[1]))

    # Keep the root and the 21 body joints; drop hands and any SMPL-H/X extras.
    omega = pose[:, :66].reshape(-1, 22, 3)
    trans = trans.reshape(-1, 3)[:len(omega)]
    return omega, trans, fps


def resample_indices(n_frames, source_fps, target_fps):
    """Frame indices that retime a clip to target_fps.

    Picks nearest source frames rather than interpolating, which avoids
    blending rotations and matches how HumanML3D downsamples.
    """
    if not source_fps or abs(source_fps - target_fps) < 1e-6:
        return np.arange(n_frames)
    duration = n_frames / source_fps
    count = max(2, int(round(duration * target_fps)))
    return np.clip(np.round(np.arange(count) * source_fps / target_fps),
                   0, n_frames - 1).astype(int)


def convert(path, rig='male', rotation='euler', target_fps=20.0, data_dir=DATA_DIR):
    """Convert one SMPL file into the runtime motion dict."""
    omega, trans, source_fps = read_smpl(path)

    if source_fps is None:
        # The runtime consumes one frame every 0.05 s, so a clip that is not at
        # the target rate plays at the wrong speed: feed it 120 Hz mocap and the
        # pedestrian walks six times too slowly. Nothing downstream can detect
        # that, so say something here.
        print('{}: no frame rate found (looked for {}); assuming it is already '
              'at {:g} Hz. Pass the rate in the file if it is not.'
              .format(os.path.basename(path), ', '.join(FPS_KEYS), target_fps),
              file=sys.stderr)

    keep = resample_indices(len(omega), source_fps, target_fps)
    omega, trans = omega[keep], trans[keep]

    pose_data = retarget(omega, rig=rig, rotation=rotation, data_dir=data_dir)

    # Motions are reused at many spawn points, so the trajectory is stored
    # relative to its own first frame. The runtime adds the spawn point,
    # heading and the rig's hip height at playback.
    transl = trans - trans[0]

    return {'pose_data': pose_data.astype(np.float64),
            'transl': transl.astype(np.float32)[None]}


# --------------------------------------------------------------------------- #
# Command line
# --------------------------------------------------------------------------- #

def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Retarget SMPL motions onto CARLA pedestrians.')
    parser.add_argument('input', help='.npz file, or a directory of them')
    parser.add_argument('-o', '--output', required=True,
                        help='output .pkl, or a directory when input is one')
    parser.add_argument('--rig', default='male', choices=['male', 'female'],
                        help='CARLA rest pose to target (default: male, as used '
                             'for the released motions)')
    parser.add_argument('--rotation', default='euler', choices=['euler', 'expmap'],
                        help='joint rotation map (default: euler, which matches '
                             'the released motions)')
    parser.add_argument('--fps', type=float, default=20.0,
                        help='target animation rate (default: 20)')
    parser.add_argument('--data-dir', default=DATA_DIR,
                        help='directory holding the CARLA rest pose files')
    args = parser.parse_args(argv)

    if os.path.isdir(args.input):
        sources = sorted(os.path.join(args.input, name)
                         for name in os.listdir(args.input)
                         if name.endswith('.npz'))
        if not sources:
            parser.error('no .npz files in {}'.format(args.input))
        if os.path.splitext(args.output)[1]:
            parser.error('output must be a directory when input is a directory')
        os.makedirs(args.output, exist_ok=True)
        targets = [os.path.join(args.output,
                                os.path.splitext(os.path.basename(s))[0] + '.pkl')
                   for s in sources]
    else:
        sources = [args.input]
        if os.path.isdir(args.output) or not os.path.splitext(args.output)[1]:
            os.makedirs(args.output, exist_ok=True)
            targets = [os.path.join(
                args.output,
                os.path.splitext(os.path.basename(args.input))[0] + '.pkl')]
        else:
            parent = os.path.dirname(args.output)
            if parent:
                os.makedirs(parent, exist_ok=True)
            targets = [args.output]

    failures = 0
    for source, target in zip(sources, targets):
        try:
            motion = convert(source, rig=args.rig, rotation=args.rotation,
                             target_fps=args.fps, data_dir=args.data_dir)
        except (KeyError, ValueError) as error:
            print('skipped {}: {}'.format(os.path.basename(source), error),
                  file=sys.stderr)
            failures += 1
            continue
        joblib.dump(motion, target)
        print('{} -> {}  ({} frames)'.format(os.path.basename(source),
                                             target, len(motion['pose_data'])))

    converted = len(sources) - failures
    print('\nconverted {}/{} file(s)'.format(converted, len(sources)))
    return 1 if failures and not converted else 0


if __name__ == '__main__':
    sys.exit(main())
