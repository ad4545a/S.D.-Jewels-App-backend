$VPS_URL = "http://117.252.16.130/send-test-notification"

Write-Host "Sending Test Error Notification..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri $VPS_URL -Method Post -ContentType "application/json" -Body '{"message": "Test Error from Antigravity Verification"}'
    
    if ($response.success) {
        Write-Host "Success! Server response: $($response.message)" -ForegroundColor Green
        Write-Host "Please check your email inbox for 'Test Notification'." -ForegroundColor Yellow
    } else {
        Write-Host "Failed. Server response: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "Error connecting to server: $_" -ForegroundColor Red
}
