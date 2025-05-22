# Docker Deployment for Simulation Tool
# PowerShell version

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Docker Deployment for Simulation Tool" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker installation
try {
    $dockerVersion = docker --version
    Write-Host "Found $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Please select an option:" -ForegroundColor Cyan
Write-Host "1. Build and run container" -ForegroundColor White
Write-Host "2. Stop running container" -ForegroundColor White
Write-Host "3. Remove container and images" -ForegroundColor White
Write-Host ""
$dockerOption = Read-Host "Enter your choice (1-3)"

switch ($dockerOption) {
    "1" {
        Write-Host ""
        Write-Host "Building and running Docker container..." -ForegroundColor Yellow
        docker-compose up --build -d
        
        Write-Host ""
        Write-Host "Container is now running!" -ForegroundColor Green
        Write-Host "Open your browser and go to: http://localhost:8501" -ForegroundColor Cyan
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    "2" {
        Write-Host ""
        Write-Host "Stopping Docker container..." -ForegroundColor Yellow
        docker-compose down
        
        Write-Host ""
        Write-Host "Container stopped." -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    "3" {
        Write-Host ""
        Write-Host "Removing container and images..." -ForegroundColor Yellow
        docker-compose down --rmi all
        
        Write-Host ""
        Write-Host "Cleanup complete." -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    default {
        Write-Host "Invalid option selected." -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
}
