# check_vps_logs.ps1
$VPS_IP = "117.252.16.130"
$VPS_USER = "root"

Write-Host "Fetching logs from $VPS_IP..." -ForegroundColor Cyan
ssh "${VPS_USER}@${VPS_IP}" "journalctl -u market_monitor -n 50 --no-pager"
Write-Host "Done." -ForegroundColor Cyan
