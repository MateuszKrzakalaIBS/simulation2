# Digital Ocean App Platform Deployment
# PowerShell version

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Digital Ocean Deployment" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check Digital Ocean CLI installation
try {
    $doVersion = doctl version
    Write-Host "Digital Ocean CLI detected" -ForegroundColor Green
} catch {
    Write-Host "Digital Ocean CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "https://docs.digitalocean.com/reference/doctl/how-to/install/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Login to Digital Ocean
Write-Host "Authenticating with Digital Ocean..." -ForegroundColor Yellow
doctl auth init

# Set deployment parameters
$appName = Read-Host "Enter app name (e.g., demographic-simulation)"
$dockerImage = Read-Host "Enter Docker image (e.g., username/demographic-simulation:latest)"

# Create app spec
$appSpec = @"
name: $appName
region: fra
services:
- name: web
  github:
    repo: your-username/demographic-simulation
    branch: main
  dockerfile_path: Dockerfile
  http_port: 8501
  instance_size_slug: basic-s
  instance_count: 1
  routes:
  - path: /
"@

# Save app spec to file
$appSpec | Out-File -FilePath "app.yaml" -Encoding utf8

# Create and deploy app
Write-Host "Creating and deploying app to Digital Ocean..." -ForegroundColor Yellow
doctl apps create --spec app.yaml

Write-Host ""
Write-Host "Deployment initiated!" -ForegroundColor Green
Write-Host "Check the status and URL in your Digital Ocean dashboard" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue"
