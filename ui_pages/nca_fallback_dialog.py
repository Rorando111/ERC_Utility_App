import subprocess
import platform
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QScrollArea, QSizePolicy
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from utils.image_utils import pil_image_to_qimage

class NcaFallbackDialog(QDialog):
    def __init__(self, parent=None, filename=None, image=None):
        super().__init__(parent)
        self.setWindowTitle("Manual NCA Number Entry")
        self.setMinimumSize(600, 400)
        self.result = None
        self.filename = filename
        layout = QVBoxLayout()

        if filename:
            label = QLabel(f"Enter NCA number for: <b>{filename}</b>")
        else:
            label = QLabel("Enter NCA number:")
        layout.addWidget(label)

        # Preview image (centered, large, scrollable, zoomable)
        self._zoom = 1.0
        if image is not None:
            img_label = QLabel()
            # Convert PIL image to QImage if needed
            if hasattr(image, 'mode') and hasattr(image, 'tobytes'):
                qimage = pil_image_to_qimage(image)
            else:
                qimage = image  # Assume already QImage
            self._original_pixmap = QPixmap.fromImage(qimage)
            img_label.setPixmap(self._original_pixmap)
            img_label.setAlignment(Qt.AlignCenter)
            img_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            img_label.adjustSize()
            self.img_label = img_label

            scroll = QScrollArea()
            scroll.setWidgetResizable(False)  # Only show scrollbars if image is larger than area
            scroll.setWidget(img_label)
            layout.addWidget(QLabel("📄 Preview (first page):"))
            layout.addWidget(scroll)

            # Zoom controls
            zoom_layout = QHBoxLayout()
            zoom_in_btn = QPushButton("＋ Zoom In")
            zoom_out_btn = QPushButton("－ Zoom Out")
            zoom_in_btn.clicked.connect(self._zoom_in)
            zoom_out_btn.clicked.connect(self._zoom_out)
            zoom_layout.addWidget(zoom_in_btn)
            zoom_layout.addWidget(zoom_out_btn)
            layout.addLayout(zoom_layout)

        # Add open in system viewer button if filename is provided
        if filename:
            open_btn = QPushButton("📂 Open File in System Viewer")
            open_btn.clicked.connect(self.open_file)
            layout.addWidget(open_btn)

        layout.addWidget(QLabel("🔍 Type the NCA number below:"))
        self.input = QLineEdit()
        self.input.setPlaceholderText("NCA-XXX-X-XX-XXXXXXX or similar")
        layout.addWidget(self.input)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        self.setLayout(layout)

    def accept(self):
        self.result = self.input.text().strip()
        super().accept()

    def get_result(self):
        return self.result

    def _zoom_in(self):
        self._zoom = min(self._zoom * 1.25, 5.0)
        self._update_zoom()

    def _zoom_out(self):
        self._zoom = max(self._zoom * 0.8, 0.2)
        self._update_zoom()

    def _update_zoom(self):
        if hasattr(self, 'img_label') and hasattr(self, '_original_pixmap'):
            # Scale the pixmap for zoom, but ensure width and height are integers
            width = int(self._original_pixmap.width() * self._zoom)
            height = int(self._original_pixmap.height() * self._zoom)
            scaled_pixmap = self._original_pixmap.scaled(
                width,
                height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.img_label.setPixmap(scaled_pixmap)
            self.img_label.adjustSize()

    def open_file(self):
        # Open the file in the system's default PDF viewer
        if hasattr(self, 'filename') and self.filename:
            path = self.filename
        elif hasattr(self, 'pdf_path') and self.pdf_path:
            path = self.pdf_path
        else:
            return
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
