# 🚀 AGENTICOM ONE-CLICK INSTALLER FOR WINDOWS
# Installs Agenticom with OpenClaw and Nanobot support
#
# Usage: irm https://raw.githubusercontent.com/wjlgatech/agentic-company/main/install.ps1 | iex
#    or: .\install.ps1
#

$ErrorActionPreference = "Stop"

# Configuration
$INSTALL_DIR = "$env:USERPROFILE\.agenticom"
$REPO_URL = "https://github.com/wjlgatech/agentic-company.git"
$PYTHON_MIN_VERSION = "3.10"

function Write-Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║                                                                  ║" -ForegroundColor Magenta
    Write-Host "║     🏢 AGENTICOM - AI Agent Orchestration Framework              ║" -ForegroundColor Magenta
    Write-Host "║                                                                  ║" -ForegroundColor Magenta
    Write-Host "║     One-Click Installer for Windows                              ║" -ForegroundColor Magenta
    Write-Host "║                                                                  ║" -ForegroundColor Magenta
    Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "▶ $Message" -ForegroundColor Blue
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
    exit 1
}

function Test-Command {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

function Test-Python {
    Write-Step "Checking Python installation..."

    $pythonCmd = $null
    if (Test-Command "python") {
        $pythonCmd = "python"
    } elseif (Test-Command "python3") {
        $pythonCmd = "python3"
    } else {
        Write-Error "Python not found. Please install Python $PYTHON_MIN_VERSION or higher from https://www.python.org/downloads/"
    }

    $version = & $pythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    Write-Host "Found Python $version"

    $versionCheck = & $pythonCmd -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python $PYTHON_MIN_VERSION or higher is required. Found: $version"
    }

    Write-Success "Python $version is compatible"
    return $pythonCmd
}

function Test-Git {
    Write-Step "Checking git..."

    if (-not (Test-Command "git")) {
        Write-Warning "git not found. Please install from https://git-scm.com/download/win"
        Write-Host "After installing git, re-run this installer."
        exit 1
    }

    Write-Success "git is available"
}

function Install-Repository {
    param([string]$PythonCmd)

    Write-Step "Setting up Agenticom..."

    if (Test-Path $INSTALL_DIR) {
        Write-Host "Existing installation found. Updating..."
        Set-Location $INSTALL_DIR
        git pull origin main 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not update. Using existing version."
        }
    } else {
        Write-Host "Cloning repository..."
        git clone $REPO_URL $INSTALL_DIR
        Set-Location $INSTALL_DIR
    }

    Write-Success "Repository ready at $INSTALL_DIR"
}

function Install-Package {
    param([string]$PythonCmd)

    Write-Step "Installing Agenticom and dependencies..."

    Set-Location $INSTALL_DIR

    # Create virtual environment
    if (-not (Test-Path "venv")) {
        Write-Host "Creating virtual environment..."
        & $PythonCmd -m venv venv
    }

    # Activate virtual environment
    $activateScript = "$INSTALL_DIR\venv\Scripts\Activate.ps1"
    . $activateScript

    # Upgrade pip
    pip install --upgrade pip

    # Install package
    Write-Host "Installing Agenticom..."
    pip install -e ".[all]"

    # Install OpenClaw
    Write-Host "Installing OpenClaw (Anthropic SDK)..."
    pip install anthropic>=0.30.0

    # Install Nanobot
    Write-Host "Installing Nanobot (OpenAI SDK)..."
    pip install openai>=1.0.0

    Write-Success "All packages installed"
}

function New-DesktopShortcut {
    Write-Step "Creating desktop shortcut..."

    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Agenticom.lnk")
    $Shortcut.TargetPath = "$INSTALL_DIR\venv\Scripts\pythonw.exe"
    $Shortcut.Arguments = "-m orchestration.launcher"
    $Shortcut.WorkingDirectory = $INSTALL_DIR
    $Shortcut.IconLocation = "$INSTALL_DIR\assets\icons\agenticom-golden.ico"
    $Shortcut.Description = "Agenticom - AI Agent Orchestration"
    $Shortcut.Save()

    Write-Success "Desktop shortcut created"
}

function New-StartMenuEntry {
    Write-Step "Creating Start Menu entry..."

    $startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Agenticom"
    New-Item -ItemType Directory -Force -Path $startMenuPath | Out-Null

    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$startMenuPath\Agenticom.lnk")
    $Shortcut.TargetPath = "$INSTALL_DIR\venv\Scripts\pythonw.exe"
    $Shortcut.Arguments = "-m orchestration.launcher"
    $Shortcut.WorkingDirectory = $INSTALL_DIR
    $Shortcut.Description = "Agenticom - AI Agent Orchestration"
    $Shortcut.Save()

    Write-Success "Start Menu entry created"
}

function New-CommandScript {
    Write-Step "Creating command-line tools..."

    $binPath = "$env:USERPROFILE\.local\bin"
    New-Item -ItemType Directory -Force -Path $binPath | Out-Null

    # Create agenticom-launch.bat
    @"
@echo off
call "$INSTALL_DIR\venv\Scripts\activate.bat"
python -m orchestration.launcher %*
"@ | Out-File -FilePath "$binPath\agenticom-launch.bat" -Encoding ASCII

    # Create agentic.bat
    @"
@echo off
call "$INSTALL_DIR\venv\Scripts\activate.bat"
python -m orchestration.cli %*
"@ | Out-File -FilePath "$binPath\agentic.bat" -Encoding ASCII

    # Add to PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($currentPath -notlike "*$binPath*") {
        [Environment]::SetEnvironmentVariable("PATH", "$binPath;$currentPath", "User")
        $env:PATH = "$binPath;$env:PATH"
    }

    Write-Success "Commands created: agenticom-launch, agentic"
}

function Select-Icon {
    Write-Step "Choose your Agenticom icon"

    Write-Host ""
    Write-Host "Available icons:"
    Write-Host "  1) 🐷 Piglet   - Cute and friendly"
    Write-Host "  2) 🦀 Claw     - Tech and powerful"
    Write-Host "  3) 🐕 Golden   - Loyal and smart (default)"
    Write-Host ""

    $choice = Read-Host "Select icon (1/2/3) [3]"

    switch ($choice) {
        "1" {
            $script:SELECTED_ICON = "agenticom-piglet"
            Write-Success "Selected: Piglet 🐷"
        }
        "2" {
            $script:SELECTED_ICON = "agenticom-claw"
            Write-Success "Selected: Claw 🦀"
        }
        default {
            $script:SELECTED_ICON = "agenticom-golden"
            Write-Success "Selected: Golden Retriever 🐕"
        }
    }
}

function Set-ApiKeys {
    Write-Step "API Key Configuration"

    Write-Host ""
    Write-Host "To use Agenticom, you need at least one API key:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  For Claude (OpenClaw):"
    Write-Host "    set ANTHROPIC_API_KEY=your-key-here"
    Write-Host ""
    Write-Host "  For GPT (Nanobot):"
    Write-Host "    set OPENAI_API_KEY=your-key-here"
    Write-Host ""

    $setup = Read-Host "Would you like to set up API keys now? (y/n)"

    if ($setup -eq "y" -or $setup -eq "Y") {
        # Anthropic key
        Write-Host ""
        $anthropicKey = Read-Host "Enter your Anthropic API key (or press Enter to skip)"
        if ($anthropicKey) {
            [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $anthropicKey, "User")
            $env:ANTHROPIC_API_KEY = $anthropicKey
            Write-Success "Anthropic API key saved"
        }

        # OpenAI key
        Write-Host ""
        $openaiKey = Read-Host "Enter your OpenAI API key (or press Enter to skip)"
        if ($openaiKey) {
            [Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $openaiKey, "User")
            $env:OPENAI_API_KEY = $openaiKey
            Write-Success "OpenAI API key saved"
        }
    } else {
        Write-Warning "Remember to set your API keys before using Agenticom"
    }
}

function Test-Installation {
    Write-Step "Verifying installation..."

    $activateScript = "$INSTALL_DIR\venv\Scripts\Activate.ps1"
    . $activateScript

    try {
        python -c "from orchestration import AgentTeam, create_feature_dev_team; print('Core imports OK')"
        Write-Success "Core module working"
    } catch {
        Write-Error "Failed to import core module"
    }

    try {
        python -c "from orchestration.integrations import UnifiedExecutor; print('Integrations OK')"
        Write-Success "Integrations working"
    } catch {
        Write-Warning "Integrations may need API keys to work"
    }
}

function Write-Completion {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                                                                  ║" -ForegroundColor Green
    Write-Host "║     🎉 AGENTICOM INSTALLED SUCCESSFULLY! 🎉                      ║" -ForegroundColor Green
    Write-Host "║                                                                  ║" -ForegroundColor Green
    Write-Host "╠══════════════════════════════════════════════════════════════════╣" -ForegroundColor Green
    Write-Host "║                                                                  ║" -ForegroundColor Green
    Write-Host "║  📍 Installation: $INSTALL_DIR" -ForegroundColor Green
    Write-Host "║                                                                  ║" -ForegroundColor Green
    Write-Host "║  🚀 Quick Start:                                                 ║" -ForegroundColor Green
    Write-Host "║     1. Double-click the desktop icon, OR                         ║" -ForegroundColor Green
    Write-Host "║     2. Run: agenticom-launch                                     ║" -ForegroundColor Green
    Write-Host "║                                                                  ║" -ForegroundColor Green
    Write-Host "║  💻 CLI Commands:                                                ║" -ForegroundColor Green
    Write-Host "║     agentic health      - Check system status                    ║" -ForegroundColor Green
    Write-Host "║     agentic serve       - Start API server                       ║" -ForegroundColor Green
    Write-Host "║                                                                  ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  Please restart your terminal for PATH changes to take effect" -ForegroundColor Yellow
    Write-Host ""
}

# Main
function Main {
    Write-Banner

    $pythonCmd = Test-Python
    Test-Git
    Install-Repository -PythonCmd $pythonCmd
    Install-Package -PythonCmd $pythonCmd
    New-CommandScript
    Select-Icon
    New-DesktopShortcut
    New-StartMenuEntry
    Set-ApiKeys
    Test-Installation
    Write-Completion
}

Main
