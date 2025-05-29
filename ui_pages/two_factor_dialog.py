from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtGui import QIcon

class TwoFactorDialog(QDialog):
    def __init__(self, expected_code):
        super().__init__()
        self.setWindowTitle("Two-Factor Authentication")
        self.setWindowIcon(QIcon("2fa.png"))
        self.expected_code = expected_code
        self.result = False

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter 6-digit code")
        self.code_input.setMaxLength(6)

        submit_btn = QPushButton("Verify")
        submit_btn.clicked.connect(self.verify)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("A verification code has been sent to your email."))
        layout.addWidget(self.code_input)
        layout.addWidget(submit_btn)

        self.setLayout(layout)

    def verify(self):
        if self.code_input.text().strip() == self.expected_code:
            self.result = True
            self.accept()
        else:
            self.result = False
            self.reject()
