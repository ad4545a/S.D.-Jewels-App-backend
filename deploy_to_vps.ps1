# deploy_to_vps.ps1
# Automates the deployment from Windows to VPS

$VPS_IP = "117.252.16.130"
$VPS_USER = "root" # Assuming root, change if different
$REMOTE_DIR = "/root/backend"

Write-Host "Starting Deployment to $VPS_IP..." -ForegroundColor Cyan

# 1. Check for SSH/SCP availability
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Error "SSH is not installed or not in PATH. Please install OpenSSH Client."
    exit
}

# 2. Upload Files
Write-Host "Step 1: Uploading files... (You will be asked for password)" -ForegroundColor Yellow
# We exclude .venv and __pycache__ to save bandwidth
scp -r -p `
    -o StrictHostKeyChecking=no `
    "$PSScriptRoot\*" `
    "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Upload failed. Please check your password and connection."
    exit
}

# 3. Execute Remote Script
Write-Host "Step 2: Running Setup on VPS... (You will be asked for password again)" -ForegroundColor Yellow
ssh -t "${VPS_USER}@${VPS_IP}" "chmod +x ${REMOTE_DIR}/deployment/deploy.sh && ${REMOTE_DIR}/deployment/deploy.sh"

Write-Host "Deployment Process Finished!" -ForegroundColor Green
