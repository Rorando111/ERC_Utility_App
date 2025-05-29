from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from config.constants import PRIMARY_COLOR, DEFAULT_FONT, FONT_SIZE
from core.logger import log_action

class MainMenuPage(QWidget):
    def __init__(self, switch_page):
        super().__init__()
        self.switch_page = switch_page
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)

        title = QLabel("ERC PDF Utility Tool")
        title.setStyleSheet(f"background-color: {PRIMARY_COLOR}; color: white; font: bold 20pt '{DEFAULT_FONT}';")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        button_labels = [
            ("🔍 Extract and Rename PDFs", "rename"),
            ("📄 Split PDF into Pages", "split"),
            ("📂 Extract SharePoint PDF Links", "sharepoint"),
            ("🧾 OBR Extractor", "obr"),
            ("🧩 Merge PDFs", "merge"),
            ("📋 View Activity Logs", "activity")
        ]

        for text, page in button_labels:
            btn = QPushButton(text)
            btn.setFixedWidth(260)
            btn.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
            btn.clicked.connect(lambda _, p=page: self.switch_page(p))
            main_layout.addWidget(btn, alignment=Qt.AlignCenter)

        main_layout.addStretch()
        self.setLayout(main_layout)
