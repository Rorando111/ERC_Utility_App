import sys
import os
import pytesseract
from pdf2image import convert_from_path
import json
import time
from PyQt5.QtWidgets import QApplication, QMessageBox
from ui_pages.main_window import PDFUtilityTool
from ui_pages.login_page import LoginPage

# Ensure core package is recognized
import core
from core.ocr_config import set_tesseract_path, set_poppler_path

def load_ocr_paths():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_config.json")
    print(f"Looking for config at: {config_path}")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            print(f"Loaded config: {config}")
            tesseract_path = config.get("tesseract_path")
            if tesseract_path and os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                # TESSDATA_PREFIX should point to the tessdata directory
                tessdata_path = os.path.join(os.path.dirname(tesseract_path), "tessdata")
                os.environ["TESSDATA_PREFIX"] = tessdata_path
                print(f"Tesseract path set to: {tesseract_path}")
                print(f"TESSDATA_PREFIX set to: {tessdata_path}")
            poppler_path = config.get("poppler_path")
            if poppler_path and os.path.exists(poppler_path):
                print(f"Setting Poppler path to: {poppler_path}")
                os.environ["POPPLER_PATH"] = poppler_path  # Set POPPLER_PATH
                os.environ["PATH"] = f"{poppler_path};" + os.environ.get("PATH", "")  # Add to PATH
                print(f"Environment PATH updated: {os.environ["PATH"]}")
                os.environ["POPPLER_PATH"] = poppler_path

        except Exception as e:
            print(f"Error loading OCR paths: {e}")

def main():
    load_ocr_paths()
    app = QApplication(sys.argv)
    window = PDFUtilityTool()

    try:
        with open("remember_me.json", "r") as f:
            saved = json.load(f)
            if "username" in saved and "timestamp" in saved:
                if time.time() - saved["timestamp"] < 30 * 24 * 60 * 60:  # 30 days
                    window.on_login_success(saved["username"])

                    QMessageBox.information(
                        window,
                        "Welcome Back 👋",
                        f"Welcome back, {saved['username']}!"
)
                else:
                    os.remove("remember_me.json")
                    window.setCentralWidget(LoginPage(window.on_login_success))
            else:
                window.setCentralWidget(LoginPage(window.on_login_success))
    except Exception:
        window.setCentralWidget(LoginPage(window.on_login_success))

    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
