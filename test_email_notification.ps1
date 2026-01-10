# test_email_notification.ps1
$VPS_IP = "117.252.16.130"
$VPS_USER = "root"

Write-Host "Testing Email Notification..." -ForegroundColor Cyan

# 1. Stop the Service
Write-Host "Stopping Server... (This should trigger the email)" -ForegroundColor Yellow
ssh "${VPS_USER}@${VPS_IP}" "systemctl stop market_monitor"

Write-Host "Server Stopped!" -ForegroundColor Red
Write-Host "Please check your email now." -ForegroundColor Green
Write-Host "Waiting 10 seconds..."
Start-Sleep -Seconds 2

Pause

# 2. Restart
Write-Host "Restarting Server..." -ForegroundColor Yellow
ssh "${VPS_USER}@${VPS_IP}" "systemctl start market_monitor"

Write-Host "Server is back online!" -ForegroundColor Green
