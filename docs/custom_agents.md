# Custom Agents

This guide describes how to implement your own autonomous driving agent for the HABIT benchmark.

## The AutonomousAgent Base Class

All agents must inherit from the `AutonomousAgent` base class, located at `leaderboard/autoagents/autonomous_agent.py`. The evaluator loads your agent dynamically by calling a `get_entry_point()` function defined at module level, which returns the name of your agent class as a string.

## Methods to Implement

### `setup(self, path_to_conf_file)`

Called once before the evaluation begins. Use this to load model weights, initialize data structures, and set the track type.

- `path_to_conf_file` (str): path to an optional configuration file, passed via the `--agent-config` command-line argument.
- Set `self.track` to either `Track.SENSORS` or `Track.MAP` depending on what data your agent requires.

### `sensors(self)`

Called once after `setup()`. Returns a list of dictionaries defining the sensor suite for your agent. Each dictionary specifies a sensor with its type, mounting position, and configuration parameters.

Returns a list of sensor configuration dictionaries (see Sensor Configuration below).

### `run_step(self, input_data, timestamp)`

Called at every simulation tick (20 Hz by default). This is where your agent's decision-making logic lives.

- `input_data` (dict): dictionary mapping sensor IDs to `(frame, data)` tuples. Camera sensors provide numpy arrays, LIDAR provides point clouds, GPS provides `[lat, lon, alt]`, IMU provides `[accelerometer, gyroscope, compass]`, and the speedometer provides a scalar speed value.
- `timestamp` (float): current simulation time in seconds.
- **Returns:** a `carla.VehicleControl` object with `steer`, `throttle`, `brake`, and `hand_brake` fields.

### `destroy(self)`

Called once after all routes are complete. Use this to release resources, close files, or clean up GPU memory.

## Sensor Configuration

Each sensor is defined as a dictionary with the following keys:

| Key | Type | Description |
|-----|------|-------------|
| `type` | str | Sensor type (see available types below) |
| `id` | str | Unique identifier for this sensor |
| `x` | float | Mounting position: forward offset in meters |
| `y` | float | Mounting position: lateral offset in meters |
| `z` | float | Mounting position: vertical offset in meters |
| `roll` | float | Roll rotation in degrees |
| `pitch` | float | Pitch rotation in degrees |
| `yaw` | float | Yaw rotation in degrees |

Camera sensors additionally accept `width`, `height`, and `fov`. Radar sensors accept `horizontal_fov` and `vertical_fov`.

## Track Types

The track determines which sensors your agent is allowed to use:

**`Track.SENSORS`** -- the standard track. Allowed sensors:
- `sensor.camera.rgb` -- RGB camera
- `sensor.lidar.ray_cast` -- 3D LIDAR
- `sensor.other.radar` -- Radar
- `sensor.other.gnss` -- GPS (latitude, longitude, altitude)
- `sensor.other.imu` -- IMU (accelerometer, gyroscope, compass)
- `sensor.speedometer` -- Ego vehicle speed

**`Track.MAP`** -- extends the SENSORS track with:
- `sensor.opendrive_map` -- provides the full OpenDRIVE map of the current town

## Example: Minimal Agent

Below is a minimal agent that drives forward at constant throttle. It demonstrates the required structure:

```python
import carla
from leaderboard.autoagents.autonomous_agent import AutonomousAgent, Track

def get_entry_point():
    return 'MyAgent'

class MyAgent(AutonomousAgent):

    def setup(self, path_to_conf_file):
        self.track = Track.SENSORS

    def sensors(self):
        return [
            {
                'type': 'sensor.camera.rgb',
                'x': 1.3, 'y': 0.0, 'z': 2.3,
                'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
                'width': 800, 'height': 600, 'fov': 100,
                'id': 'front_camera'
            },
            {
                'type': 'sensor.other.gnss',
                'x': 0.0, 'y': 0.0, 'z': 0.0,
                'id': 'gps'
            },
            {
                'type': 'sensor.speedometer',
                'reading_frequency': 20,
                'id': 'speed'
            },
        ]

    def run_step(self, input_data, timestamp):
        control = carla.VehicleControl()
        control.steer = 0.0
        control.throttle = 0.3
        control.brake = 0.0
        control.hand_brake = False
        return control

    def destroy(self):
        pass
```

## Running Your Agent

Save your agent to a Python file (e.g., `my_agent.py`) and run:

```bash
bash scripts/run_evaluation.sh path/to/my_agent.py
```

If your agent requires a configuration file (for model weights, hyperparameters, etc.), pass it with the `--agent-config` flag:

```bash
bash scripts/run_evaluation.sh path/to/my_agent.py --agent-config path/to/config.yaml
```

## Accessing the Route Plan

The evaluator calls `set_global_plan()` on your agent before `run_step()` begins. This populates two attributes:

- `self._global_plan` -- list of GPS waypoints `(lat, lon, alt)` with associated road options (e.g., `RoadOption.LEFT`, `RoadOption.STRAIGHT`)
- `self._global_plan_world_coord` -- list of `(carla.Transform, RoadOption)` tuples in world coordinates

These are downsampled versions of the full route. Use them for high-level navigation planning.

## Tips

- The simulation runs at 20 Hz. Your `run_step()` must return within the timeout period (default: 300 seconds total per route).
- Use the `DummyAgent` at `leaderboard/autoagents/dummy_agent.py` as a reference for the expected interface.
- Sensor data arrives as numpy arrays for cameras and LIDAR. Check `input_data[sensor_id][1]` for the data and `input_data[sensor_id][0]` for the frame number.
- The evaluator will reject your agent if it uses sensors not allowed by the chosen track.

## Environment Considerations

If your agent requires specific deep learning frameworks (e.g., PyTorch), you may need a separate conda environment. The HABIT paper evaluates InterFuser, TransFuser, and BEVDriver, each requiring different PyTorch versions.

See [agent_environments.md](agent_environments.md) for details on setting up agent-specific environments.
