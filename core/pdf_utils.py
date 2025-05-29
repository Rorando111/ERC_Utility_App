import os
import urllib.parse
from PyPDF2 import PdfReader, PdfWriter
from openpyxl import load_workbook
from openpyxl.styles import Font
from PyQt5.QtWidgets import QMessageBox

def sanitize_filename(filename):
    return "".join(c if c.isalnum() or c in ("-", "_") else "" for c in filename).lstrip("_")

def show_error(message, title="Error"):
    QMessageBox.critical(None, title, message)

def show_warning(message, title="Warning"):
    QMessageBox.warning(None, title, message)

def show_info(message, title="Info"):
    QMessageBox.information(None, title, message)

def split_pdf(input_pdf, output_folder, output_widget, progress_bar=None):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        reader = PdfReader(input_pdf)
        total_pages = len(reader.pages)
        if progress_bar:
            progress_bar.setMaximum(total_pages)
            progress_bar.setValue(0)
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            output_path = os.path.join(output_folder, f"page_{i+1}.pdf")
            with open(output_path, "wb") as output_pdf:
                writer.write(output_pdf)
            output_widget.append(f"Saved: {output_path}")
            if progress_bar:
                progress_bar.setValue(i + 1)
    except Exception as e:
        output_widget.append(f"Error splitting PDF: {e}")
