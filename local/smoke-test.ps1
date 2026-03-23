param(
    [string]$ApiBaseUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000"
)

$ErrorActionPreference = "Stop"

Write-Host "Checking frontend: $FrontendUrl"
$frontendResponse = Invoke-WebRequest -Uri $FrontendUrl -Method Get
Write-Host "Frontend status: $($frontendResponse.StatusCode)"

Write-Host "Checking API health: $ApiBaseUrl/health"
$healthResponse = Invoke-RestMethod -Uri "$ApiBaseUrl/health" -Method Get
$healthResponse | ConvertTo-Json -Depth 5
