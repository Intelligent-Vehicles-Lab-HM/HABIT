import math
import random
import time
import carla
import numpy as np
from srunner.scenariomanager.actorcontrols.basic_control import BasicControl


class PedestrianAnimationControl(BasicControl):
    """
    Full animation-based controller for pedestrians with motion alignment,
    cycle-aware blending, and reactive transitions based on nearby actors.
    """

    def __init__(self, actor, required_joints, motion_library, idle_library, initial_facing, spawn_point):
        if not isinstance(actor, carla.Walker):
            raise RuntimeError("PedestrianAnimationControl: actor must be a pedestrian")

        super(PedestrianAnimationControl, self).__init__(actor)
        self._required_joints = required_joints
        self._motions = motion_library
        self._idles = idle_library
        self._spawn_point = spawn_point
        self._initial_facing = initial_facing
        self._facing_rad = math.radians(initial_facing - 90)

        self._animation_offset = carla.Location()
        self._last_idle_spawn_point = spawn_point.location
        self._cycle_mode = "idle"  # or "motion", or "walker"
        self._frame_idx = 0
        self._current_cycle = 0
        self._max_cycles = 3
        self._blend_frames = 5
        self._start_time = time.time()
        self._bone_struct = self._actor.get_bones()
        self._collision_threshold = 4.5

        self._nearby_vehicles = []
        self._nearby_walkers = []

        self._walking_direction = carla.Vector3D(1, 0, 0)

        self._select_random_idle()
        self._select_random_motion()

    def reset(self):
        self._frame_idx = 0
        self._current_cycle = 0
        self._cycle_mode = "idle"
        self._actor.blend_pose(1.0)

    def set_nearby_actors(self, vehicles=None, walkers=None):
        self._nearby_vehicles = vehicles if vehicles else []
        self._nearby_walkers = [w for w in walkers if w.id != self._actor.id] if walkers else []

    def run_step(self):
        if not self._actor or not self._actor.is_alive:
            return

        now = time.time()
        if now - self._start_time < 0.05:
            return  # maintain ~20 FPS
        self._start_time = now

        if self._cycle_mode == "idle":
            if self._will_collide(self._actor.get_location()):
                self._cycle_mode = "motion"
                self._frame_idx = 0
                return
            self._run_idle_frame()
        elif self._cycle_mode == "motion":
            self._run_motion_frame()
        elif self._cycle_mode == "walker":
            self._run_walker_control_step()

    def _select_random_idle(self):
        self._idle_pose_data, self._idle_transl = random.choice(self._idles)

    def _select_random_motion(self):
        self._motion_pose_data, self._motion_transl = random.choice(self._motions)

    def _run_idle_frame(self):
        pose_data = self._idle_pose_data
        transl = self._idle_transl
        frame_idx = self._frame_idx % len(pose_data)

        # Offset realignment at beginning of cycle
        if self._frame_idx == 0 and self._current_cycle > 0:
            current_pos = self._actor.get_transform().location
            first = self._transform_translation(transl[0])
            self._animation_offset = current_pos - first

        location = self._transform_translation(transl[frame_idx]) + self._animation_offset + self._spawn_point.location
        rotation = self._compute_root_rotation(pose_data[frame_idx])

        self._actor.set_transform(carla.Transform(location, rotation))
        self._apply_bone_pose(self._bone_struct, pose_data[frame_idx])
        self._actor.blend_pose(1.0)

        self._frame_idx += 1
        if self._frame_idx >= len(pose_data):
            self._frame_idx = 0
            self._current_cycle += 1
            self._last_idle_spawn_point = location
            if self._current_cycle >= self._max_cycles:
                self._current_cycle = 0
                self._cycle_mode = "motion"
                self._select_random_motion()

    def _run_motion_frame(self):
        pose_data = self._motion_pose_data
        transl = self._motion_transl
        frame_idx = self._frame_idx % len(pose_data)

        if self._frame_idx == 0 and self._current_cycle > 0:
            current_pos = self._actor.get_transform().location
            first = self._transform_translation(transl[0])
            self._animation_offset = current_pos - first

        location = self._transform_translation(transl[frame_idx]) + self._animation_offset + self._last_idle_spawn_point
        if self._will_collide(location):
            return  # skip frame if collision likely

        rotation = self._compute_root_rotation(pose_data[frame_idx])
        self._actor.set_transform(carla.Transform(location, rotation))
        self._apply_bone_pose(self._bone_struct, pose_data[frame_idx])

        blend_factor = min(1.0, frame_idx / max(1, self._blend_frames))
        self._actor.blend_pose(1.0 - blend_factor)

        self._frame_idx += 1
        if self._frame_idx >= len(pose_data):
            self._frame_idx = 0
            self._current_cycle += 1
            self._last_idle_spawn_point = location
            if self._current_cycle >= self._max_cycles:
                self._cycle_mode = "walker"
                self._frame_idx = 0
                self._walking_direction = rotation.get_forward_vector()
                return
            self._select_random_motion()

    def _run_walker_control_step(self):
        control = carla.WalkerControl()
        control.direction = self._walking_direction
        control.speed = 1.0
        control.jump = False
        self._actor.apply_control(control)

        # stop after some time or distance
        if random.random() < 0.01:  # small chance per tick to reset
            self._cycle_mode = "idle"
            self._select_random_idle()
            self._frame_idx = 0
            self._current_cycle = 0
            self._actor.blend_pose(1.0)

    def _will_collide(self, next_location):
        actors = self._nearby_vehicles + self._nearby_walkers
        for actor in actors:
            if not actor.is_alive:
                continue
            if actor.get_transform().location.distance(next_location) < self._collision_threshold:
                return True
        return False

    def _transform_translation(self, transl_frame):
        x_in, y_in, z_in = float(transl_frame[0]), float(transl_frame[2]), float(transl_frame[1])
        x_out = x_in * math.cos(self._facing_rad) - y_in * math.sin(self._facing_rad)
        y_out = x_in * math.sin(self._facing_rad) + y_in * math.cos(self._facing_rad)
        return carla.Location(x_out, y_out, z_in)

    def _compute_root_rotation(self, frame_pose):
        root_rotation = frame_pose[self._required_joints.index('crl_root')]
        yaw = (float(root_rotation[0]) + self._initial_facing + 180) % 360 - 180
        return carla.Rotation(pitch=float(root_rotation[1]), yaw=yaw, roll=float(root_rotation[2]))

    def _apply_bone_pose(self, bone_structure, frame_pose):
        bone_transforms = []
        for bone in bone_structure.bone_transforms:
            if bone.name in self._required_joints:
                idx = self._required_joints.index(bone.name)
                rotation = frame_pose[idx]
                transform = carla.Transform(
                    location=bone.relative.location,
                    rotation=carla.Rotation(pitch=rotation[1], yaw=rotation[2], roll=rotation[0])
                )
                bone_transforms.append((bone.name, transform))
        control = carla.WalkerBoneControlIn()
        control.bone_transforms = bone_transforms
        self._actor.set_bones(control)
