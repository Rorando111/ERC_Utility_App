import os
import shutil
import pdf2image
import pytesseract
from PyPDF2 import PdfReader, PdfWriter
from utils.dialogs import show_error, show_warning
from utils.helpers import sanitize_filename

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton,
    QInputDialog, QMessageBox, QLineEdit, QFileDialog
)
from PyQt5.QtGui import QDesktopServices, QKeyEvent
from PyQt5.QtCore import QUrl, Qt


def extract_and_rename_pdfs(folder_path, output_widget, progress_bar=None):
    if not os.path.isdir(folder_path):
        show_error("Invalid folder path.")
        return

    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    if not pdf_files:
        output_widget.append("No PDF files found in the selected folder.\n")
        return

    total = len(pdf_files)
    if progress_bar:
        progress_bar.setMaximum(total)
        progress_bar.setValue(0)

    for count, filename in enumerate(pdf_files, start=1):
        pdf_path = os.path.join(folder_path, filename)
        try:
            images = pdf2image.convert_from_path(pdf_path)
        except Exception as e:
            output_widget.append(f"Failed to convert {filename}: {e}")
            continue

        serial_number = None
        for image in images:
            text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
            for line in text.split('\n'):
                if 'Serial No.' in line:
                    serial_number = sanitize_filename(line.split('Serial No.')[-1].strip())
                    break
            if serial_number:
                break

        if serial_number:
            new_filename = f"{serial_number}.pdf"
            new_path = os.path.join(folder_path, new_filename)
            if not os.path.exists(new_path):
                try:
                    os.rename(pdf_path, new_path)
                    output_widget.append(f"Renamed: {filename} → {new_filename}")
                except Exception as e:
                    output_widget.append(f"Error renaming {filename}: {e}")
            else:
                output_widget.append(f"Skipped: {new_filename} already exists.")
        else:
            output_widget.append(f"Serial number not found in {filename}")

        if progress_bar:
            progress_bar.setValue(count)

    open_and_manage_files(folder_path)


def open_and_manage_files(folder_path):
    class FileListDialog(QDialog):
        def __init__(self, folder_path, parent=None):
            super().__init__(parent)
            self.folder_path = folder_path
            self.setWindowTitle("Manage PDF Files")
            self.resize(500, 400)
            self.initUI()

        def initUI(self):
            layout = QVBoxLayout()
            self.list_widget = QListWidget()
            self.populate_list()
            layout.addWidget(self.list_widget)

            self.list_widget.itemDoubleClicked.connect(self.open_file)
            self.list_widget.keyPressEvent = self.list_key_press

            button_layout = QHBoxLayout()
            open_button = QPushButton("Open")
            open_button.clicked.connect(self.open_file)
            rename_button = QPushButton("Rename")
            rename_button.clicked.connect(self.rename_file)
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(self.delete_file)
            move_button = QPushButton("Move")
            move_button.clicked.connect(self.move_file)

            button_layout.addWidget(open_button)
            button_layout.addWidget(rename_button)
            button_layout.addWidget(delete_button)
            button_layout.addWidget(move_button)

            layout.addLayout(button_layout)
            self.setLayout(layout)

        def populate_list(self):
            self.list_widget.clear()
            pdf_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith('.pdf')]
            self.list_widget.addItems(pdf_files)

        def get_selected_file(self):
            selected = self.list_widget.selectedItems()
            if not selected:
                QMessageBox.warning(self, "No Selection", "Please select a file.")
                return None
            return selected[0].text()

        def open_file(self, *args):
            file = self.get_selected_file()
            if file:
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.join(self.folder_path, file)))

        def rename_file(self):
            old_name = self.get_selected_file()
            if not old_name:
                return
            new_name, ok = QInputDialog.getText(self, "Rename File", "Enter new name:", QLineEdit.Normal, old_name)
            if ok and new_name:
                new_name = sanitize_filename(new_name)
                if not new_name.endswith(".pdf"):
                    new_name += ".pdf"
                src = os.path.join(self.folder_path, old_name)
                dst = os.path.join(self.folder_path, new_name)
                if not os.path.exists(dst):
                    try:
                        os.rename(src, dst)
                        self.populate_list()
                        QMessageBox.information(self, "Renamed", f"{old_name} → {new_name}")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to rename: {e}")
                else:
                    QMessageBox.warning(self, "Exists", "File with that name already exists.")

        def delete_file(self):
            file = self.get_selected_file()
            if not file:
                return
            confirm = QMessageBox.question(self, "Confirm Delete", f"Delete {file}?", QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                try:
                    os.remove(os.path.join(self.folder_path, file))
                    self.populate_list()
                    QMessageBox.information(self, "Deleted", f"{file} deleted.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

        def move_file(self):
            file = self.get_selected_file()
            if not file:
                return
            target_folder = QFileDialog.getExistingDirectory(self, "Select Destination")
            if target_folder:
                src = os.path.join(self.folder_path, file)
                dst = os.path.join(target_folder, file)
                if os.path.exists(dst):
                    QMessageBox.warning(self, "Exists", "File already exists in destination.")
                else:
                    try:
                        shutil.move(src, dst)
                        self.populate_list()
                        QMessageBox.information(self, "Moved", f"{file} moved successfully.")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Move failed: {e}")

        def list_key_press(self, event: QKeyEvent):
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.open_file()
            else:
                QListWidget.keyPressEvent(self.list_widget, event)

    dialog = FileListDialog(folder_path)
    dialog.exec_()


def split_pdf(input_pdf, output_folder, output_widget, progress_bar=None):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        reader = PdfReader(input_pdf)
        total_pages = len(reader.pages)
        if progress_bar:
            progress_bar.setMaximum(total_pages)
            progress_bar.setValue(0)

        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            out_path = os.path.join(output_folder, f"page_{i + 1}.pdf")
            with open(out_path, "wb") as out_pdf:
                writer.write(out_pdf)
            output_widget.append(f"Saved: {out_path}")
            if progress_bar:
                progress_bar.setValue(i + 1)

    except Exception as e:
        output_widget.append(f"Error splitting PDF: {e}")
