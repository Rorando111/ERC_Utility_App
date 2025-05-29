import os
import json

def get_config_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "theme_config.json")

def load_theme():
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f).get("dark_mode", False)
        except json.JSONDecodeError:
            return False
    return False

def save_theme(enabled):
    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump({"dark_mode": enabled}, f)
