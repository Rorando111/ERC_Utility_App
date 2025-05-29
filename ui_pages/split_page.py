from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar, QFileDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from core.pdf_utils import split_pdf, show_warning
from config.constants import FONT_SIZE, DEFAULT_FONT, SECONDARY_COLOR
from core.logger import log_action

class SplitPage(QWidget):
    def __init__(self, switch_page, username="Unknown"):
        super().__init__()
        self.switch_page = switch_page
        self.username = username
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        title = QLabel("Split PDF into Individual Pages")
        title.setStyleSheet(f"background-color: {SECONDARY_COLOR}; color: black; font: bold 14pt '{DEFAULT_FONT}';")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form_layout1 = QHBoxLayout()
        self.input_entry = QLineEdit()
        self.input_entry.setPlaceholderText("Select PDF file")
        self.input_entry.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        form_layout1.addWidget(self.input_entry)

        btn_browse_pdf = QPushButton("📂 Select PDF")
        btn_browse_pdf.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        btn_browse_pdf.clicked.connect(self.browse_pdf)
        form_layout1.addWidget(btn_browse_pdf)
        layout.addLayout(form_layout1)

        form_layout2 = QHBoxLayout()
        self.output_entry = QLineEdit()
        self.output_entry.setPlaceholderText("Select output folder")
        self.output_entry.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        form_layout2.addWidget(self.output_entry)

        btn_browse_folder = QPushButton("📁 Select Output Folder")
        btn_browse_folder.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        btn_browse_folder.clicked.connect(self.browse_folder)
        form_layout2.addWidget(btn_browse_folder)
        layout.addLayout(form_layout2)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        layout.addWidget(self.output_text)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        btn_action = QPushButton("🚀 Start Splitting")
        btn_action.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        btn_action.clicked.connect(self.start_splitting)
        layout.addWidget(btn_action)

        btn_back = QPushButton("⬅ Back")
        btn_back.setFont(QFont(DEFAULT_FONT, FONT_SIZE))
        btn_back.clicked.connect(lambda: self.switch_page("main"))
        layout.addWidget(btn_back)
        self.setLayout(layout)

    def browse_pdf(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if fname:
            self.input_entry.setText(fname)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_entry.setText(folder)

    def start_splitting(self):
        input_pdf = self.input_entry.text().strip()
        output_folder = self.output_entry.text().strip()
        if not input_pdf or not output_folder:
            show_warning("Please select both input PDF and output folder.")
            return
        self.output_text.clear()
        split_pdf(input_pdf, output_folder, self.output_text, self.progress_bar)

    def cancel_operation(self):
        # Call this method when a split operation is canceled
        log_action(self.username, "Split Canceled", [])
        # ...existing cancel logic...
