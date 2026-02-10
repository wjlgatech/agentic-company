#!/bin/bash
#
# 🚀 AGENTICOM ONE-CLICK INSTALLER
# Installs Agenticom with OpenClaw and Nanobot support
#
# Usage: curl -fsSL https://raw.githubusercontent.com/wjlgatech/agentic-company/main/install.sh | bash
#    or: ./install.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/.agenticom"
REPO_URL="https://github.com/wjlgatech/agentic-company.git"
PYTHON_MIN_VERSION="3.10"

echo -e "${MAGENTA}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║     🏢 AGENTICOM - AI Agent Orchestration Framework              ║"
echo "║                                                                  ║"
echo "║     One-Click Installer                                          ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print step
step() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}▶ $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to print success
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print warning
warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print error
error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    step "Checking Python installation..."

    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        error "Python not found. Please install Python $PYTHON_MIN_VERSION or higher."
    fi

    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "Found Python $PYTHON_VERSION"

    # Check version
    if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
        error "Python $PYTHON_MIN_VERSION or higher is required. Found: $PYTHON_VERSION"
    fi

    success "Python $PYTHON_VERSION is compatible"
}

# Check/Install pip
check_pip() {
    step "Checking pip..."

    if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
        warn "pip not found, installing..."
        $PYTHON_CMD -m ensurepip --upgrade || {
            curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
            $PYTHON_CMD /tmp/get-pip.py
        }
    fi

    success "pip is available"
}

# Check/Install git
check_git() {
    step "Checking git..."

    if ! command_exists git; then
        warn "git not found, attempting to install..."

        if command_exists apt-get; then
            sudo apt-get update && sudo apt-get install -y git
        elif command_exists yum; then
            sudo yum install -y git
        elif command_exists brew; then
            brew install git
        else
            error "Please install git manually: https://git-scm.com/downloads"
        fi
    fi

    success "git is available"
}

# Clone or update repository
setup_repo() {
    step "Setting up Agenticom..."

    if [ -d "$INSTALL_DIR" ]; then
        echo "Existing installation found. Updating..."
        cd "$INSTALL_DIR"
        git pull origin main || warn "Could not update. Using existing version."
    else
        echo "Cloning repository..."
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi

    success "Repository ready at $INSTALL_DIR"
}

# Create virtual environment and install
install_package() {
    step "Installing Agenticom and dependencies..."

    cd "$INSTALL_DIR"

    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install package with all dependencies
    echo "Installing Agenticom..."
    pip install -e ".[all]"

    # Install OpenClaw (Anthropic SDK)
    echo "Installing OpenClaw (Anthropic SDK)..."
    pip install anthropic>=0.30.0

    # Install Nanobot (OpenAI SDK)
    echo "Installing Nanobot (OpenAI SDK)..."
    pip install openai>=1.0.0

    success "All packages installed"
}

# Create desktop entry (Linux)
create_desktop_entry_linux() {
    step "Creating desktop launcher..."

    DESKTOP_DIR="$HOME/.local/share/applications"
    DESKTOP_FILE="$DESKTOP_DIR/agenticom.desktop"

    mkdir -p "$DESKTOP_DIR"

    # Determine icon (default to golden)
    ICON_PATH="$INSTALL_DIR/assets/icons/agenticom-golden.svg"

    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Agenticom
Comment=AI Agent Orchestration Framework
Exec=$INSTALL_DIR/venv/bin/python -m orchestration.launcher
Icon=$ICON_PATH
Terminal=false
Categories=Development;AI;
Keywords=AI;Agent;Orchestration;Claude;GPT;
StartupWMClass=Agenticom
EOF

    chmod +x "$DESKTOP_FILE"

    # Also create in Desktop folder if it exists
    if [ -d "$HOME/Desktop" ]; then
        cp "$DESKTOP_FILE" "$HOME/Desktop/agenticom.desktop"
        chmod +x "$HOME/Desktop/agenticom.desktop"
        success "Desktop shortcut created"
    fi

    success "Application menu entry created"
}

# Create desktop entry (macOS)
create_desktop_entry_macos() {
    step "Creating macOS application..."

    APP_DIR="$HOME/Applications/Agenticom.app"
    mkdir -p "$APP_DIR/Contents/MacOS"
    mkdir -p "$APP_DIR/Contents/Resources"

    # Create launcher script
    cat > "$APP_DIR/Contents/MacOS/Agenticom" << EOF
#!/bin/bash
source "$INSTALL_DIR/venv/bin/activate"
python -m orchestration.launcher
EOF
    chmod +x "$APP_DIR/Contents/MacOS/Agenticom"

    # Create Info.plist
    cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Agenticom</string>
    <key>CFBundleDisplayName</key>
    <string>Agenticom</string>
    <key>CFBundleIdentifier</key>
    <string>com.agenticom.app</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleExecutable</key>
    <string>Agenticom</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
</dict>
</plist>
EOF

    # Copy icon
    cp "$INSTALL_DIR/assets/icons/agenticom-golden.svg" "$APP_DIR/Contents/Resources/"

    # Create symlink on Desktop
    if [ -d "$HOME/Desktop" ]; then
        ln -sf "$APP_DIR" "$HOME/Desktop/Agenticom.app"
        success "Desktop shortcut created"
    fi

    success "macOS application created at $APP_DIR"
}

# Create launcher script
create_launcher() {
    step "Creating command-line launcher..."

    LAUNCHER_SCRIPT="$HOME/.local/bin/agenticom-launch"
    mkdir -p "$HOME/.local/bin"

    cat > "$LAUNCHER_SCRIPT" << EOF
#!/bin/bash
# Agenticom Launcher
source "$INSTALL_DIR/venv/bin/activate"
python -m orchestration.launcher "\$@"
EOF

    chmod +x "$LAUNCHER_SCRIPT"

    # Also create 'agentic' alias
    AGENTIC_SCRIPT="$HOME/.local/bin/agentic"
    cat > "$AGENTIC_SCRIPT" << EOF
#!/bin/bash
# Agenticom CLI
source "$INSTALL_DIR/venv/bin/activate"
python -m orchestration.cli "\$@"
EOF
    chmod +x "$AGENTIC_SCRIPT"

    success "Commands created: agenticom-launch, agentic"
}

# Setup API keys prompt
setup_api_keys() {
    step "API Key Configuration"

    echo -e "\n${YELLOW}To use Agenticom, you need at least one API key:${NC}"
    echo ""
    echo "  For Claude (OpenClaw):"
    echo "    export ANTHROPIC_API_KEY=your-key-here"
    echo ""
    echo "  For GPT (Nanobot):"
    echo "    export OPENAI_API_KEY=your-key-here"
    echo ""

    read -p "Would you like to set up API keys now? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Anthropic key
        echo -e "\n${CYAN}Enter your Anthropic API key (or press Enter to skip):${NC}"
        read -r ANTHROPIC_KEY
        if [ -n "$ANTHROPIC_KEY" ]; then
            echo "export ANTHROPIC_API_KEY=\"$ANTHROPIC_KEY\"" >> "$HOME/.bashrc"
            echo "export ANTHROPIC_API_KEY=\"$ANTHROPIC_KEY\"" >> "$HOME/.zshrc" 2>/dev/null || true
            export ANTHROPIC_API_KEY="$ANTHROPIC_KEY"
            success "Anthropic API key saved"
        fi

        # OpenAI key
        echo -e "\n${CYAN}Enter your OpenAI API key (or press Enter to skip):${NC}"
        read -r OPENAI_KEY
        if [ -n "$OPENAI_KEY" ]; then
            echo "export OPENAI_API_KEY=\"$OPENAI_KEY\"" >> "$HOME/.bashrc"
            echo "export OPENAI_API_KEY=\"$OPENAI_KEY\"" >> "$HOME/.zshrc" 2>/dev/null || true
            export OPENAI_API_KEY="$OPENAI_KEY"
            success "OpenAI API key saved"
        fi
    else
        warn "Remember to set your API keys before using Agenticom"
    fi
}

# Add to PATH
update_path() {
    step "Updating PATH..."

    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
        export PATH="$HOME/.local/bin:$PATH"
    fi

    success "PATH updated"
}

# Select icon
select_icon() {
    step "Choose your Agenticom icon"

    echo ""
    echo "Available icons:"
    echo "  1) 🐷 Piglet   - Cute and friendly"
    echo "  2) 🦀 Claw     - Tech and powerful"
    echo "  3) 🐕 Golden   - Loyal and smart (default)"
    echo ""

    read -p "Select icon (1/2/3) [3]: " -n 1 -r
    echo

    case $REPLY in
        1)
            SELECTED_ICON="agenticom-piglet.svg"
            success "Selected: Piglet 🐷"
            ;;
        2)
            SELECTED_ICON="agenticom-claw.svg"
            success "Selected: Claw 🦀"
            ;;
        *)
            SELECTED_ICON="agenticom-golden.svg"
            success "Selected: Golden Retriever 🐕"
            ;;
    esac

    # Update desktop entry with selected icon
    if [ "$(uname)" = "Linux" ]; then
        sed -i "s|Icon=.*|Icon=$INSTALL_DIR/assets/icons/$SELECTED_ICON|" "$HOME/.local/share/applications/agenticom.desktop" 2>/dev/null || true
        sed -i "s|Icon=.*|Icon=$INSTALL_DIR/assets/icons/$SELECTED_ICON|" "$HOME/Desktop/agenticom.desktop" 2>/dev/null || true
    fi
}

# Verify installation
verify_installation() {
    step "Verifying installation..."

    source "$INSTALL_DIR/venv/bin/activate"

    # Test import
    if $PYTHON_CMD -c "from orchestration import AgentTeam, create_feature_dev_team; print('✅ Core imports OK')"; then
        success "Core module working"
    else
        error "Failed to import core module"
    fi

    # Test integrations
    if $PYTHON_CMD -c "from orchestration.integrations import UnifiedExecutor; print('✅ Integrations OK')"; then
        success "Integrations working"
    else
        warn "Integrations may need API keys to work"
    fi
}

# Print completion message
print_completion() {
    echo -e "\n${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                  ║"
    echo "║     🎉 AGENTICOM INSTALLED SUCCESSFULLY! 🎉                      ║"
    echo "║                                                                  ║"
    echo "╠══════════════════════════════════════════════════════════════════╣"
    echo "║                                                                  ║"
    echo "║  📍 Installation location: $INSTALL_DIR"
    echo "║                                                                  ║"
    echo "║  🚀 Quick Start:                                                 ║"
    echo "║     1. Click the desktop icon, OR                                ║"
    echo "║     2. Run: agenticom-launch                                     ║"
    echo "║                                                                  ║"
    echo "║  💻 CLI Commands:                                                ║"
    echo "║     agentic health      - Check system status                    ║"
    echo "║     agentic serve       - Start API server                       ║"
    echo "║     agenticom-launch    - Start GUI                              ║"
    echo "║                                                                  ║"
    echo "║  📚 Documentation: https://github.com/wjlgatech/agentic-company  ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "${YELLOW}⚠️  Please restart your terminal or run: source ~/.bashrc${NC}"
    echo ""
}

# Main installation flow
main() {
    check_python
    check_pip
    check_git
    setup_repo
    install_package
    create_launcher
    update_path
    select_icon

    # Platform-specific desktop entry
    case "$(uname)" in
        Linux*)
            create_desktop_entry_linux
            ;;
        Darwin*)
            create_desktop_entry_macos
            ;;
    esac

    setup_api_keys
    verify_installation
    print_completion
}

# Run main
main "$@"
