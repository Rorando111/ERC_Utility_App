import os
import pdf2image
import pytesseract
from .pdf_utils import sanitize_filename, show_error
from PyQt5.QtWidgets import QMessageBox

def extract_and_rename_pdfs(folder_path, output_widget, progress_bar=None):
    if not os.path.isdir(folder_path):
        show_error("Invalid folder path.")
        return

    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    if not pdf_files:
        output_widget.append("No PDF files found in the selected folder.\n")
        return

    total = len(pdf_files)
    if progress_bar:
        progress_bar.setMaximum(total)
        progress_bar.setValue(0)

    for count, filename in enumerate(pdf_files, start=1):
        pdf_path = os.path.join(folder_path, filename)
        try:
            images = pdf2image.convert_from_path(pdf_path)
        except Exception as e:
            output_widget.append(f"Failed to convert {filename}: {e}")
            continue

        serial_number = None
        for image in images:
            text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
            for line in text.split('\n'):
                if 'Serial No.' in line:
                    serial_number = sanitize_filename(line.split('Serial No.')[-1].strip())
                    break
            if serial_number:
                break

        if serial_number:
            new_filename = f"{serial_number}.pdf"
            new_path = os.path.join(folder_path, new_filename)
            if not os.path.exists(new_path):
                try:
                    os.rename(pdf_path, new_path)
                    output_widget.append(f"Renamed: {filename} -> {new_filename}")
                except Exception as e:
                    output_widget.append(f"Error renaming {filename}: {e}")
            else:
                output_widget.append(f"Skipped: {new_filename} already exists.")
        else:
            output_widget.append(f"Serial number not found in {filename}")

        if progress_bar:
            progress_bar.setValue(count)
