from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QHBoxLayout
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import os
import platform
import subprocess


class SaroFallbackDialog(QDialog):
    def __init__(self, suggestions, full_image: QImage, pdf_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manual SARO Rename")
        self.setMinimumSize(600, 500)
        self.selected_text = ""
        self.pdf_path = pdf_path

        layout = QVBoxLayout()

        layout.addWidget(QLabel("📄 Preview (bottom-right of file):"))

        # 👉 Crop bottom-right quadrant for focused preview
        if not full_image.isNull():
            width, height = full_image.width(), full_image.height()
            start_x = int(width * 0.3)
            start_y = int(height * 0.65)
            crop_width = int(width * 0.7)
            crop_height = int(height * 0.35)

            # Bound check
            if start_x + crop_width > width:
                crop_width = width - start_x
            if start_y + crop_height > height:
                crop_height = height - start_y

            preview_qimage = full_image.copy(start_x, start_y, crop_width, crop_height)

            preview_label = QLabel()
            scaled = preview_qimage.scaled(750, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            preview_label.setPixmap(QPixmap.fromImage(scaled))
            layout.addWidget(preview_label)
        else:
            layout.addWidget(QLabel("⚠ Failed to load image preview."))

        # ComboBox for suggestions + free input
        layout.addWidget(QLabel("🔍 Choose a suggestion or type below:"))
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.addItems(suggestions)
        if suggestions:
            self.combo.setCurrentIndex(0)
        layout.addWidget(self.combo)

        # Open PDF system viewer
        open_btn = QPushButton("📂 Open File in System Viewer")
        open_btn.clicked.connect(self.open_pdf_in_viewer)
        layout.addWidget(open_btn)

        # Buttons
        btns = QHBoxLayout()
        ok_btn = QPushButton("✅ Rename")
        cancel_btn = QPushButton("❌ Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        self.setLayout(layout)

    def get_selected_text(self):
        return self.combo.currentText().strip()

    def open_pdf_in_viewer(self):
        if platform.system() == 'Windows':
            os.startfile(self.pdf_path)
        elif platform.system() == 'Darwin':
            subprocess.call(['open', self.pdf_path])
        else:
            subprocess.call(['xdg-open', self.pdf_path])
