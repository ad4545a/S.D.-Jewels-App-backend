# fix_email_hardcoded.ps1

# === UPDATE THESE VALUES ===
$Email = "ad4545a@gmail.com"
# PASTE YOUR 16-CHAR PASSWORD INSIDE THE QUOTES BELOW (REMOVE SPACES IF ANY)
$Password = "snjmsnkfxkyasqyj" 
$Receiver = "aditya96verma1@gmail.com"
# ===========================

$VPS_IP = "117.252.16.130"
$VPS_USER = "root"
$REMOTE_DIR = "/root/backend"

Write-Host "Repairing Email Config using hardcoded values..." -ForegroundColor Cyan

# 1. Download existing .env
scp -o StrictHostKeyChecking=no "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/.env" "$PSScriptRoot\.env.tmp"

# 2. Clean and Rewrite
$envContent = Get-Content "$PSScriptRoot\.env.tmp"
$cleanContent = @()

foreach ($line in $envContent) {
    if ($line -notmatch "^SMTP_") {
        $cleanContent += $line
    }
}

# Remove spaces from password just in case
$CleanPassword = $Password -replace " ", ""

$cleanContent += "SMTP_EMAIL=$Email"
$cleanContent += "SMTP_PASSWORD=$CleanPassword"
$cleanContent += "SMTP_RECEIVER=$Receiver"

$cleanContent | Set-Content "$PSScriptRoot\.env.new"

# 3. Upload
Write-Host "Uploading fixed config... (Password required)" -ForegroundColor Yellow
scp -o StrictHostKeyChecking=no "$PSScriptRoot\.env.new" "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/.env"

# 4. Cleanup
Remove-Item "$PSScriptRoot\.env.tmp"
Remove-Item "$PSScriptRoot\.env.new"

# 5. Restart
Write-Host "Restarting Service... (Password required)" -ForegroundColor Yellow
ssh -t "${VPS_USER}@${VPS_IP}" "systemctl restart market_monitor"

Write-Host "Done! Please try testing now." -ForegroundColor Green
