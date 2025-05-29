from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from obr_extractor import PDFExtractor
from config.constants import DEFAULT_FONT, FONT_SIZE
from core.logger import log_action

class OBRPage(QWidget):
    def __init__(self, switch_page, apply_theme_callback, username = "Unknown"):
        super().__init__()
        self.switch_page = switch_page
        self.apply_theme_callback = apply_theme_callback
        layout = QVBoxLayout()

         # 🔙 Back button
        back_btn = QPushButton("⬅ Back")
        back_btn.setFont(QFont("Segoe UI", 8))
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

        self.obr_window = PDFExtractor(user=username)
        self.obr_window.theme_toggle.hide()
        layout.addWidget(self.obr_window.centralWidget())

       
        self.setLayout(layout)
