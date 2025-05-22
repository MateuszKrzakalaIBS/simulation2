# AWS Elastic Beanstalk Deployment
# PowerShell version

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "AWS Elastic Beanstalk Deployment" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI installation
try {
    $awsVersion = aws --version
    Write-Host "AWS CLI detected" -ForegroundColor Green
} catch {
    Write-Host "AWS CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "https://aws.amazon.com/cli/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check EB CLI installation
try {
    $ebVersion = eb --version
    Write-Host "EB CLI detected" -ForegroundColor Green
} catch {
    Write-Host "EB CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "pip install awsebcli" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Initialize EB application
Write-Host "Initializing Elastic Beanstalk application..." -ForegroundColor Yellow
eb init

# Create necessary configuration files
Write-Host "Creating configuration files..." -ForegroundColor Yellow

# Create .ebextensions directory if it doesn't exist
New-Item -ItemType Directory -Force -Path ".ebextensions" | Out-Null

# Create environment configuration file
@"
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: web/interactive_app.py
  aws:elasticbeanstalk:application:environment:
    STREAMLIT_SERVER_ENABLE_STATIC_SERVING: true
    STREAMLIT_SERVER_FILE_WATCHER_TYPE: none
    PYTHONPATH: /var/app
"@ | Out-File -FilePath ".ebextensions/01_environment.config" -Encoding utf8

# Create Procfile
@"
web: streamlit run web/interactive_app.py --server.port=8080 --server.address=0.0.0.0
"@ | Out-File -FilePath "Procfile" -Encoding utf8

# Create and deploy
Write-Host "Creating and deploying to Elastic Beanstalk..." -ForegroundColor Yellow
eb create

Write-Host ""
Write-Host "Deployment initiated!" -ForegroundColor Green
Write-Host "Your app will be available at the URL shown above" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue"
