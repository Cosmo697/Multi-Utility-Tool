"""Simple YAML-based configuration storage."""

import os
import yaml

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "MultiUtilityTool")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f)
