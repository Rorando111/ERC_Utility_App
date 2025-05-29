# ERC PDF Utility Tool

A multifunctional PyQt5-based desktop application to streamline and automate PDF-related document processing tasks for the Energy Regulatory Commission's Financial Administrative Services - Budget Division.

Libraries and Dependencies installed:
- Poppler
- Pytesseract

Tasks to remember before using the app:

Before using the app, "tesseract-ocr.exe" must be installed first

When opening the app (this is for every use of the app), before using any of the app's features, click the tesseract icon to manually set the paths of tesseract and poppler.
If the user have an administrative access, you can add the path of Tesseract and Poppler to the Environment Variables
- To do this: (You can skip the first 5 steps by just searching "Edit the System Environment Variables" on your device)
  - Go to the Control Panel
  - Click "System and Security"
  - Click "System"
  - Under the "Related Links", click "Advanced system settings"
  - On the System Properties Dialog Box, click "Environment Variables..."
  - On the Environment Variables Dialog Box, under the System Variables, click "Edit..."
  - On the Edit environment variable Dialog Box, click "New" then paste the link for Tesseract
  - Click "New" again to add another path for poppler.
After doing this, you don't have to manually set the paths for poppler and tesseract and can directly use all the app's features every time, even when reopening.

Examples of Tesseract and Poppler Paths:
- Poppler: C:\Program Files\poppler-24.08.0\Library\bin
- Tesseract: C:\Program Files\Tesseract-OCR
- 
---

## 🚀 Features

### 📂 File Management
- **Extract & Rename of OBR, NCA, and SARO PDFs by batch** based on content (e.g., OBR No., NCA No., SARO No.)
- **Split PDF** into individual pages

### 🧾 OBR Extractor
- OCR-based data extraction from PDF forms
- Intelligent parsing of Payee, Date, Particulars, Amount
- Table editing with:
  - Cell-level editing
  - Undo/Redo
  - Copy/Paste
  - Inline audit logs
- Manual OCR region scan per cell (crop & extract)
- Save to CSV, Excel, and PDF
- Smart summary row calculation

### 🏢 SharePoint Integration
- Authenticate to a SharePoint site
- Extract PDF links from folders
- Export result as a hyperlinked Excel file

### 🎨 Theme Support
- 🌗 Dark/Light mode toggle
- Theme preference is saved between sessions

### Activity Logs
- Logs all the activity done by the user during runtime
- Logs can be exported into a CSV file

---

## 📁 Project Structure
```
erc-pdfut/
│
├── main.py
├── build.ps1
├── icon.ico
├── sun.ico
├── moon.ico
├── erc.ico
├── tesseract.ico
├── README.md
├── obr_extractor.py
├── tesseract-ocr-w64-setup-5.5.0.20241111.exe
│
├── core/
│   ├── file_utils.py
│   ├── pdf_utils.py
│   ├── budget_utils.py
│   └── sharepoint_utils.py
│   └── email_utils.py
│   └── logger.py
│   └── ocr_config.py
│   └── pdf_tools.py
│   └── sharepoint_tools.py
│   └── user_auth.py
│
├── config/
│   ├── constants.py
│   └── theme_config.py
|   ├── theme_config.json
│
├── ui_pages/
|   ├── main_window.py
|   ├── main_menu.py
|   ├── rename_page.py
|   ├── obr_page.py
|   ├── split_page.py
|   ├── sharepoint_page.py
|   ├── activity_log_page.py
|   ├── login_page.py
|   ├── merge_page.py
|   ├── nca_fallback_dialog.py
|   ├── obr_fallback_dialog.py
|   ├── path_settings_page.py
|   ├── rename_option_dialog.py
|   ├── saro_fallback_dialog.py
|   ├── signup_dialog.py
|   ├── two_factor_dialog.py
|
├── poppler-24.08.0
├── utils/
|   ├── dialogs.py
|   ├── helpers.py
|   ├── image_utils.py

```x`

---

## 🤝 Developers:
- Engr. Rolando Celeste - celeste.landon667@gmail.com
- Engr. Cris John Perez - perezcj2003@gmail.com

