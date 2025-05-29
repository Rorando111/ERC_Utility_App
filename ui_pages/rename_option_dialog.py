from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QIcon
class RenameOptionDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Rename Option")
        self.setWindowIcon(QIcon("rename.png"))
        self.setFixedSize(300, 160)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Which type of files do you want to rename?"))

        self.obr_button = QPushButton("OBR")
        self.nca_button = QPushButton("NCA")
        self.saro_button = QPushButton("SARO")

        layout.addWidget(self.obr_button)
        layout.addWidget(self.nca_button)
        layout.addWidget(self.saro_button)

        self.setLayout(layout)

        self.obr_button.clicked.connect(lambda: self.done(1))
        self.nca_button.clicked.connect(lambda: self.done(2))
        self.saro_button.clicked.connect(lambda: self.done(3))
