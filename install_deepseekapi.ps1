#!/usr/bin/env pwsh
# install_deepseek_api.ps1
Write-Host "Installing DeepSeek API-based code assistance..." -ForegroundColor Green

# Install VS Code if needed
if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
    Write-Host "Installing VS Code..." -ForegroundColor Yellow
    
    # Check if Chocolatey is installed (recommended package manager for Windows)
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Host "Installing Chocolatey package manager..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    }
    
    # Install VS Code via Chocolatey
    choco install vscode -y
}

# Install DeepSeek extension
Write-Host "Installing DeepSeek Coder extension..." -ForegroundColor Yellow
try {
    # Try the correct extension ID
    code --install-extension deepseek-ai.deepseek-coder
}
catch {
    Write-Host "Extension installation failed. Try manual installation:" -ForegroundColor Yellow
    Write-Host "1. Open VS Code" -ForegroundColor Cyan
    Write-Host "2. Press Ctrl+Shift+X" -ForegroundColor Cyan
    Write-Host "3. Search for 'DeepSeek Coder'" -ForegroundColor Cyan
    Write-Host "4. Click Install" -ForegroundColor Cyan
}

# Alternative: Open VS Code Marketplace directly
Write-Host "`nOpening DeepSeek Coder extension page..." -ForegroundColor Yellow
Start-Process "https://marketplace.visualstudio.com/items?itemName=deepseek-ai.deepseek-coder"

# Cleanup (Windows-specific)
Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow
Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Clear-RecycleBin -Force -ErrorAction SilentlyContinue

# Final instructions
Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "1. Open VS Code" -ForegroundColor Cyan
Write-Host "2. Go to Extensions (Ctrl+Shift+X) → DeepSeek Coder" -ForegroundColor Cyan
Write-Host "3. Click 'Install' if not already installed" -ForegroundColor Cyan
Write-Host "4. Click the DeepSeek icon in the Activity Bar" -ForegroundColor Cyan
Write-Host "5. Enter your API key from: https://platform.deepseek.com" -ForegroundColor Cyan
Write-Host "6. Start coding with AI assistance!" -ForegroundColor Cyan

# Optional: Create desktop shortcut
Write-Host "`nCreating desktop shortcut..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\VS Code.lnk")
$Shortcut.TargetPath = "$env:PROGRAMFILES\Microsoft VS Code\Code.exe"
$Shortcut.Save()