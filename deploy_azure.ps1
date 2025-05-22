# Azure Deployment Script for Demographic Simulation Tool
# PowerShell version

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Azure App Service Deployment" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check Azure CLI installation
try {
    $azureVersion = az --version
    Write-Host "Azure CLI detected" -ForegroundColor Green
} catch {
    Write-Host "Azure CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Login to Azure
Write-Host "Logging in to Azure..." -ForegroundColor Yellow
az login

# Set deployment parameters
$resourceGroup = Read-Host "Enter resource group name"
$location = Read-Host "Enter location (e.g., westeurope)"
$appName = Read-Host "Enter app name"

# Create resource group if it doesn't exist
Write-Host "Creating resource group if it doesn't exist..." -ForegroundColor Yellow
az group create --name $resourceGroup --location $location

# Create App Service plan
Write-Host "Creating App Service plan..." -ForegroundColor Yellow
az appservice plan create --name "${appName}-plan" --resource-group $resourceGroup --sku B1 --is-linux

# Create web app
Write-Host "Creating web app..." -ForegroundColor Yellow
az webapp create --name $appName --resource-group $resourceGroup --plan "${appName}-plan" --runtime "PYTHON:3.9"

# Configure web app
Write-Host "Configuring web app..." -ForegroundColor Yellow
az webapp config set --name $appName --resource-group $resourceGroup --startup-file "startup.sh"

# Add application settings
Write-Host "Adding application settings..." -ForegroundColor Yellow
az webapp config appsettings set --name $appName --resource-group $resourceGroup --settings STREAMLIT_SERVER_ENABLE_STATIC_SERVING=true STREAMLIT_SERVER_FILE_WATCHER_TYPE=none

# Deploy code
Write-Host "Deploying code to Azure..." -ForegroundColor Yellow
az webapp up --name $appName --resource-group $resourceGroup --sku B1 --location $location

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Your app is available at: https://${appName}.azurewebsites.net" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue"
