#!/usr/bin/env python3
"""Dump a CARLA walker's rest pose to the YAML format smpl_to_carla.py reads.

The files in data/ were produced this way. Regenerate them if you target a
different CARLA version or a walker whose rig differs from the defaults.

Requires a running CARLA server and the CARLA PythonAPI on PYTHONPATH.

Example
-------
    python3 tools/motion/dump_carla_rest_pose.py \\
        --blueprint walker.pedestrian.0001 \\
        -o tools/motion/data/carla_rest_male.yaml
"""

import argparse
import sys

import carla

from smpl_to_carla import CARLA_BONES


def dump(world, blueprint_id):
    """Spawn a walker, read its rest pose, and return it as a plain dict."""
    blueprints = world.get_blueprint_library().filter(blueprint_id)
    if not blueprints:
        raise RuntimeError('no walker blueprint matching {!r}'.format(blueprint_id))

    spawn = world.get_map().get_spawn_points()[0]
    walker = world.try_spawn_actor(blueprints[0], spawn)
    if walker is None:
        raise RuntimeError('could not spawn {} at {}'.format(blueprint_id, spawn.location))

    try:
        world.tick() if world.get_settings().synchronous_mode else world.wait_for_tick()
        bones = {bone.name: bone.relative for bone in walker.get_bones().bone_transforms}
    finally:
        walker.destroy()

    missing = [name for name in CARLA_BONES if name not in bones]
    if missing:
        raise RuntimeError('rig is missing expected bones: {}'.format(', '.join(missing)))

    transforms = {}
    for name in CARLA_BONES:
        transform = bones[name]
        transforms[name] = {
            'location': {'x': transform.location.x,
                         'y': transform.location.y,
                         'z': transform.location.z},
            'rotation': {'pitch': transform.rotation.pitch,
                         'yaw': transform.rotation.yaw,
                         'roll': transform.rotation.roll},
        }
    return transforms


def write_yaml(transforms, path):
    """Write the rest pose, keeping bone order and fixed-point formatting."""
    with open(path, 'w') as handle:
        handle.write('transforms:\n')
        for name in CARLA_BONES:
            entry = transforms[name]
            handle.write('  {}:\n'.format(name))
            handle.write('    location:\n')
            for axis in ('x', 'y', 'z'):
                handle.write('      {}: {:.6f}\n'.format(axis, entry['location'][axis]))
            handle.write('    rotation:\n')
            for angle in ('pitch', 'yaw', 'roll'):
                handle.write('      {}: {:.6f}\n'.format(angle, entry['rotation'][angle]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('-o', '--output', required=True, help='destination .yaml')
    parser.add_argument('--blueprint', default='walker.pedestrian.0001',
                        help='walker blueprint to read (default: %(default)s)')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=2000)
    parser.add_argument('--timeout', type=float, default=20.0)
    args = parser.parse_args(argv)

    client = carla.Client(args.host, args.port)
    client.set_timeout(args.timeout)
    world = client.get_world()

    transforms = dump(world, args.blueprint)
    write_yaml(transforms, args.output)
    print('wrote {} ({} bones from {})'.format(args.output, len(transforms), args.blueprint))
    return 0


if __name__ == '__main__':
    sys.exit(main())
