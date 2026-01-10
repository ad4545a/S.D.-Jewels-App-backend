# setup_email.ps1
$VPS_IP = "117.252.16.130"
$VPS_USER = "root"
$REMOTE_DIR = "/root/backend"

Write-Host "Set up (and Repair) Email Notifications" -ForegroundColor Cyan
Write-Host "Get App Password here: https://myaccount.google.com/apppasswords" -ForegroundColor Gray

$Email = Read-Host "Enter Sender Email (e.g. ad4545a@gmail.com)"
$Password = Read-Host "Enter App Password (16 characters)"
$Receiver = Read-Host "Enter Receiver Email (Press Enter to use Sender)"

if ([string]::IsNullOrWhiteSpace($Receiver)) {
    $Receiver = $Email
}

# 1. Download existing .env to preserve API keys
Write-Host "Downloading current config... (Password required)" -ForegroundColor Yellow
scp -o StrictHostKeyChecking=no "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/.env" "$PSScriptRoot\.env.tmp"

if (-not (Test-Path "$PSScriptRoot\.env.tmp")) {
    Write-Error "Failed to download configuration. Check connection."
    exit
}

# 2. Clean old SMTP settings and Append new ones
$envContent = Get-Content "$PSScriptRoot\.env.tmp"
$cleanContent = @()

foreach ($line in $envContent) {
    if ($line -notmatch "^SMTP_") {
        $cleanContent += $line
    }
}

$cleanContent += "SMTP_EMAIL=$Email"
$cleanContent += "SMTP_PASSWORD=$Password"
$cleanContent += "SMTP_RECEIVER=$Receiver"

$cleanContent | Set-Content "$PSScriptRoot\.env.new"

# 3. Upload back
Write-Host "Uploading repaired config... (Password required)" -ForegroundColor Yellow
scp -o StrictHostKeyChecking=no "$PSScriptRoot\.env.new" "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/.env"

# 4. Cleanup temp files
Remove-Item "$PSScriptRoot\.env.tmp"
Remove-Item "$PSScriptRoot\.env.new"

# 5. Restart
Write-Host "Restarting Service... (Password required)" -ForegroundColor Yellow
ssh -t "${VPS_USER}@${VPS_IP}" "systemctl restart market_monitor"

Write-Host "Email Configured Successfully!" -ForegroundColor Green
