$ErrorActionPreference = "Stop"

Write-Host "Installing/updating packaging dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt

Write-Host "Checking for running packaged app..."
$runningApp = Get-Process -Name "ConductingTutor" -ErrorAction SilentlyContinue
if ($runningApp) {
    throw "ConductingTutor.exe is currently running. Close it before building."
}

Write-Host "Cleaning old build artifacts..."
if (Test-Path "dist") {
    try {
        Remove-Item -Recurse -Force "dist"
    } catch {
        throw "Could not remove dist folder. Ensure ConductingTutor.exe is closed and no files are locked."
    }
}
if (Test-Path "build") {
    try {
        Remove-Item -Recurse -Force "build"
    } catch {
        Write-Host "Warning: Could not fully remove build folder (likely file lock). Continuing with --clean."
    }
}

Write-Host "Building Conducting Tutor (Windows onefile)..."
pyinstaller --noconfirm --clean conducting_tutor.spec

if (-not (Test-Path "dist/ConductingTutor.exe")) {
    throw "PyInstaller build did not produce dist/ConductingTutor.exe"
}

Write-Host "Build complete. Output file: dist/ConductingTutor.exe"
