from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PyQt5.QtGui import QIcon
from core.user_auth import signup

class SignupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create an Account")
        self.setWindowIcon(QIcon("njz.png"))
        self.setFixedSize(350, 300)
        self.setStyleSheet("font-family: 'Segoe UI'; font-size: 14px;")

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 30, 20, 20)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password)

        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        layout.addWidget(self.email)

        signup_btn = QPushButton("Sign Up")
        signup_btn.clicked.connect(self.handle_signup)
        signup_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(signup_btn)

        self.setLayout(layout)

    def handle_signup(self):
        username = self.username.text().strip()
        password = self.password.text().strip()
        email = self.email.text().strip()

        if not username or not password or not email:
            QMessageBox.warning(self, "Missing Info", "All fields are required.")
            return

        ok, msg = signup(username, password, email)
        if ok:
            QMessageBox.information(self, "Signup Successful", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Signup Failed", msg)
