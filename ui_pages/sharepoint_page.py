from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QFileDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from core.pdf_utils import show_warning
from core.sharepoint_utils import authenticate_user, logout_user, extract_and_save
from config.constants import FONT_SIZE, DEFAULT_FONT, SECONDARY_COLOR
from core.logger import log_action

class SharepointPage(QWidget):
    def __init__(self, switch_page, username="Unknown"):
        super().__init__()
        self.switch_page = switch_page
        self.username = username
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        title = QLabel("Extract SharePoint PDF Links")
        title.setStyleSheet(f"background-color: {SECONDARY_COLOR}; color: black; font: bold 14pt '{DEFAULT_FONT}';")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form_layout = QFormLayout()
        self.link_entry = QLineEdit()
        self.username_entry = QLineEdit()
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)

        form_layout.addRow("SharePoint Folder Link:", self.link_entry)
        form_layout.addRow("Username:", self.username_entry)
        form_layout.addRow("Password:", self.password_entry)
        layout.addLayout(form_layout)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        btn_auth = QPushButton("Authenticate")
        btn_auth.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        btn_auth.clicked.connect(self.authenticate)
        layout.addWidget(btn_auth)

        btn_logout = QPushButton("Logout")
        btn_logout.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        btn_logout.clicked.connect(self.logout)
        layout.addWidget(btn_logout)

        form_layout2 = QHBoxLayout()
        self.save_location_entry = QLineEdit()
        btn_browse = QPushButton("Browse")
        btn_browse.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        btn_browse.clicked.connect(self.browse_save_location)

        form_layout2.addWidget(self.save_location_entry)
        form_layout2.addWidget(btn_browse)
        layout.addLayout(form_layout2)

        btn_extract = QPushButton("Extract & Save Excel")
        btn_extract.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        btn_extract.clicked.connect(self.extract_and_save)
        layout.addWidget(btn_extract)

        btn_back = QPushButton("⬅ Back")
        btn_back.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        btn_back.clicked.connect(lambda: self.switch_page("main"))
        layout.addWidget(btn_back)
        self.setLayout(layout)

    def authenticate(self):
        authenticate_user(self.link_entry.text(), self.username_entry.text(), self.password_entry.text(), self.status_label)

    def logout(self):
        logout_user(self.status_label, self.username_entry, self.password_entry)

    def browse_save_location(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if folder:
            self.save_location_entry.setText(folder)

    def extract_and_save(self):
        extract_and_save(self.link_entry.text(), self.save_location_entry.text(), self.status_label)
#             self.output_text.append("Please select both input PDF and output folder.")
#             return