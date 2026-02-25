"""
Config loader for HABIT benchmark.
Loads config.yaml and resolves relative paths against the project root.
"""

import os
import yaml


_DEFAULT_CONFIG = "config.yaml"


def _find_project_root():
    """Walk up from this file to find the directory containing config.yaml."""
    path = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isfile(os.path.join(path, "config.yaml")):
            return path
        path = os.path.dirname(path)
    return None


def load_config(config_path=None):
    """
    Load the HABIT benchmark configuration.

    Parameters:
        config_path: Path to config.yaml. If None, searches upward from this file.

    Returns:
        dict with configuration values and resolved paths.
    """
    if config_path is None:
        config_path = os.environ.get("HABIT_CONFIG")

    if config_path is None:
        root = _find_project_root()
        if root is None:
            raise FileNotFoundError("Could not find config.yaml in project hierarchy")
        config_path = os.path.join(root, _DEFAULT_CONFIG)

    config_path = os.path.abspath(config_path)
    project_root = os.path.dirname(config_path)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Resolve relative paths under 'data' against project root
    data = config.get("data", {})
    for key in ("motions_dir", "spawn_points", "routes", "csvs_dir"):
        val = data.get(key)
        if val and not os.path.isabs(val):
            data[key] = os.path.join(project_root, val)

    config["project_root"] = project_root
    return config
