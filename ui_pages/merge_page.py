import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QFileDialog, QMessageBox, QLabel,
)
from PyPDF2 import PdfMerger
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.logger import log_action

class MergePDFPage(QWidget):
    def __init__(self, switch_page_callback=None, username="Unknown"):
        super().__init__()
        self.switch_page = switch_page_callback
        self.username = username
        self.selected_files = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        back_btn = QPushButton("⬅ Back")
        back_btn.setFont(QFont("Segoe UI", 11))
        back_btn.setFixedWidth(120)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #cccccc;
                color: #333;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #bbbbbb;
            }
        """)
        back_btn.clicked.connect(lambda: self.switch_page("main"))
        layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        layout.addWidget(QLabel("📑 Select and merge PDF files"))

        self.main_pdf_btn = QPushButton("Select first PDF")
        self.main_pdf_btn.clicked.connect(self.select_first_file)
        layout.addWidget(self.main_pdf_btn)

        self.other_pdf_btn = QPushButton("Select Other PDFs to be merged")
        self.other_pdf_btn.clicked.connect(self.select_other_files)
        layout.addWidget(self.other_pdf_btn)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.setDragDropMode(QListWidget.InternalMove)
        layout.addWidget(self.file_list)

        self.merge_btn = QPushButton("Merge PDFs")
        self.merge_btn.clicked.connect(self.merge_pdfs)
        layout.addWidget(self.merge_btn)

        self.setLayout(layout)

        self.main_file = None
        self.other_files = []

    def select_first_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select First PDF", "", "PDF Files (*.pdf)")
        if file:
            self.first_file = file
            self.update_file_list()

    def select_other_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Other PDFs", "", "PDF Files (*.pdf)")
        if files:
            self.selected_files = files
            self.update_file_list()

    def update_file_list(self):
        self.file_list.clear()
        if hasattr(self, 'first_file') and self.first_file:
            self.file_list.addItem(f"[First] {os.path.basename(self.first_file)}")
        for file in self.selected_files:
            self.file_list.addItem(os.path.basename(file))


    def merge_pdfs(self):
        if not self.first_file or not self.selected_files:
            QMessageBox.warning(self, "Incomplete Selection", "Please select a first file and at least one other file to merge.")
            return

        all_files = [self.first_file] + self.selected_files

        folder = os.path.dirname(self.first_file)
        default_name = os.path.splitext(os.path.basename(self.first_file))[0] + "_merged.pdf"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged PDF", os.path.join(folder, default_name), "PDF Files (*.pdf)"
        )
        if not save_path:
            return

        try:
            merger = PdfMerger()
            for file in all_files:
                merger.append(file)
            merger.write(save_path)
            merger.close()

            QMessageBox.information(self, "Success", f"Merged PDF saved to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to merge PDFs:\n{str(e)}")

    def cancel_operation(self):
        # Call this method when a merge operation is canceled
        log_action(self.username, "Merge Canceled", [])
        # ...existing cancel logic...
