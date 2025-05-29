from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QHBoxLayout
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import subprocess
import platform
import os

class ObrFallbackDialog(QDialog):
    def __init__(self, suggestions, preview_image: QImage, pdf_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manual OBR Rename")
        self.setMinimumSize(600, 400)
        self.selected_text = ""
        self.pdf_path = pdf_path

        layout = QVBoxLayout()

        layout.addWidget(QLabel("📄 Preview (top-right corner where 'Serial No.' usually appears):"))

        if preview_image:
            label = QLabel()
            pixmap = QPixmap.fromImage(preview_image)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)

        layout.addWidget(QLabel("🔍 Choose a suggestion or type below:"))
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.addItems(suggestions)
        if suggestions:
            self.combo.setCurrentIndex(0)
        layout.addWidget(self.combo)

        open_btn = QPushButton("📂 Open File in System Viewer")
        open_btn.clicked.connect(self.open_file)
        layout.addWidget(open_btn)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("✅ Rename")
        cancel_btn = QPushButton("❌ Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def get_selected_text(self):
        return self.combo.currentText().strip()

    def open_file(self):
        if platform.system() == "Windows":
            os.startfile(self.pdf_path)
        elif platform.system() == "Darwin":
            subprocess.call(["open", self.pdf_path])
        else:
            subprocess.call(["xdg-open", self.pdf_path])