$root = $PSScriptRoot

Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    "cd '$root\backend'; .\.venv\Scripts\Activate.ps1; uvicorn src.main:app --reload"
)

Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    "cd '$root\frontend'; npm run dev"
)
