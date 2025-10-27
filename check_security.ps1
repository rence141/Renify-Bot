# Renify Bot Security Check Script
# Run this before committing to Git!

Write-Host "=== Renify Bot Security Check ===" -ForegroundColor Cyan
Write-Host ""

# Check for .env file
if (Test-Path ".env") {
    Write-Host "✓ .env file exists" -ForegroundColor Green
} else {
    Write-Host "✗ .env file NOT found" -ForegroundColor Yellow
    Write-Host "  Create one from env.example!" -ForegroundColor Yellow
}

# Check if .env would be committed
Write-Host ""
Write-Host "Checking if sensitive files are in Git..." -ForegroundColor Cyan

$sensitiveFiles = @(".env", "*.log", "renify_bot.log", "*token*.txt", "*secret*.txt")
$found = $false

foreach ($file in $sensitiveFiles) {
    $matches = Get-ChildItem -Path . -Filter $file -Force -ErrorAction SilentlyContinue
    if ($matches) {
        foreach ($match in $matches) {
            $gitStatus = git check-ignore $match.FullName 2>$null
            if (-not $gitStatus) {
                Write-Host "⚠ WARNING: $($match.Name) is NOT in .gitignore!" -ForegroundColor Red
                $found = $true
            } else {
                Write-Host "✓ $($match.Name) is properly ignored" -ForegroundColor Green
            }
        }
    }
}

Write-Host ""
if ($found) {
    Write-Host "❌ ISSUES FOUND! Do not commit!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Run: git status" -ForegroundColor Yellow
} else {
    Write-Host "✓ All sensitive files are protected!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Safe to commit!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Checking for hardcoded tokens in Python files..." -ForegroundColor Cyan

$pythonFiles = Get-ChildItem -Path . -Filter "*.py" -Recurse -ErrorAction SilentlyContinue
foreach ($file in $pythonFiles) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($content -match "YOUR_BOT_TOKEN_HERE|YOUR_TOKEN|sk_live_|pk_live_" -and $content -notmatch "YOUR_BOT_TOKEN_HERE") {
        Write-Host "⚠ WARNING: Potential hardcoded token in $($file.Name)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Check Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review git status: git status" -ForegroundColor White
Write-Host "2. Check what will be committed: git diff" -ForegroundColor White
Write-Host "3. Only commit safe files!" -ForegroundColor White

