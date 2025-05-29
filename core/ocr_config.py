import os
import json
import pytesseract

def load_ocr_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ocr_config.json")
    print(f"Loading config from: {config_path}")
    if os.path.exists(config_path):
        print("Config file exists")
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                print(f"Loaded config: {config}")
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    print("Config file not found")
    return {}

def get_tesseract_path():
    config = load_ocr_config()
    path = config.get("tesseract_path")
    if path and os.path.exists(path):
        return path
    return None

def set_tesseract_path(path):
    if path and os.path.exists(path):
        print(f"Setting pytesseract path to: {path}")
        pytesseract.pytesseract.tesseract_cmd = path
        tessdata_path = os.path.join(os.path.dirname(path), "tessdata")
        os.environ["TESSDATA_PREFIX"] = tessdata_path
        print(f"TESSDATA_PREFIX set to: {os.environ['TESSDATA_PREFIX']}")
        return True
    print(f"Failed to set Tesseract path: {path}")
    return False

def get_poppler_path():
    config = load_ocr_config()
    path = config.get("poppler_path")
    if path and os.path.exists(path):
        os.environ["POPPLER_PATH"] = path
        print(f"Setting POPPLER_PATH to: {path}")
        return path
    return None

def set_poppler_path(path):
    if path and os.path.exists(path):
        os.environ["POPPLER_PATH"] = path
        return True
    return False
