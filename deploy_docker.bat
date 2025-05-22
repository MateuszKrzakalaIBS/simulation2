@echo off
ECHO ====================================
ECHO Docker Deployment for Simulation Tool
ECHO ====================================
ECHO.

:: Check Docker installation
docker --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Docker is not installed or not in PATH.
    ECHO Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
    ECHO.
    PAUSE
    EXIT /B 1
)

ECHO Please select an option:
ECHO 1. Build and run container
ECHO 2. Stop running container
ECHO 3. Remove container and images
ECHO.
SET /P DOCKER_OPTION="Enter your choice (1-3): "

IF "%DOCKER_OPTION%"=="1" (
    ECHO.
    ECHO Building and running Docker container...
    docker-compose up --build -d
    
    ECHO.
    ECHO Container is now running!
    ECHO Open your browser and go to: http://localhost:8501
    ECHO.
    PAUSE
) ELSE IF "%DOCKER_OPTION%"=="2" (
    ECHO.
    ECHO Stopping Docker container...
    docker-compose down
    
    ECHO.
    ECHO Container stopped.
    ECHO.
    PAUSE
) ELSE IF "%DOCKER_OPTION%"=="3" (
    ECHO.
    ECHO Removing container and images...
    docker-compose down --rmi all
    
    ECHO.
    ECHO Cleanup complete.
    ECHO.
    PAUSE
) ELSE (
    ECHO Invalid option selected.
    ECHO.
    PAUSE
)
