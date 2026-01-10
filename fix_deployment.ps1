# fix_deployment.ps1
$VPS_IP = "117.252.16.130"
$VPS_USER = "root"
$REMOTE_DIR = "/root/backend"

Write-Host "Diagnosing Configuration..." -ForegroundColor Cyan

# 1. Find the Firebase JSON file
$jsonFile = Get-ChildItem -Path "$PSScriptRoot" -Filter "*firebase*.json" | Select-Object -First 1

if ($null -eq $jsonFile) {
    Write-Error "Could not find a Firebase JSON file (e.g., *firebase*.json) in the current directory."
    exit
}

Write-Host "Found Firebase Key: $($jsonFile.Name)" -ForegroundColor Green

# 2. Read local .env
$envContent = Get-Content "$PSScriptRoot\.env"
$newEnvLines = @()
$foundKey = $false

foreach ($line in $envContent) {
    if ($line -match "^FIREBASE_KEY_PATH=") {
        # Replace the path with just the filename for Linux
        $newEnvLines += "FIREBASE_KEY_PATH=$($jsonFile.Name)"
        $foundKey = $true
    }
    else {
        $newEnvLines += $line
    }
}

if (-not $foundKey) {
    Write-Host "FIREBASE_KEY_PATH was missing. Adding it." -ForegroundColor Yellow
    $newEnvLines += "FIREBASE_KEY_PATH=$($jsonFile.Name)"
}

# 3. Save as temp file
$tempEnv = "$PSScriptRoot\production.env"
$newEnvLines | Set-Content $tempEnv
Write-Host "Created patched .env file for Linux." -ForegroundColor Green

# 4. Upload and Restart
Write-Host "Uploading new configuration... (Password required)" -ForegroundColor Yellow
scp -o StrictHostKeyChecking=no "$tempEnv" "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/.env"

Write-Host "Restarting Service... (Password required)" -ForegroundColor Yellow
ssh -t "${VPS_USER}@${VPS_IP}" "systemctl restart market_monitor"

# 5. Cleanup
Remove-Item $tempEnv

Write-Host "Fix applied! Please wait 10 seconds effectively, then check logs." -ForegroundColor Green
Write-Host "You can use: .\check_vps_logs.ps1"
