# Demographic Simulation Tool Launcher
# PowerShell version

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Demographic Simulation Tool Launcher" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
try {
    $pythonVersion = python --version
    Write-Host "Found $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install or update dependencies
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check launch option
Write-Host ""
Write-Host "Please select which application to launch:" -ForegroundColor Cyan
Write-Host "1. Standard Web Interface" -ForegroundColor White
Write-Host "2. Interactive Dashboard (Recommended)" -ForegroundColor Green
Write-Host "3. Download External Data" -ForegroundColor Yellow
Write-Host ""
$launchOption = Read-Host "Enter your choice (1-3)"

switch ($launchOption) {
    "1" {
        Write-Host ""
        Write-Host "Launching standard web interface..." -ForegroundColor Cyan
        Set-Location -Path "web"
        python -m streamlit run app.py
    }
    "2" {
        Write-Host ""
        Write-Host "Launching interactive dashboard..." -ForegroundColor Green
        Set-Location -Path "web"
        python -m streamlit run interactive_app.py
    }
    "3" {
        Write-Host ""
        Write-Host "====================================" -ForegroundColor Yellow
        Write-Host "External Data Download" -ForegroundColor Yellow
        Write-Host "====================================" -ForegroundColor Yellow
        Write-Host ""
        
        $country = Read-Host "Enter country code (default: PL)"
        if ([string]::IsNullOrEmpty($country)) { $country = "PL" }
        
        $year = Read-Host "Enter year (default: 2022)"
        if ([string]::IsNullOrEmpty($year)) { $year = 2022 }
        
        $output = Read-Host "Enter output filename (default: External_Input.xlsx)"
        if ([string]::IsNullOrEmpty($output)) { $output = "External_Input.xlsx" }
        
        Write-Host ""
        Write-Host "Downloading data for country=$country, year=$year..." -ForegroundColor Yellow
        python external_data_integration.py --country $country --year $year --output $output
        
        Write-Host ""
        Write-Host "Press any key to return to the main menu..." -ForegroundColor Cyan
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        & $PSCommandPath
    }
    default {
        Write-Host "Invalid option selected." -ForegroundColor Red
        Write-Host ""
        Write-Host "Press any key to try again..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        & $PSCommandPath
    }
}

# Deactivate virtual environment when app closes
deactivate
