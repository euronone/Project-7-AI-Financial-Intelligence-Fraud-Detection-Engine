# FinShield AI - Windows PowerShell Quick Start Guide
# Run this in PowerShell to set up the complete system

# Project Root Directory
$projectRoot = "c:\Users\gsuni\OneDrive\Desktop\AI_Project\Temp\AI-Financial-Intelligence-Fraud-Detection-\AI-Financial-Intelligence-Fraud-Detection-"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FinShield AI - Windows Setup Guide" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host

# ============================================================================
# PREREQUISITE CHECK
# ============================================================================
Write-Host "STEP 0: Checking Prerequisites" -ForegroundColor Blue
Write-Host

Write-Host "Checking Python..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    Write-Host " ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host " ✗ NOT FOUND - Install from https://www.python.org" -ForegroundColor Red
}

Write-Host "Checking Node.js..." -NoNewline
try {
    $nodeVersion = node --version
    Write-Host " ✓ $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host " ✗ NOT FOUND - Install from https://nodejs.org" -ForegroundColor Red
}

Write-Host "Checking npm..." -NoNewline
try {
    $npmVersion = npm --version
    Write-Host " ✓ $npmVersion" -ForegroundColor Green
} catch {
    Write-Host " ✗ NOT FOUND - Install Node.js" -ForegroundColor Red
}

Write-Host "Checking Docker..." -NoNewline
try {
    $dockerVersion = docker --version
    Write-Host " ✓ $dockerVersion" -ForegroundColor Green
    $dockerReady = $true
} catch {
    Write-Host " ✗ NOT INSTALLED (Required for PostgreSQL & Redis)" -ForegroundColor Yellow
    Write-Host "   Download: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    $dockerReady = $false
}

Write-Host

# ============================================================================
# STEP 1: Start Infrastructure Services
# ============================================================================
Write-Host "STEP 1: Starting Infrastructure Services" -ForegroundColor Blue
Write-Host "  - PostgreSQL 16 (Database)" -ForegroundColor Gray
Write-Host "  - Redis 7 (Cache)" -ForegroundColor Gray
Write-Host "  - MailHog (Email)" -ForegroundColor Gray
Write-Host

if ($dockerReady) {
    $response = Read-Host "Start Docker services? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "▶ Starting Docker Compose..." -ForegroundColor Green
        Set-Location $projectRoot
        docker compose up -d
        
        Write-Host "Waiting for services to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        Write-Host "✓ Services started:" -ForegroundColor Green
        docker ps --format "table {{.Names}} `t {{.Status}}"
        Write-Host
    }
} else {
    Write-Host "⚠ Docker not available. Please install Docker Desktop (see prerequisite above)." -ForegroundColor Yellow
    Write-Host
}

# ============================================================================
# STEP 2: Install/Verify Dependencies
# ============================================================================
Write-Host "STEP 2: Verifying Dependencies" -ForegroundColor Blue
Write-Host

Write-Host "Backend dependencies..."
Set-Location "$projectRoot\backend"
if (Test-Path "poetry.lock") {
    Write-Host "✓ Poetry lock file exists - dependencies installed" -ForegroundColor Green
} else {
    Write-Host "Installing Python packages..." -ForegroundColor Yellow
    poetry install --no-root
}

Write-Host
Write-Host "Frontend dependencies..."
Set-Location "$projectRoot\frontend"
if (Test-Path "node_modules") {
    Write-Host "✓ node_modules directory exists - npm packages installed" -ForegroundColor Green
} else {
    Write-Host "Installing npm packages..." -ForegroundColor Yellow
    npm install
}

Write-Host
Write-Host

# ============================================================================
# STEP 3: Database Migration
# ============================================================================
Write-Host "STEP 3: Database Setup & Migration" -ForegroundColor Blue
Write-Host

$dbResponse = Read-Host "Run database migrations and seed data? (y/n)"
if ($dbResponse -eq 'y' -or $dbResponse -eq 'Y') {
    Set-Location "$projectRoot\backend"
    
    Write-Host "▶ Running Alembic migrations..." -ForegroundColor Green
    poetry run alembic upgrade head
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Migrations complete" -ForegroundColor Green
    }
    
    Write-Host
    Write-Host "▶ Seeding test data..." -ForegroundColor Green
    poetry run python scripts/seed_data.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Database ready with test data" -ForegroundColor Green
    }
    
    Write-Host
}

# ============================================================================
# STEP 4: Start Servers
# ============================================================================
Write-Host
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Ready to Start Servers" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host

Write-Host "STEP 4A: Start Backend Server" -ForegroundColor Blue
Write-Host "  URL: http://localhost:8000" -ForegroundColor Gray
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host

Write-Host "Run this in a NEW PowerShell window:" -ForegroundColor Yellow
Write-Host @"
    `$projectRoot = "$projectRoot"
    Set-Location `$projectRoot\backend
    poetry run uvicorn app.main:app --reload --port 8000
"@ -ForegroundColor Cyan
Write-Host

Write-Host "STEP 4B: Start Frontend Server" -ForegroundColor Blue
Write-Host "  URL: http://localhost:3000" -ForegroundColor Gray
Write-Host

Write-Host "Run this in ANOTHER NEW PowerShell window:" -ForegroundColor Yellow
Write-Host @"
    `$projectRoot = "$projectRoot"
    Set-Location `$projectRoot\frontend
    npm run dev
"@ -ForegroundColor Cyan

Write-Host
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Login Credentials" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host

Write-Host "Email:    " -NoNewline
Write-Host "admin@finshield.dev" -ForegroundColor Green
Write-Host "Password: " -NoNewline
Write-Host "Admin123!@#" -ForegroundColor Green

Write-Host
Write-Host

# ============================================================================
# AUTOMATED START (Optional)
# ============================================================================
$autoStart = Read-Host "Would you like to start the backend server now? (y/n)"
if ($autoStart -eq 'y' -or $autoStart -eq 'Y') {
    Set-Location "$projectRoot\backend"
    Write-Host "▶ Starting Backend Server..." -ForegroundColor Green
    Write-Host "  (Keep this window open while working)" -ForegroundColor Yellow
    Write-Host
    poetry run uvicorn app.main:app --reload --port 8000
}

Write-Host
Write-Host "Setup complete! Open another PowerShell window and run:" -ForegroundColor Green
Write-Host
Write-Host "setx PROJECT_ROOT `"$projectRoot`"" -ForegroundColor Cyan
Write-Host "cd `$env:PROJECT_ROOT\frontend" -ForegroundColor Cyan
Write-Host "npm run dev" -ForegroundColor Cyan
Write-Host
Write-Host "Then open http://localhost:3000 in your browser" -ForegroundColor Green
