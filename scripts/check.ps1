$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot\..
python -m compileall backend\\app backend\\tests
Push-Location backend
python -m pytest -q
Pop-Location
Push-Location frontend
npm run build
Pop-Location
Pop-Location
