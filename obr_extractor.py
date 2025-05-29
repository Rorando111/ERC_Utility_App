import os
import re
import sys
import pytesseract
import pandas as pd
import cv2
import numpy as np
from core.logger import log_action
import csv
import json
from pdf2image import convert_from_path
from PIL import Image
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QPushButton, QWidget, QHBoxLayout, QLineEdit, QMenu, QMessageBox, QProgressDialog,
    QHeaderView, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QRubberBand, QDialog, QLabel, QTextEdit, QAbstractItemView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QRect, QSize, QPoint
from PyQt5.QtGui import QPixmap, QImage, QColor, QIcon, QKeySequence



def pil_to_pixmap(pil_image):
    open_cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    height, width, channel = open_cv_image.shape
    bytes_per_line = 3 * width
    q_img = QImage(open_cv_image.data, width, height, bytes_per_line, QImage.Format_BGR888)
    return QPixmap.fromImage(q_img)

class CropGraphicsView(QGraphicsView):
    def __init__(self, pixmap, callback):
        super().__init__()
        self.callback = callback
        self.origin = QPoint()
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.setScene(QGraphicsScene(self))
        self.scene().addItem(self.pixmap_item)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.rubberBand.isVisible():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubberBand.hide()
            rect = self.rubberBand.geometry()
            scene_rect = self.mapToScene(rect).boundingRect().toRect()
            x1, y1, x2, y2 = scene_rect.left(), scene_rect.top(), scene_rect.right(), scene_rect.bottom()
            self.callback((x1, y1, x2, y2))
        super().mouseReleaseEvent(event)

class PDFCropViewer(QDialog):
    def __init__(self, pil_image, callback):
        super().__init__()
        self.setWindowTitle("Select Area to Extract")
        self.setGeometry(200, 100, 1000, 800)
        self.original_pil_image = pil_image
        self.callback = callback

        pixmap = pil_to_pixmap(pil_image)
        self.view = CropGraphicsView(pixmap, self.extract_crop_text)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def extract_crop_text(self, rect_coords):
        try:
            x1, y1, x2, y2 = map(int, rect_coords)
            cropped = self.original_pil_image.crop((x1, y1, x2, y2))
            text = pytesseract.image_to_string(cropped, lang="eng", config="--psm 6")
            self.callback(text.strip())
        except Exception as e:
            QMessageBox.warning(self, "OCR Error", str(e))
        self.accept()

class ExtractWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)
    result = pyqtSignal(list)

    def __init__(self, folder, files):
        super().__init__()
        self.folder = folder
        self.files = files
        self._is_running = True

    def cancel(self):
        self._is_running = False

    def run(self):
        from core.ocr_config import get_poppler_path, get_tesseract_path
        poppler_path = get_poppler_path()
        tesseract_path = get_tesseract_path()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        for i, filename in enumerate(self.files):
            if not self._is_running:
                break
            try:
                self.progress.emit(i, filename)
                image = convert_from_path(os.path.join(self.folder, filename), poppler_path=poppler_path)[0]
                text = pytesseract.image_to_string(image, lang="eng", config="--psm 6")
                serial = os.path.splitext(filename)[0]

                date_match = re.search(r"(?:Date\s*[:\-]?\s*)([A-Za-z]+\s+\d{1,2},\s+\d{4})", text, re.IGNORECASE)
                date = date_match.group(1) if date_match else ""

                payee = ""
                lines = text.split("\n")
                for i, line in enumerate(lines):
                    match = re.search(r"Payee\s*[:\-]?\s*(.+)", line, re.IGNORECASE)
                    if match and match.group(1).strip():
                        payee = match.group(1).strip()
                        break
                    if re.match(r"^\s*Payee\s*[:\-]?\s*$", line, re.IGNORECASE) and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line:
                            payee = next_line
                            break

                particulars_lines = []
                is_collecting = False
                blank_line_count = 0

                for line in lines:
                    stripped = line.strip()
                    lower = stripped.lower()
                    if not is_collecting and "to obligate" in lower:
                        match = re.search(r"(To obligate.*)", stripped, re.IGNORECASE)
                        if match:
                            particulars_lines.append(match.group(1).strip())
                            is_collecting = True
                        continue

                    if is_collecting:
                        if any(kw in lower for kw in ["certified", "signature", "position", "printed name", "head", "date:", "status of obligation"]):
                            break
                        if not stripped:
                            blank_line_count += 1
                            if blank_line_count >= 2:
                                break
                            continue
                        else:
                            blank_line_count = 0
                            particulars_lines.append(stripped)

                full_particulars = " ".join(particulars_lines)
                cleaned = re.split(r"\s+\d{10,}|\s+\d{3,}\.\d{2}|\|\s*\d+", full_particulars)[0].strip()

                total_match = re.search(r"Total\s*[:\s]*([\d,]+\.\d{2})", text)
                if total_match:
                    total_amount = f"{float(total_match.group(1).replace(',', '')):,.2f}"
                else:
                    amounts = [float(a.replace(",", "")) for a in re.findall(r"(\d{1,3}(?:,\d{3})*\.\d{2})", text)]
                    total_amount = f"{sum(amounts):,.2f}"

                row_data = [filename, serial, date, payee, cleaned, total_amount, "", "", total_amount]
                self.result.emit(row_data)

            except Exception as e:
                self.error.emit(f"Failed to process {filename}: {e}")

        self.finished.emit()

CONFIG_FILE = "theme_config.json"

def load_theme():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f).get("dark_mode", False)
    return False

def save_theme(enabled):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"dark_mode": enabled}, f)

class PDFExtractor(QMainWindow):
    def __init__(self, user = "Unknown"):
        super().__init__()
        self.user = user
        self.setWindowTitle("OBR Extractor")
        self.setWindowIcon(QIcon("icon.png"))
        self.setGeometry(100, 100, 1600, 900)
        self.folder_path = ""
        self.edit_log = []
        self.undo_stack = []
        self.redo_stack = []

        self.columns = ["File Name", "Serial No.", "Date", "Payee", "Particulars",
                        "Total Amount", "Payment", "Tax", "Balance", "Remarks"]

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.table.itemChanged.connect(self.log_edit)
        self.table.itemChanged.connect(self.recalculate_totals)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Folder path...")

        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search table...")
        self.search_entry.textChanged.connect(self.search_table)

        self.theme_toggle = QPushButton()
        self.theme_toggle.setCheckable(True)
        self.theme_toggle.setObjectName("ThemeToggle")
        self.theme_toggle.setIcon(QIcon("moon.png") if load_theme() else QIcon("sun.png"))
        self.theme_toggle.setToolTip("Toggle Dark Mode")
        self.theme_toggle.clicked.connect(self.toggle_dark_mode)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_folder)

        extract_button = QPushButton("Start Extraction")
        extract_button.clicked.connect(self.extract_pdfs)

        save_button = QPushButton("Save As")
        save_button.clicked.connect(self.save_as)

        open_button = QPushButton("Open File")
        open_button.clicked.connect(self.open_file)

        undo_button = QPushButton("Undo")
        undo_button.clicked.connect(self.undo_edit)

        redo_button = QPushButton("Redo")
        redo_button.clicked.connect(self.redo_edit)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(100)

        top_row1 = QHBoxLayout()
        top_row1.addWidget(self.entry)
        top_row1.addWidget(browse_button)
        top_row1.addWidget(extract_button)
        top_row1.addWidget(open_button)
        top_row1.addWidget(save_button)

        top_row2 = QHBoxLayout()
        top_row2.addWidget(undo_button)
        top_row2.addWidget(redo_button)
        top_row2.addWidget(self.search_entry)
        top_row2.addWidget(self.theme_toggle)

        top_layout = QVBoxLayout()
        top_layout.addLayout(top_row1)
        top_layout.addLayout(top_row2)


        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.log_output)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.theme_toggle.setChecked(load_theme())
        self.toggle_dark_mode()

        # Keyboard shortcuts for copy/paste
        self.table.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == event.KeyPress:
            if event.matches(QKeySequence.Copy):
                self.copy_selection()
                return True
            elif event.matches(QKeySequence.Paste):
                self.paste_to_selection()
                return True
        return super().eventFilter(source, event)
    
    def copy_selection(self):
        selection = self.table.selectedRanges()
        if selection:
            text = ""
            for range_ in selection:
                for row in range(range_.topRow(), range_.bottomRow() + 1):
                    row_data = []
                    for col in range(range_.leftColumn(), range_.rightColumn() + 1):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    text += "\t".join(row_data) + "\n"
            QApplication.clipboard().setText(text)

    def paste_to_selection(self):
        start_row = self.table.currentRow()
        start_col = self.table.currentColumn()
        text = QApplication.clipboard().text()
        for i, line in enumerate(text.splitlines()):
            for j, val in enumerate(line.split("\t")):
                row = start_row + i
                col = start_col + j
                if row < self.table.rowCount() and col < self.table.columnCount():
                    old = self.table.item(row, col).text() if self.table.item(row, col) else ""
                    self.undo_stack.append((row, col, old))
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                    self.table.setItem(row, col, item)

    def log_edit(self, item):
        row, col = item.row(), item.column()
        text = item.text()
        old = getattr(item, 'old_text', '')
        self.edit_log.append((row, col, old, text))
        self.undo_stack.append((row, col, old))
        self.log_output.append(f"[{self.user}] Edited (Row {row+1}, Col {col+1}): '{old}' → '{text}'")
        item.old_text = text

    def undo_edit(self):
        if not self.undo_stack:
            return
        row, col, old = self.undo_stack.pop()
        current = self.table.item(row, col).text() if self.table.item(row, col) else ""
        self.redo_stack.append((row, col, current))
        item = QTableWidgetItem(old)
        item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        item.old_text = old
        self.table.blockSignals(True)
        self.table.setItem(row, col, item)
        self.table.blockSignals(False)
        self.log_output.append(f"Undo (Row {row+1}, Col {col+1}): → '{old}'")

    def redo_edit(self):
        if not self.redo_stack:
            return
        row, col, text = self.redo_stack.pop()
        old = self.table.item(row, col).text() if self.table.item(row, col) else ""
        self.undo_stack.append((row, col, old))
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        item.old_text = text
        self.table.blockSignals(True)
        self.table.setItem(row, col, item)
        self.table.blockSignals(False)
        self.log_output.append(f"Redo (Row {row+1}, Col {col+1}): → '{text}'")

    def search_table(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            row_matches = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    row_matches = True

            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if not item:
                    item = QTableWidgetItem("")
                    self.table.setItem(row, col, item)
                item.setBackground(QColor("cyan") if row_matches and text else Qt.white) 

    def toggle_dark_mode(self):
        dark = self.theme_toggle.isChecked()
        save_theme(dark)

        self.theme_toggle.setIcon(QIcon("moon.png") if dark else QIcon("sun.png"))

        if dark:
            self.setStyleSheet("""
            QWidget {
                background-color: #2f3136;
                color: #dcddde;
                font-size: 14px;
            }
            QLineEdit, QTableWidget, QTextEdit {
                background-color: #202225;
                border: 1px solid #444;
                color: #dcddde;
            }
            QHeaderView::section {
                background-color: #2f3136;
                color: #dcddde;
                padding: 4px;
                border: 1px solid #444;
            }
            QTableWidget::item:selected {
                background-color: #3a3c40;
            }
            QPushButton {
                background-color: #40444b;
                color: #dcddde;
                border: 1px solid #444;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4f545c;
            }

            QPushButton#ThemeToggle {
                font-size: 12px;
                padding: 2px;
            }

            QMenu {
                background-color: #2f3136;
                color: #dcddde;
            }
            QScrollBar:vertical {
                background: #2f3136;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #72767d;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                background: none;
            }
            """)
        else:
            self.setStyleSheet("")

    def browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            self.folder_path = path
            self.entry.setText(path)

    def extract_pdfs(self):
        try:
            self.table.itemChanged.disconnect(self.recalculate_totals)
        except:
            pass
            log_action(self.user, "Started PDF Extraction", os.listdir(self.folder_path))
        

        self.table.setRowCount(0)
        folder = self.folder_path or self.entry.text()
        if not os.path.isdir(folder):
            QMessageBox.critical(self, "Error", "Invalid folder path.")
            return

        pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
        if not pdf_files:
            QMessageBox.information(self, "No PDFs", "No PDF files found.")
            return

        self.progress_dialog = QProgressDialog("Extracting PDFs...", None, 0, len(pdf_files), self)
        self.progress_dialog.setWindowTitle("Please Wait")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)

        self.thread = QThread()
        self.worker = ExtractWorker(folder, pdf_files)
        self.worker.moveToThread(self.thread)

        self.worker.progress.connect(lambda i, name: (
            self.progress_dialog.setValue(i),
            self.progress_dialog.setLabelText(f"Processing {name} ({i+1}/{len(pdf_files)})")
        ))
        self.worker.result.connect(self.add_row)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, "Error", msg))
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.progress_dialog.close)
        self.worker.finished.connect(self.update_total_row)
        self.worker.finished.connect(lambda: self.table.itemChanged.connect(self.recalculate_totals))
        self.progress_dialog.canceled.connect(self.worker.cancel)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def add_row(self, data):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col in range(self.table.columnCount()):
            if col < len(data):
                item = QTableWidgetItem(data[col])
            else:
                item = QTableWidgetItem("")
            if col != 0:
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.table.setItem(row, col, item)
        self.table.resizeRowToContents(row)

    def insert_text_and_resize(self, row, col, text):
        self.table.setItem(row, col, QTableWidgetItem(text))
        self.table.resizeRowToContents(row)

    def scan_pdf_to_cell(self, item):
        row, col = item.row(), item.column()
        filename = self.table.item(row, 0).text()
        pdf_path = os.path.join(self.folder_path, filename)
        if not os.path.exists(pdf_path):
            QMessageBox.warning(self, "Error", f"PDF not found: {pdf_path}")
            return
        images = convert_from_path(pdf_path)
        if not images:
            QMessageBox.warning(self, "Error", "Failed to convert PDF.")
            return
        image = images[0]
        viewer = PDFCropViewer(image, lambda text: self.insert_text_and_resize(row, col, text))
        viewer.exec_()

    def open_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item:
            menu = QMenu()
            menu.addAction("Scan PDF to Cell", lambda: self.scan_pdf_to_cell(item))
            menu.exec_(self.table.viewport().mapToGlobal(pos))

    def update_total_row(self):
        self.table.blockSignals(True)
        for row in reversed(range(self.table.rowCount())):
            if self.table.item(row, 0) and self.table.item(row, 0).text() == "TOTAL":
                self.table.removeRow(row)

        total_amount = payment_total = tax_total = balance_total = 0.0
        for row in range(self.table.rowCount()):
            try:
                total_amount += float(self.table.item(row, 5).text().replace(",", "") or 0)
                payment_total += float(self.table.item(row, 6).text().replace(",", "") or 0)
                tax_total += float(self.table.item(row, 7).text().replace(",", "") or 0)
                balance_total += float(self.table.item(row, 8).text().replace(",", "") or 0)
            except:
                continue

        row = self.table.rowCount()
        self.table.insertRow(row)
        totals = ["TOTAL", "", "", "", "", f"{total_amount:,.2f}", f"{payment_total:,.2f}", f"{tax_total:,.2f}", f"{balance_total:,.2f}"]

        for col, value in enumerate(totals):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            item.setToolTip("Summary Total")
            item.setBackground(Qt.lightGray)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, col, item)

        self.table.blockSignals(False)

    def recalculate_totals(self):
        for row in range(self.table.rowCount()):
            item0 = self.table.item(row, 0)
            if item0 and item0.text() == "TOTAL":
                continue
            try:
                total = float(self.table.item(row, 5).text().replace(",", "") or 0)
                payment = float(self.table.item(row, 6).text().replace(",", "") or 0)
                tax = float(self.table.item(row, 7).text().replace(",", "") or 0)
                balance = total - payment - tax
                self.table.blockSignals(True)
                balance_item = QTableWidgetItem(f"{balance:,.2f}")
                balance_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                self.table.setItem(row, 8, balance_item)
                self.table.blockSignals(False)
            except:
                pass
        self.update_total_row()

    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV (*.csv);;Excel (*.xlsx);;PDF (*.pdf)")
        log_action(self.user, f"Exported table as {os.path.splitext(path)[1]}", [path])
        if not path:
            return
        
        data = []
        for row in range(self.table.rowCount()):
            data.append([
                self.table.item(row, col).text() if self.table.item(row, col) else ""
                for col in range(self.table.columnCount())
            ])
        df = pd.DataFrame(data, columns=self.columns)

        if path.endswith(".csv"):
            df.to_csv(path, index=False)
        elif path.endswith(".xlsx"):
            df.to_excel(path, index=False)
        elif path.endswith(".pdf"):
            try:
                from reportlab.lib.pagesizes import letter, landscape
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
                from reportlab.lib import colors 

                pdf = SimpleDocTemplate(path, pagesize=landscape(letter))
                table_data = [self.columns] + data
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                ]))
                pdf.build([table])
            except ImportError:
                QMessageBox.warning(self, "Missing Package", "Please install reportlab:\npip install reportlab")
                return

            QMessageBox.information(self, "Success", f"Saved to {path}")

            # Ask user if they want to open the file
            reply = QMessageBox.question(
                self,
                "Open File?",
                "Do you want to open the file now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                os.startfile(path)


    def open_file(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Error", "No file selected.")
            return
        filename = self.table.item(selected, 0).text()
        full_path = os.path.join(self.folder_path, filename)
        if os.path.exists(full_path):
            os.startfile(full_path)
        else:
            QMessageBox.warning(self, "Error", "File not found.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFExtractor()
    window.show()
    sys.exit(app.exec_())
