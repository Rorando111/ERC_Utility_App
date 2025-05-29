from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QSpacerItem, QSizePolicy, QCheckBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from core.user_auth import login
from ui_pages.two_factor_dialog import TwoFactorDialog
from ui_pages.signup_dialog import SignupDialog
import json
import time
from core.logger import log_action

class LoginPage(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(120, 80, 120, 80)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Welcome to ERC PDF Utility Tool")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #333333; margin-bottom: 5px;")
        layout.addWidget(title)

        subtitle = QLabel("Login to your account to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666666; font-size: 12pt;")
        layout.addWidget(subtitle)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setMinimumHeight(40)
        self.username.setStyleSheet(self.input_style())
        layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(40)
        self.password.setStyleSheet(self.input_style())
        layout.addWidget(self.password)

        self.remember_me = QCheckBox("Remember Me")
        layout.addWidget(self.remember_me)

        self.login_btn = QPushButton("Login")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.setStyleSheet(self.primary_button())
        self.login_btn.clicked.connect(self.attempt_login)
        layout.addWidget(self.login_btn)

        self.signup_btn = QPushButton("Sign Up")
        self.signup_btn.setMinimumHeight(40)
        self.signup_btn.setStyleSheet(self.secondary_button())
        self.signup_btn.clicked.connect(self.open_signup_dialog)
        # layout.addWidget(self.signup_btn)

        # Or sign up label
        signup_hint = QLabel("or <a href='#'>sign up if you don't have an account</a>")
        signup_hint.setAlignment(Qt.AlignCenter)
        signup_hint.setStyleSheet("color: #666; font-size: 15px;")
        signup_hint.setOpenExternalLinks(False)
        signup_hint.linkActivated.connect(lambda: self.open_signup_dialog())
        layout.addWidget(signup_hint)

        layout.addSpacerItem(QSpacerItem(20, 80, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(layout)

    def input_style(self):
        return """
            QLineEdit {
                padding: 10px;
                border-radius: 10px;
                border: 1px solid #cccccc;
                background-color: #f9f9f9;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #a3c0ff;
                background-color: #ffffff;
            }
        """

    def primary_button(self):
        return """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """

    def secondary_button(self):
        return """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """

    def attempt_login(self):
        username = self.username.text().strip()
        password = self.password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Missing Info", "Please enter both username and password.")
            return

        ok, result = login(username, password)
        if ok:
            dialog = TwoFactorDialog(expected_code=result)
            if dialog.exec_() and dialog.result:
                if self.remember_me.isChecked():
                    with open("remember_me.json", "w") as f:
                        json.dump({"username": username, "timestamp": time.time()}, f)
                self.on_login_success(username)
            else:
                QMessageBox.warning(self, "Verification Failed", "Incorrect verification code.")
        else:
            QMessageBox.warning(self, "Login Failed", result)

    def open_signup_dialog(self):
        dialog = SignupDialog()
        dialog.exec_()
