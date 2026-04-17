$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot\..
docker compose up -d
Start-Process powershell -WorkingDirectory ".\\backend" -ArgumentList "-NoProfile","-Command","python -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -WorkingDirectory ".\\frontend" -ArgumentList "-NoProfile","-Command","npm run dev"
Pop-Location
