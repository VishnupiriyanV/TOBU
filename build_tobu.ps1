
Write-Host " Starting TOBU Build Process..." -ForegroundColor Cyan

$ProjectRoot = Get-Location
$ClientDir = Join-Path $ProjectRoot "client"
$DesktopDir = Join-Path $ProjectRoot "desktop"
$DistDir = Join-Path $ProjectRoot "dist"
$DesktopUIDir = Join-Path $DesktopDir "ui"

Write-Host "`n Building React Frontend..." -ForegroundColor Yellow
Set-Location $ClientDir
npm install
npm run build
if ($LASTEXITCODE -ne 0) { Write-Error "Frontend build failed"; exit 1 }

# 2. Sync UI to Desktop
Write-Host "`n Syncing UI to Electron shell..." -ForegroundColor Yellow
if (Test-Path $DesktopUIDir) { Remove-Item -Recurse -Force $DesktopUIDir }
New-Item -ItemType Directory -Path $DesktopUIDir
Copy-Item -Recurse (Join-Path $ClientDir "dist\*") $DesktopUIDir
Write-Host "UI files synced."

# 3. Build Backend Engine
Write-Host "`n: Building Python Backend Engine..." -ForegroundColor Yellow
Set-Location $ProjectRoot
python scripts/build_backend.py
if ($LASTEXITCODE -ne 0) { Write-Error "Backend build failed"; exit 1 }

# 4. Package Desktop App
Write-Host "`n Packaging Desktop Application..." -ForegroundColor Yellow
Set-Location $DesktopDir
npm install
npm run dist
if ($LASTEXITCODE -ne 0) { Write-Error "Desktop packaging failed"; exit 1 }

Set-Location $ProjectRoot
Write-Host "`n Build Complete! Check the 'desktop/release' folder for the installer." -ForegroundColor Green
