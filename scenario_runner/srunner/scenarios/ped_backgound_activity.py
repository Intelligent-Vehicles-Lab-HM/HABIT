import carla
import math
import random
import numpy as np
import py_trees
import os
import joblib
import pickle
import time

from agents.tools.misc import get_speed
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import AtomicBehavior
from leaderboard.envs.sensor_interface import GameTime

REQUIRED_JOINTS = [
    'crl_root', 'crl_hips__C', 'crl_spine__C', 'crl_spine01__C',
    'crl_shoulder__L', 'crl_arm__L', 'crl_foreArm__L', 'crl_hand__L',
    'crl_neck__C', 'crl_Head__C', 'crl_eye__L', 'crl_eye__R',
    'crl_shoulder__R', 'crl_arm__R', 'crl_foreArm__R', 'crl_hand__R',
    'crl_thigh__R', 'crl_leg__R', 'crl_foot__R', 'crl_toe__R', 'crl_toeEnd__R',
    'crl_thigh__L', 'crl_leg__L', 'crl_foot__L', 'crl_toe__L', 'crl_toeEnd__L'
]

EXCLUDED_BLUEPRINTS = ['walker.pedestrian.0050', 'walker.pedestrian.0051']

class PedBackgroundBehavior(AtomicBehavior):
    def __init__(self, ego_vehicle, world, route, animation_folder, spawn_file, crossing, not_crossing, attempting, name="PedBackgroundBehavior"):
        super(PedBackgroundBehavior, self).__init__(name)
        self.vehicles = None
        self.ego = ego_vehicle
        self.world = world
        self.route = route
        self.animation_folder = animation_folder
        self.spawn_file = spawn_file
        self.crossing = crossing
        self.not_crossing = not_crossing
        self.attempting = attempting

        self._pedestrians = []
        self._animations = []
        self._frame_counters = {}
        self._state = {}
        self._animation_interval = 0.05
        self._last_tick_time = None
        self.num_idle_real_peds = 20  # default: 25 before
        self.num_idle_only_peds = 20  # default: 25


    # def initialise(self):
    #     self._last_tick_time = GameTime.get_time()
    #     spawn_points = self._load_spawn_points()
    #     nearby_spawns = self._filter_spawns_near_route(spawn_points, max_distance=30.0)
    #     animations = self._load_animation_files()

    #     all_blueprints = self.world.get_blueprint_library().filter('walker.pedestrian.*')
    #     blueprints = [bp for bp in all_blueprints if bp.id not in EXCLUDED_BLUEPRINTS]

    #     idx = 0
    #     for spawn_point in random.sample(nearby_spawns, min(len(nearby_spawns), 25)):
    #         walker_bp = random.choice(blueprints)
    #         walker = self.world.try_spawn_actor(walker_bp, spawn_point)
    #         if not walker:
    #             continue

    #         motion_path = random.choice(animations['motions'])
    #         idle_path = random.choice(animations['idles'])
    #         pose_data, transl = self._load_animation(motion_path)
    #         idle_pose_data, idle_transl = self._load_animation(idle_path)

    #         self._pedestrians.append(walker)
    #         self._animations.append(type('Anim', (object,), {
    #             'walker': walker,
    #             'pose_data': pose_data,
    #             'transl': transl,
    #             'idle_pose_data': idle_pose_data,
    #             'idle_transl': idle_transl,
    #             'required_joints': REQUIRED_JOINTS,
    #             'initial_facing': spawn_point.rotation.yaw,
    #             'fixed_spawn_point': spawn_point,
    #             'offset': carla.Location(),
    #             'last_world_loc': spawn_point.location,
    #             'motion_cycle': 0
    #         })())
    #         self._frame_counters[idx] = 0
    #         self._state[idx] = "idle"
    #         idx += 1
    def initialise(self):
        self._last_tick_time = GameTime.get_time()
        spawn_points = self._load_spawn_points()
        nearby_spawns = self._filter_spawns_near_route(spawn_points, max_distance=30.0)
        animations = self._load_animation_files()

        all_blueprints = self.world.get_blueprint_library().filter('walker.pedestrian.*')
        blueprints = [bp for bp in all_blueprints if bp.id not in EXCLUDED_BLUEPRINTS]

        idx = 0
        used_spawn_points = []

        for spawn_point in random.sample(nearby_spawns, min(len(nearby_spawns), self.num_idle_real_peds)):
            walker_bp = random.choice(blueprints)
            walker = self.world.try_spawn_actor(walker_bp, spawn_point)
            if not walker:
                continue

            motion_path = random.choice(animations['motions'])
            idle_path = random.choice(animations['idles'])
            pose_data, transl = self._load_animation(motion_path)
            idle_pose_data, idle_transl = self._load_animation(idle_path)

            self._pedestrians.append(walker)
            self._animations.append(type('Anim', (object,), {
                'walker': walker,
                'pose_data': pose_data,
                'transl': transl,
                'idle_pose_data': idle_pose_data,
                'idle_transl': idle_transl,
                'required_joints': REQUIRED_JOINTS,
                'initial_facing': spawn_point.rotation.yaw,
                'fixed_spawn_point': spawn_point,
                'offset': carla.Location(),
                'last_world_loc': spawn_point.location,
                'motion_cycle': 0
            })())
            self._frame_counters[idx] = 0
            self._state[idx] = "idle"
            used_spawn_points.append(spawn_point)
            idx += 1

        # --- Add ambient idle-only pedestrians ---
        extra_idle_spawns = [sp for sp in spawn_points if sp not in used_spawn_points]
        random.shuffle(extra_idle_spawns)
        extra_idle_spawns = extra_idle_spawns[:self.num_idle_only_peds]

        existing_idle_ids = set(os.path.splitext(os.path.basename(anim_path))[0] for anim_path in animations['idles'])
        used_idle_paths = set()
        idle_file_ids = set(self.not_crossing['File ID'].values)

        extra_idle_paths = [
            os.path.join(self.animation_folder, f)
            for f in os.listdir(self.animation_folder)
            if f.endswith('.pkl') and os.path.splitext(f)[0] in idle_file_ids and f not in used_idle_paths
        ]

        for spawn_point in extra_idle_spawns:
            walker_bp = random.choice(blueprints)
            walker = self.world.try_spawn_actor(walker_bp, spawn_point)
            if not walker:
                continue

            idle_path = random.choice(extra_idle_paths) if extra_idle_paths else random.choice(animations['idles'])
            idle_pose_data, idle_transl = self._load_animation(idle_path)

            self._pedestrians.append(walker)
            self._animations.append(type('Anim', (object,), {
                'walker': walker,
                'pose_data': idle_pose_data,
                'transl': idle_transl,
                'idle_pose_data': idle_pose_data,
                'idle_transl': idle_transl,
                'required_joints': REQUIRED_JOINTS,
                'initial_facing': spawn_point.rotation.yaw,
                'fixed_spawn_point': spawn_point,
                'offset': carla.Location(),
                'last_world_loc': spawn_point.location,
                'motion_cycle': 0
            })())
            self._frame_counters[idx] = 0
            self._state[idx] = "idle-only"
            used_spawn_points.append(spawn_point)
            used_idle_paths.add(os.path.basename(idle_path))
            idx += 1


    def update(self):
        self.vehicles = self.world.get_actors().filter('vehicle.*')
        current_time = GameTime.get_time()
        if current_time - self._last_tick_time < self._animation_interval:
            return py_trees.common.Status.RUNNING
        self._last_tick_time = current_time

        for idx, anim in enumerate(self._animations):
            pedestrian = anim.walker
            distance = pedestrian.get_transform().location.distance(self.ego.get_transform().location)

            # if self._state.get(idx, "idle") == "idle" and distance < 30:
            #     self._state[idx] = "real"
            #     frame_index = self._frame_counters.get(idx, 0)
            #     theta_rad = math.radians(anim.initial_facing - 90)
            #     base_location = carla.Location(
            #         x=float(anim.transl[0][0]) * math.cos(theta_rad) - float(anim.transl[0][2]) * math.sin(theta_rad),
            #         y=float(anim.transl[0][0]) * math.sin(theta_rad) + float(anim.transl[0][2]) * math.cos(theta_rad),
            #         z=0
            #     ) + anim.fixed_spawn_point.location + anim.offset
            #     current_location = pedestrian.get_transform().location
            #     anim.offset = current_location - base_location
            #     anim.last_world_loc = current_location
            #     self._frame_counters[idx] = 0
            #     anim.motion_cycle += 1
            if self._state.get(idx) == "idle-only":
                # Ambient idle peds never switch to real
                pass
            elif self._state.get(idx) == "idle" and distance < 30:
                self._state[idx] = "real"
                frame_index = self._frame_counters.get(idx, 0)
                theta_rad = math.radians(anim.initial_facing - 90)
                base_location = carla.Location(
                    x=float(anim.transl[0][0]) * math.cos(theta_rad) - float(anim.transl[0][2]) * math.sin(theta_rad),
                    y=float(anim.transl[0][0]) * math.sin(theta_rad) + float(anim.transl[0][2]) * math.cos(theta_rad),
                    z=0
                ) + anim.fixed_spawn_point.location + anim.offset
                current_location = pedestrian.get_transform().location
                anim.offset = current_location - base_location
                anim.last_world_loc = current_location
                self._frame_counters[idx] = 0
                anim.motion_cycle += 1

            frame_index = self._frame_counters.get(idx, 0)
            state = self._state.get(idx, "idle")
            # pose_data = anim.idle_pose_data if state == "idle" else anim.pose_data
            # transl = anim.idle_transl if state == "idle" else anim.transl
            pose_data = anim.idle_pose_data if state in ["idle", "idle-only"] else anim.pose_data
            transl = anim.idle_transl if state in ["idle", "idle-only"] else anim.transl


            if frame_index == 0 and state == "real" and anim.motion_cycle > 0:
                theta_rad = math.radians(anim.initial_facing - 90)
                first_frame_pos = carla.Location(
                    x=float(transl[0][0]) * math.cos(theta_rad) - float(transl[0][2]) * math.sin(theta_rad),
                    y=float(transl[0][0]) * math.sin(theta_rad) + float(transl[0][2]) * math.cos(theta_rad),
                    z=float(transl[0][1])
                ) + anim.fixed_spawn_point.location
                current_pos = pedestrian.get_transform().location
                anim.offset = current_pos - first_frame_pos

            self._apply_animation_frame(pose_data, transl, anim, frame_index)
            total_frames = pose_data.shape[0]
            self._frame_counters[idx] = (frame_index + 1) % total_frames

        return py_trees.common.Status.RUNNING

    def terminate(self, new_status):
        for anim in self._animations:
            anim.walker.blend_pose(0)

    def _apply_animation_frame(self, pose_data, transl, anim_obj, frame_index):
        walker = anim_obj.walker
        theta_deg = anim_obj.initial_facing - 90
        theta_rad = math.radians(theta_deg)
        age_value = walker.attributes.get('age', 'adult')
        hips_height = 1.04862213 if age_value == 'adult' else 0.613

        x_translation = float(transl[frame_index][0])
        y_translation = float(transl[frame_index][1] + hips_height)
        z_translation = float(transl[frame_index][2])

        new_location = carla.Location(
            x=x_translation * math.cos(theta_rad) - z_translation * math.sin(theta_rad),
            y=x_translation * math.sin(theta_rad) + z_translation * math.cos(theta_rad),
            z=0
        ) + anim_obj.fixed_spawn_point.location + anim_obj.offset
        collision, _, _ = self.will_next_step_collide_with_any_vehicle(new_location)
        if collision:
            return
        anim_obj.last_world_loc = new_location

        rot = None
        for bone in walker.get_bones().bone_transforms:
            if bone.name == 'crl_root':
                rotation = pose_data[frame_index][anim_obj.required_joints.index('crl_root')]
                rot = carla.Rotation(
                    pitch=float(rotation[1]),
                    yaw=(float(rotation[0]) + theta_deg + 180) % 360 - 180,
                    roll=float(rotation[2])
                )
                break

        walker.set_transform(carla.Transform(new_location, rot))

        ue_carla_pose = []
        for bone in walker.get_bones().bone_transforms:
            if bone.name in anim_obj.required_joints:
                rotation = pose_data[frame_index][anim_obj.required_joints.index(bone.name)]
                if bone.name == 'crl_hips__C':
                    location = carla.Location(x=0, y=-y_translation, z=0)
                else:
                    location = bone.relative.location
                ue_carla_pose.append((
                    bone.name,
                    carla.Transform(
                        rotation=carla.Rotation(
                            pitch=rotation[1],
                            yaw=rotation[2],
                            roll=rotation[0]
                        ),
                        location=location
                    )
                ))

        control = carla.WalkerBoneControlIn()
        control.bone_transforms = ue_carla_pose
        walker.set_bones(control)
        walker.blend_pose(1)

    def _load_animation(self, file_path):
        with open(file_path, 'rb') as f:
            data = joblib.load(f)
        return data['pose_data'], data['transl'].squeeze()

    def _load_animation_files(self):
        all_files = [f for f in os.listdir(self.animation_folder) if f.endswith('.pkl')]
        file_ids = {os.path.splitext(f)[0]: f for f in all_files}

        crossing_ids = set(self.crossing['File ID'].values)
        not_crossing_ids = set(self.not_crossing['File ID'].values)
        attempting_ids = set(self.attempting['File ID'].values)

        motions = [
            os.path.join(self.animation_folder, file_ids[fid])
            for fid in (crossing_ids | attempting_ids)
            if fid in file_ids
        ]
        idles = [
            os.path.join(self.animation_folder, file_ids[fid])
            for fid in not_crossing_ids
            if fid in file_ids
        ]

        return {'motions': motions, 'idles': idles}

    def _load_spawn_points(self):
        with open(self.spawn_file, 'rb') as f:
            raw = pickle.load(f)
        spawn_points = []
        for data in raw:
            location = carla.Location(**data['location'])
            rotation = carla.Rotation(**data['rotation'])
            spawn_points.append(carla.Transform(location=location, rotation=rotation))
        return spawn_points

    def _filter_spawns_near_route(self, spawns, max_distance):
        near = []
        for sp in spawns:
            for wp in self.route:
                transform, _ = wp
                if sp.location.distance(transform.location) < max_distance:
                    near.append(sp)
                    break
        return near

    def will_next_step_collide_with_any_vehicle(self, next_location, collision_threshold=3):
        """
        Checks if the next animation step will collide with ego or any other vehicle.
        """
        min_distance = float('inf')
        closest_vehicle = None

        for vehicle in self.vehicles:
            vehicle_location = vehicle.get_transform().location
            distance = next_location.distance(vehicle_location)
            if distance < min_distance:
                min_distance = distance
                closest_vehicle = vehicle

        return min_distance < collision_threshold, min_distance, closest_vehicle