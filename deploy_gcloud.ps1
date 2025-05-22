# Google Cloud Run Deployment
# PowerShell version

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Google Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check Google Cloud CLI installation
try {
    $gcloudVersion = gcloud --version
    Write-Host "Google Cloud CLI detected" -ForegroundColor Green
} catch {
    Write-Host "Google Cloud CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Login to Google Cloud
Write-Host "Authenticating with Google Cloud..." -ForegroundColor Yellow
gcloud auth login

# Set deployment parameters
$projectId = Read-Host "Enter your Google Cloud project ID"
$region = Read-Host "Enter region (e.g., us-central1)"
$serviceName = Read-Host "Enter service name (e.g., demographic-simulation)"

# Set the project
gcloud config set project $projectId

# Build and push the Docker image to Google Container Registry
Write-Host "Building and pushing Docker image..." -ForegroundColor Yellow
gcloud builds submit --tag gcr.io/$projectId/$serviceName

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $serviceName `
  --image gcr.io/$projectId/$serviceName `
  --platform managed `
  --region $region `
  --allow-unauthenticated `
  --port 8501

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Your app will be available at the URL shown above" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue"
