# ================================
# === Build Script for PyInstaller ===
# ================================

# Load OCR paths from config
$configPath = Join-Path $PSScriptRoot "ocr_config.json"
if (!(Test-Path $configPath)) {
    Write-Host "❌ OCR config not found at $configPath" -ForegroundColor Red
    Write-Host "Please configure OCR paths first using the application settings." -ForegroundColor Yellow
    exit 1
}

try {
    $config = Get-Content $configPath | ConvertFrom-Json
    $popplerPath = $config.poppler_path
    $tesseractPath = $config.tesseract_path

    if (!$popplerPath -or !$tesseractPath) {
        Write-Host "❌ Invalid OCR configuration: Missing paths" -ForegroundColor Red
        Write-Host "Please configure both Poppler and Tesseract paths in the application settings." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Error reading OCR configuration: $_" -ForegroundColor Red
    Write-Host "Please ensure ocr_config.json is properly formatted." -ForegroundColor Yellow
    exit 1
}

# Check if paths exist
if (!(Test-Path $popplerPath)) {
    Write-Host "❌ Poppler not found at $popplerPath" -ForegroundColor Red
    Write-Host "Please verify the Poppler path in application settings." -ForegroundColor Yellow
    exit 1
}

if (!(Test-Path $tesseractPath)) {
    Write-Host "❌ Tesseract not found at $tesseractPath" -ForegroundColor Red
    Write-Host "Please verify the Tesseract path in application settings." -ForegroundColor Yellow
    exit 1
}

Write-Host "✔ OCR paths verified" -ForegroundColor Green

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
    .venv\Scripts\Activate.ps1
}

# Install/Update dependencies
Write-Host "📦 Installing/Updating dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Clean previous build artifacts
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force dist }
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "*.spec") { Remove-Item -Force *.spec }

# Collect all icon files
$iconFiles = Get-ChildItem -Path $PSScriptRoot -Filter "*.ico" | ForEach-Object { $_.FullName }
Write-Host "🎨 Found icon files:" -ForegroundColor Green
$iconFiles | ForEach-Object { Write-Host "  - $_" }

# Build with PyInstaller
Write-Host "🚀 Building executable..." -ForegroundColor Green
python -m PyInstaller --name "ERC PDF Utility Tool" --onefile --windowed --icon=erc.ico `
    --hidden-import=pytesseract `
    --hidden-import=pdf2image `
    --hidden-import=PyQt5.QtWidgets `
    --hidden-import=PyQt5.QtGui `
    --hidden-import=PyQt5.QtCore `
    --hidden-import=office365.runtime.auth.authentication_context `
    --hidden-import=office365.sharepoint.client_context `
    --hidden-import=PIL `
    --hidden-import=openpyxl `
    --hidden-import=json `
    --hidden-import=csv `
    --add-data "$popplerPath;poppler_bin" `
    --add-data "$tesseractPath;tesseract" `
    --add-data "config;config" `
    --add-data "*.ico;." `
    --add-data "*.json;." `
    main.py

# Copy configuration files and icons to dist
Write-Host "📄 Copying configuration files and icons..." -ForegroundColor Yellow
Copy-Item "theme_config.json" -Destination "dist"
Copy-Item "ocr_config.json" -Destination "dist"
foreach ($icon in $iconFiles) {
    Copy-Item $icon -Destination "dist"
}

Write-Host "✅ Build complete! Executable is in the dist folder." -ForegroundColor Green
