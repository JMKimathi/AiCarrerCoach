$ErrorActionPreference = "Stop"
$backendDir = $PSScriptRoot
$projectDir = Split-Path -Parent $backendDir
Set-Location $projectDir

$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
$envFile = Join-Path $backendDir ".env"

if (-not (Test-Path $venvPython)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pythonCommand) {
        & $pythonCommand.Source -m venv (Join-Path $backendDir ".venv")
    } elseif ($null -ne $pyCommand) {
        & $pyCommand.Source -3 -m venv (Join-Path $backendDir ".venv")
    } else {
        throw "Install Python 3.11+ and add it to PATH, then run this script again."
    }
}

$envContent = if (Test-Path $envFile) { Get-Content $envFile -Raw } else { "" }
$secretLine = [regex]::Match($envContent, '(?m)^SECRET_KEY=([^\r\n]+)$')
if (-not $secretLine.Success -or $secretLine.Groups[1].Value.Length -lt 32 -or $secretLine.Groups[1].Value.StartsWith("replace-")) {
    $signingKey = & $venvPython -c "import secrets; print(secrets.token_urlsafe(48))"
    if ($secretLine.Success) {
        $envContent = [regex]::Replace($envContent, '(?m)^SECRET_KEY=[^\r\n]*$', "SECRET_KEY=$signingKey")
    } else {
        $envContent = $envContent.TrimEnd() + [Environment]::NewLine + "SECRET_KEY=$signingKey" + [Environment]::NewLine
    }
    [System.IO.File]::WriteAllText($envFile, $envContent)
    Write-Host "Created or refreshed the private backend signing key in backend/.env."
}

$requirementsFile = Join-Path $backendDir "requirements.txt"
$installMarker = Join-Path $backendDir ".venv\.requirements-installed"
$needsInstall = -not (Test-Path $installMarker)
if (-not $needsInstall) {
    $needsInstall = (Get-Item $requirementsFile).LastWriteTimeUtc -gt (Get-Item $installMarker).LastWriteTimeUtc
}
if ($needsInstall) {
    & $venvPython -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) { throw "Backend dependency installation failed." }
    New-Item -ItemType File -Path $installMarker -Force | Out-Null
}
& $venvPython (Join-Path $backendDir "run.py")
