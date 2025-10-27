# Renify Bot Startup Script
# This will start both Lavalink and the bot

Write-Host "=== Starting Renify Music Bot ===" -ForegroundColor Cyan
Write-Host ""

# Load environment variables from .env file
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host "✓ Environment variables loaded" -ForegroundColor Green
} else {
    Write-Host "✗ .env file not found!" -ForegroundColor Red
    Write-Host "Create .env file with your Discord token" -ForegroundColor Yellow
    exit
}

# Check if Lavalink is running
Write-Host ""
Write-Host "Checking if Lavalink is running..." -ForegroundColor Cyan

$lavalinkRunning = Test-NetConnection -ComputerName localhost -Port 2333 -InformationLevel Quiet -WarningAction SilentlyContinue

if (-not $lavalinkRunning) {
    Write-Host "⚠ Lavalink is NOT running!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Starting Lavalink..." -ForegroundColor Cyan
    
    # Start Lavalink in background
    Start-Process -FilePath "java" -ArgumentList "-jar", "renify_lavalink\Lavalink.jar" -WorkingDirectory "renify_lavalink" -WindowStyle Minimized
    
    Write-Host "Waiting for Lavalink to start (30 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    $lavalinkRunning = Test-NetConnection -ComputerName localhost -Port 2333 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($lavalinkRunning) {
        Write-Host "✓ Lavalink started successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Lavalink failed to start" -ForegroundColor Red
        Write-Host "Please start it manually in a separate terminal:" -ForegroundColor Yellow
        Write-Host "  cd renify_lavalink" -ForegroundColor White
        Write-Host "  java -jar Lavalink.jar" -ForegroundColor White
        Write-Host ""
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne 'y') { exit }
    }
} else {
    Write-Host "✓ Lavalink is already running" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Starting Renify Bot ===" -ForegroundColor Cyan
Write-Host ""

# Start the bot
python renify_core.py

