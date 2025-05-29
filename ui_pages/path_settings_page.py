from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt
import os
import json
import pytesseract
from core.ocr_config import set_tesseract_path, set_poppler_path
import sys

def get_config_path():
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "ocr_config.json")

def load_config():
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    return {}

def save_config(config):
    config_path = get_config_path()
    try:
        with open(config_path, "w") as f:
            json.dump(config, f)
        print("Config saved successfully")
    except Exception as e:
        print(f"Error saving config: {e}")
        raise

class PathSettingsPage(QWidget):
    def __init__(self, parent=None, back_callback=None):
        super().__init__(parent)
        self.back_callback = back_callback
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        self.tesseract_label = QLabel("Tesseract Path:")
        self.tesseract_input = QLineEdit()
        self.poppler_label = QLabel("Poppler Bin Path:")
        self.poppler_input = QLineEdit()
        self.save_btn = QPushButton("Save Paths")
        self.save_btn.clicked.connect(self.save_paths)
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.handle_back)

        config = load_config()
        self.tesseract_input.setText(config.get("tesseract_path", ""))
        self.poppler_input.setText(config.get("poppler_path", ""))

        layout.addWidget(self.tesseract_label)
        layout.addWidget(self.tesseract_input)
        layout.addWidget(self.poppler_label)
        layout.addWidget(self.poppler_input)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.back_btn, alignment=Qt.AlignLeft)
        self.setLayout(layout)

    def save_paths(self):
        try:
            tesseract_path = self.tesseract_input.text().strip()
            poppler_path = self.poppler_input.text().strip()
            print(f"Saving paths - Tesseract: {tesseract_path}, Poppler: {poppler_path}")
            
            config = load_config()
            errors = []
            
            if tesseract_path:
                print(f"Checking Tesseract path: {tesseract_path}")
                if os.path.exists(tesseract_path):
                    config["tesseract_path"] = tesseract_path
                    if not set_tesseract_path(tesseract_path):
                        errors.append("Failed to set Tesseract path")
                else:
                    errors.append(f"Tesseract path does not exist: {tesseract_path}")
            else:
                errors.append("Tesseract path is empty")
                
            if poppler_path:
                print(f"Checking Poppler path: {poppler_path}")
                if os.path.exists(poppler_path):
                    config["poppler_path"] = poppler_path
                    if not set_poppler_path(poppler_path):
                        errors.append("Failed to set Poppler path")
                else:
                    errors.append(f"Poppler path does not exist: {poppler_path}")
            else:
                errors.append("Poppler path is empty")
                
            try:
                save_config(config)
                print("Config saved successfully")
            except Exception as e:
                print(f"Error saving config: {e}")
                errors.append(f"Failed to save configuration: {str(e)}")
                
            if errors:
                QMessageBox.warning(self, "Path Error", "\n".join(errors))
            else:
                QMessageBox.information(self, "Success", "Paths saved successfully.")
                
        except Exception as e:
            print(f"Unexpected error in save_paths: {e}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    def handle_back(self):
        if self.back_callback:
            self.back_callback()
