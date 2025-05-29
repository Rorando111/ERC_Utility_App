import os
import re
import cv2
import platform
import numpy as np
import pytesseract
from PyQt5.QtWidgets import ( 
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar, QFileDialog, QMessageBox,
    QProgressDialog, QApplication, QDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QRubberBand,
    QInputDialog
)
import traceback
from PyQt5.QtGui import QFont, QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QEventLoop
from PIL import Image, ImageOps, ImageFilter
from pdf2image import convert_from_path
from config.constants import FONT_SIZE, DEFAULT_FONT, SECONDARY_COLOR
from core.logger import log_action
from ui_pages.rename_option_dialog import RenameOptionDialog
from utils.image_utils import preprocess_image, pil_image_to_qimage
from ui_pages.saro_fallback_dialog import SaroFallbackDialog
from ui_pages.path_settings_page import PathSettingsPage
from ui_pages.nca_fallback_dialog import NcaFallbackDialog
import json
import sys
from ui_pages.obr_fallback_dialog import ObrFallbackDialog


def create_styled_button(text):
    button = QPushButton(text)
    button.setFixedWidth(250)
    button.setStyleSheet("""
        QPushButton {
            background-color: #6c63ff;
            color: white;
            padding: 10px 20px;
            border-radius: 12px;
            font-size: 14px;
            font-family: 'Segoe UI';
            font-weight: 500;
            border: none;
        }
        QPushButton:hover {
            background-color: #574fd6;
        }
        QPushButton:pressed {
            background-color: #4c45c4;
        }
    """)
    return button

def get_config_path():
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "ocr_config.json")

CONFIG_FILE = get_config_path()

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def ensure_tesseract_path(parent=None):
    # Check if Tesseract is configured
    if pytesseract.pytesseract.tesseract_cmd:
        return True
    
    QMessageBox.warning(parent, "Tesseract Not Set", "Tesseract path is not set. Please use the settings button (gear icon) to set the Tesseract path.")
    return False

def ensure_poppler_path(parent=None):
    # Get Poppler path from environment
    poppler_path = os.environ.get("POPPLER_PATH")
    if (poppler_path and os.path.exists(poppler_path)):
        return poppler_path  # Return the actual path string
    
    QMessageBox.warning(parent, "Poppler Not Set", "Poppler path is not set or not working. Please use the settings button (gear icon) to configure the Poppler path.")
    return None

def extract_nca_number(image):
    try:
        text = pytesseract.image_to_string(image, config="--psm 6")
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        for i, line in enumerate(lines):
            if "2067" in line:
                if i > 0:
                    potential_nca = lines[i - 1]

                    # Priority: 7-digit NCA format
                    match = re.search(r"(NCA-[A-Z]{2,5}-[A-Z]-\d{2,4}-\d{7})", potential_nca)
                    if match:
                        return match.group(1).strip()

                    # Fallback: 6-digit variant
                    match = re.search(r"(NCA-[A-Z]{2,5}-[A-Z]-\d{2,4}-\d{6})", potential_nca)
                    if match:
                        return match.group(1).strip()

                    # Fallback: plain numeric code like '345247-0'
                    match = re.search(r"(\d{5,7}[-–]\d{1,3})", potential_nca)
                    if match:
                        return match.group(1).strip()

        return None
    except Exception as e:
        print(f"Error during OCR: {e}")
        return None
    
def extract_saro_number_from_image(image: Image.Image) -> str:
    # Convert image to grayscale for better OCR accuracy
    gray = image.convert("L")

    # Crop bottom-right corner (where SARO No. usually appears)
    width, height = gray.size
    cropped = gray.crop((int(width * 0.5), int(height * 0.75), width, height))

    # Run OCR on cropped section
    text = pytesseract.image_to_string(cropped)

    # Regex patterns for SARO No.
    patterns = [
        r"(SARO[-\s]?[A-Z]{3}[-\s]?[A-Z]?[-\s]?\d{2}[-\s]?\d{7})",  # e.g. SARO-BMB-A-08-0016104
        r"\b([A-Z]{1}-\d{2}-\d{5})\b"  # e.g. A-01-05818
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).replace(" ", "").strip()

    print("OCR text (no match):", text)
    return None

def extract_obr_number(text):
    try:
        # Try to match OBR serial patterns (CA-MOOE..., MOOE..., PGF..., PS...)
        match = re.search(r"(CA\-MOOE\S+|MOOE\S+|PGF\S+|PS\S+)", text)
        if match:
            return match.group(1).strip()
        return None
    except Exception as e:
        print(f"Error during OBR pattern matching: {e}")
        return None


class RenamePage(QWidget):
    def __init__(self, switch_page_callback, username="Unknown"):
        super().__init__()
        self.switch_page = switch_page_callback
        self.username = username
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Remove header row with duplicate dark mode and tesseract settings buttons
        # Only the main window should provide these buttons in the global header

        # Start Renaming button centered
        rename_btn = create_styled_button("Start Renaming")
        rename_btn.clicked.connect(self.extract_and_rename_dialog)
        layout.addWidget(rename_btn, alignment=Qt.AlignHCenter)

        # Back button below
        back_btn = create_styled_button("Back")
        back_btn.clicked.connect(lambda: self.switch_page("main"))
        layout.addWidget(back_btn, alignment=Qt.AlignHCenter)

        layout.addStretch()
        self.setLayout(layout)

    def extract_and_rename_dialog(self):
        dialog = RenameOptionDialog(self)
        choice = dialog.exec_()
        if choice == 1:
            self.rename_obr_files()
            log_action(self.username, "Renamed PDFs", ["Mode: OBR"])
        elif choice == 2:
            self.rename_nca_files()
            log_action(self.username, "Renamed PDFs", ["Mode: NCA"])
        elif choice == 3:
            self.rename_saro_files()
            log_action(self.username, "Renamed PDFs", ["Mode: SARO"])

    def rename_obr_files(self):
        from core.ocr_config import get_tesseract_path
        tesseract_path = get_tesseract_path()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        if not ensure_tesseract_path(self):
            return
        poppler_path = ensure_poppler_path(self)
        if not poppler_path:
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with OBR PDFs")
        if not folder:
            return
        pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
        if not pdf_files:
            QMessageBox.information(self, "No PDFs", "No PDF files found in the folder.")
            return
        self.progress_dialog = QProgressDialog("Renaming OBR files...", "Cancel", 0, len(pdf_files), self)
        self.progress_dialog.setWindowTitle("Renaming OBR Files")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.worker_thread = QThread()
        self.worker = OBRRenameWorker(folder, pdf_files, poppler_path)
        self.worker.moveToThread(self.worker_thread)
        self.worker.progress.connect(self._on_rename_progress)
        self.worker.finished.connect(self._on_rename_finished)
        self.worker.canceled.connect(lambda: self._on_rename_canceled("OBR"))
        self.worker.manual_input_requested.connect(self._on_obr_manual_input)
        self.progress_dialog.canceled.connect(self.worker.cancel)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def _on_rename_progress(self, i, label):
        self.progress_dialog.setValue(i)
        self.progress_dialog.setLabelText(label)

    def _on_rename_finished(self, renamed, skipped, summary):
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.progress_dialog.close()
        message = f"✅ Renamed {renamed} OBR files."
        if skipped:
            message += "\n\n⚠ Skipped Files:\n" + "\n".join(skipped[:10])
            if len(skipped) > 10:
                message += "\n..."
        QMessageBox.information(self, "Renaming Complete", message)
        if skipped:
            self.show_skipped_files_preview(skipped)
        # Log the rename activity for OBR, NCA, SARO
        if hasattr(self.parent(), 'on_rename_completed'):
            self.parent().on_rename_completed(self.username, renamed, skipped, "OBR")

    def _on_rename_canceled(self, mode=None):
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.progress_dialog.close()
        QMessageBox.information(self, "Canceled", "Renaming was canceled.")
        # Log the cancellation event
        if hasattr(self.parent(), 'on_rename_canceled'):
            self.parent().on_rename_canceled(self.username, mode or "Unknown")
        else:
            log_action(self.username, f"Renaming Canceled", [f"Mode: {mode or 'Unknown'}"])
        self.worker_thread.quit()
        self.worker_thread.wait()

    def _on_nca_manual_input(self, file, image):
        dialog = NcaFallbackDialog(self, filename=file, image=image)
        if dialog.exec_() == QDialog.Accepted and dialog.get_result():
            self.worker.manual_input_result.emit(dialog.get_result())
        else:
            self.worker.manual_input_result.emit("")
            
    def _on_obr_manual_input(self, file, image, pdf_path, suggestions):
        dialog = ObrFallbackDialog(suggestions, image, pdf_path, self)
        if dialog.exec_() == QDialog.Accepted:
            self.worker.manual_input_result.emit(dialog.combo.currentText().strip())
        else:
            self.worker.manual_input_result.emit("")
            
    def _on_saro_manual_input(self, file, image, pdf_path, suggestions):
        dialog = SaroFallbackDialog(suggestions, image, pdf_path, self)
        if dialog.exec_() == QDialog.Accepted:
            self.worker.manual_input_result.emit(dialog.combo.currentText().strip())
        else:
            self.worker.manual_input_result.emit("")

    def _on_rename_finished_nca(self, renamed, skipped, summary):
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.progress_dialog.close()
        message = f"✅ Renamed {renamed} NCA files."
        if skipped:
            message += "\n\n⚠ Skipped Files:\n" + "\n".join(skipped[:10])
            if len(skipped) > 10:
                message += "\n..."
        QMessageBox.information(self, "Renaming Complete", message)
        if skipped:
            self.show_skipped_files_preview(skipped)
        if hasattr(self.parent(), 'on_rename_completed'):
            self.parent().on_rename_completed(self.username, renamed, skipped, "NCA")

    def rename_nca_files(self):
        from core.ocr_config import get_tesseract_path
        tesseract_path = get_tesseract_path()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        if not ensure_tesseract_path(self):
            return
        poppler_path = ensure_poppler_path(self)
        if not poppler_path:
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with NCA PDFs")
        if not folder:
            return
        pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
        if not pdf_files:
            QMessageBox.information(self, "No PDFs", "No PDF files found in the folder.")
            return
        self.progress_dialog = QProgressDialog("Renaming NCA files...", "Cancel", 0, len(pdf_files), self)
        self.progress_dialog.setWindowTitle("Renaming NCA Files")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.worker_thread = QThread()
        self.worker = NCARenameWorker(folder, pdf_files, poppler_path)
        self.worker.moveToThread(self.worker_thread)
        self.worker.progress.connect(self._on_rename_progress)
        self.worker.finished.connect(self._on_rename_finished_nca)
        self.worker.canceled.connect(lambda: self._on_rename_canceled("NCA"))
        self.worker.manual_input_requested.connect(self._on_nca_manual_input)
        self.progress_dialog.canceled.connect(self.worker.cancel)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def rename_saro_files(self):
        from core.ocr_config import get_tesseract_path
        tesseract_path = get_tesseract_path()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        if not ensure_tesseract_path(self):
            return
        poppler_path = ensure_poppler_path(self)
        if not poppler_path:
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with SARO PDFs")
        if not folder:
            return
        pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
        if not pdf_files:
            QMessageBox.information(self, "No PDFs", "No PDF files found in the folder.")
            return
        self.progress_dialog = QProgressDialog("Renaming SARO files...", "Cancel", 0, len(pdf_files), self)
        self.progress_dialog.setWindowTitle("Renaming SARO Files")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.worker_thread = QThread()
        self.worker = SARORenameWorker(folder, pdf_files, poppler_path)
        self.worker.moveToThread(self.worker_thread)
        self.worker.progress.connect(self._on_rename_progress)
        self.worker.finished.connect(self._on_rename_finished)
        self.worker.canceled.connect(lambda: self._on_rename_canceled("SARO"))
        self.worker.manual_input_requested.connect(self._on_saro_manual_input)
        self.progress_dialog.canceled.connect(self.worker.cancel)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def show_skipped_files_preview(self, skipped_files):
        dialog = QDialog(self)
        dialog.setWindowTitle("Skipped Files Preview")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout()
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setText("\n".join(skipped_files))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)

        layout.addWidget(text_area)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        dialog.setLayout(layout)

        dialog.exec_()

class OBRRenameWorker(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(int, list, list)
    canceled = pyqtSignal()
    manual_input_requested = pyqtSignal(str, object, str, list)  # file, image, pdf_path, suggestions
    manual_input_result = pyqtSignal(str)

    def __init__(self, folder, pdf_files, poppler_path):
        super().__init__()
        self.folder = folder
        self.pdf_files = pdf_files
        self.poppler_path = poppler_path
        self._cancel = False
        self._manual_result = None
        self._event_loop = None
        self.manual_input_result.connect(self._on_manual_input_result)

    def cancel(self):
        self._cancel = True
        if self._event_loop:
            self._event_loop.quit()
            
    def _on_manual_input_result(self, value):
        self._manual_result = value
        if self._event_loop:
            self._event_loop.quit()

    def run(self):
        renamed, skipped, summary = 0, [], []
        for i, file in enumerate(self.pdf_files):
            if self._cancel:
                self.canceled.emit()
                return
            self.progress.emit(i, f"Processing {file} ({i+1}/{len(self.pdf_files)})")
            path = os.path.join(self.folder, file)
            try:
                if self._cancel:
                    self.canceled.emit()
                    return
                image = convert_from_path(path, first_page=1, last_page=1, poppler_path=self.poppler_path)[0]
                if self._cancel:
                    self.canceled.emit()
                    return
                QThread.msleep(100)  # Add small delay after PDF conversion
                text = pytesseract.image_to_string(image)
                if self._cancel:
                    self.canceled.emit()
                    return
                QThread.msleep(50)  # Add small delay after OCR
                serial = extract_obr_number(text)
                if self._cancel:
                    self.canceled.emit()
                    return
                if serial:
                    new_name = f"{serial}.pdf"
                    new_path = os.path.join(self.folder, new_name)
                    if not os.path.exists(new_path):
                        os.rename(path, new_path)
                        renamed += 1
                        summary.append(f"{file} ➔ {new_name}")
                    else:
                        skipped.append(f"{file} (already exists as {new_name})")
                    continue
                # Try to find potential OBR numbers for suggestions
                suggestions = []
                lines = text.splitlines()
                for line in lines:
                    if any(pattern in line.upper() for pattern in ['CA-MOOE', 'MOOE', 'PGF', 'PS']):
                        suggestions.append(line.strip())
                suggestions = list(dict.fromkeys(suggestions))[:3]  # Unique, max 3
                
                # Crop image to show top-right corner where OBR numbers typically appear
                width, height = image.size
                cropped_image = image.crop((int(width * 0.5), 0, width, int(height * 0.3)))
                preview_image = pil_image_to_qimage(cropped_image)
                
                # Manual fallback with suggestions
                self._manual_result = None
                self._event_loop = QEventLoop()
                self.manual_input_requested.emit(file, preview_image, path, suggestions)
                self._event_loop.exec_()
                manual_value = self._manual_result
                self._event_loop = None
                
                if manual_value and manual_value.strip():
                    new_name = f"{manual_value.strip()}.pdf"
                    new_path = os.path.join(self.folder, new_name)
                    if not os.path.exists(new_path):
                        os.rename(path, new_path)
                        renamed += 1
                        summary.append(f"{file} ➔ {new_name}")
                    else:
                        skipped.append(f"{file} (already exists as {new_name})")
                else:
                    skipped.append(f"{file} (OBR number not found)")
            except Exception as e:
                skipped.append(f"{file} (error: {e})")
        self.finished.emit(renamed, skipped, summary)

class NCARenameWorker(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(int, list, list)
    canceled = pyqtSignal()
    manual_input_requested = pyqtSignal(str, object)  # file, image
    manual_input_result = pyqtSignal(str)

    def __init__(self, folder, pdf_files, poppler_path):
        super().__init__()
        self.folder = folder
        self.pdf_files = pdf_files
        self.poppler_path = poppler_path
        self._cancel = False
        self._manual_result = None
        self._event_loop = None
        self.manual_input_result.connect(self._on_manual_input_result)

    def cancel(self):
        self._cancel = True
        if self._event_loop:
            self._event_loop.quit()

    def _on_manual_input_result(self, value):
        self._manual_result = value
        if self._event_loop:
            self._event_loop.quit()

    def run(self):
        renamed, skipped, summary = 0, [], []
        for i, file in enumerate(self.pdf_files):
            if self._cancel:
                self.canceled.emit()
                return
            self.progress.emit(i, f"Processing {file} ({i+1}/{len(self.pdf_files)})")
            path = os.path.join(self.folder, file)
            try:
                image = convert_from_path(path, first_page=1, last_page=1, poppler_path=self.poppler_path)[0]
                if self._cancel:
                    self.canceled.emit()
                    return
                QThread.msleep(100)  # Add small delay after PDF conversion
                text = pytesseract.image_to_string(image)
                if self._cancel:
                    self.canceled.emit()
                    return
                QThread.msleep(50)  # Add small delay after OCR
                nca_number = extract_nca_number(image)
                if self._cancel:
                    self.canceled.emit()
                    return
                if nca_number:
                    new_name = f"{nca_number}.pdf"
                    new_path = os.path.join(self.folder, new_name)
                    if not os.path.exists(new_path):
                        os.rename(path, new_path)
                        renamed += 1
                        summary.append(f"{file} ➔ {new_name}")
                    else:
                        skipped.append(f"{file} (already exists as {new_name})")
                    continue
                # Manual fallback: request input from main thread
                self._manual_result = None
                self._event_loop = QEventLoop()
                self.manual_input_requested.emit(file, image)
                self._event_loop.exec_()
                manual_value = self._manual_result
                self._event_loop = None
                if manual_value and manual_value.strip():
                    new_name = f"{manual_value.strip()}.pdf"
                    new_path = os.path.join(self.folder, new_name)
                    if not os.path.exists(new_path):
                        os.rename(path, new_path)
                        renamed += 1
                        summary.append(f"{file} ➔ {new_name}")
                    else:
                        skipped.append(f"{file} (already exists as {new_name})")
                else:
                    skipped.append(f"{file} (NCA number not found)")
            except Exception as e:
                skipped.append(f"{file} (error: {e})")
        self.finished.emit(renamed, skipped, summary)

class SARORenameWorker(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(int, list, list)
    canceled = pyqtSignal()
    manual_input_requested = pyqtSignal(str, object, str, list)  # file, image, pdf_path, suggestions
    manual_input_result = pyqtSignal(str)

    def __init__(self, folder, pdf_files, poppler_path):
        super().__init__()
        self.folder = folder
        self.pdf_files = pdf_files
        self.poppler_path = poppler_path
        self._cancel = False
        self._manual_result = None
        self._event_loop = None
        self.manual_input_result.connect(self._on_manual_input_result)

    def cancel(self):
        self._cancel = True
        if self._event_loop:
            self._event_loop.quit()

    def _on_manual_input_result(self, value):
        self._manual_result = value
        if self._event_loop:
            self._event_loop.quit()

    def run(self):
        renamed, skipped, summary = 0, [], []
        for i, file in enumerate(self.pdf_files):
            if self._cancel:
                self.canceled.emit()
                return
            self.progress.emit(i, f"Processing {file} ({i+1}/{len(self.pdf_files)})")
            path = os.path.join(self.folder, file)
            try:
                if self._cancel:
                    self.canceled.emit()
                    return
                image = convert_from_path(path, first_page=1, last_page=1, poppler_path=self.poppler_path)[0]
                if self._cancel:
                    self.canceled.emit()
                    return
                QThread.msleep(100)  # Add small delay after PDF conversion
                text = pytesseract.image_to_string(image)
                if self._cancel:
                    self.canceled.emit()
                    return
                QThread.msleep(50)  # Add small delay after OCR
                # Try to find potential SARO numbers for suggestions
                suggestions = []
                match = re.search(r"SARO\s*No\.?\s*[:\-~]?\s*([A-Z0-9\-~]+)", text, re.IGNORECASE)
                if match:
                    suggestion = match.group(1).replace("~", "-").replace("–", "-").strip()
                    if not suggestion.upper().startswith(("SARO-", "A-")):
                        suggestion = "A-" + suggestion
                    suggestions.append(suggestion)
                
                # Look for additional patterns in each line
                lines = text.splitlines()
                for line in lines:
                    # Look for A-XX-XXXXX pattern
                    match = re.search(r"\b([A-Z]\-\d{2}\-\d{5})\b", line)
                    if match:
                        suggestions.append(match.group(1))
                    # Look for SARO-XXX-X-XX-XXXXXXX pattern
                    match = re.search(r"(SARO\-[A-Z]{3}\-[A-Z]\-\d{2}\-\d{7})", line)
                    if match:
                        suggestions.append(match.group(1))
                
                # Remove duplicates and limit to top 3
                suggestions = list(dict.fromkeys(suggestions))[:3]
                
                # Crop image to show bottom-right corner where SARO numbers typically appear
                width, height = image.size
                cropped_image = image.crop((int(width * 0.5), int(height * 0.7), width, height))
                preview_image = pil_image_to_qimage(cropped_image)
                
                # Manual fallback with suggestions
                self._manual_result = None
                self._event_loop = QEventLoop()
                self.manual_input_requested.emit(file, preview_image, path, suggestions)
                self._event_loop.exec_()
                manual_value = self._manual_result
                self._event_loop = None

                if manual_value and manual_value.strip():
                    fallback_name = manual_value.strip()
                    if not fallback_name.upper().startswith(("SARO-", "A-")):
                        fallback_name = "A-" + fallback_name
                    new_name = f"{fallback_name}.pdf"
                    new_path = os.path.join(self.folder, new_name)
                    if not os.path.exists(new_path):
                        os.rename(path, new_path)
                        renamed += 1
                        summary.append(f"{file} ➔ {new_name}")
                    else:
                        skipped.append(f"{file} (already exists as {new_name})")
                else:
                    skipped.append(f"{file} (SARO number not found)")
            except Exception as e:
                skipped.append(f"{file} (error: {e})")
        self.finished.emit(renamed, skipped, summary)