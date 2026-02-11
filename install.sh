#!/bin/bash
# Agenticom installer for OpenClaw and Nanobot
# Usage: curl -fsSL https://raw.githubusercontent.com/wjlgatech/agentic-company/main/install.sh | bash

set -e

# Detect environment
if [ -d "$HOME/.openclaw" ]; then
    INSTALL_DIR="$HOME/.openclaw/workspace/agenticom"
    SKILL_DIR="$HOME/.openclaw/skills"
    ENV="openclaw"
elif [ -d "$HOME/.nanobot" ]; then
    INSTALL_DIR="$HOME/.nanobot/workspace/agenticom"
    SKILL_DIR="$HOME/.nanobot/skills"
    ENV="nanobot"
else
    INSTALL_DIR="$HOME/.agenticom/src"
    SKILL_DIR=""
    ENV="standalone"
fi

echo "🤖 Installing Agenticom ($ENV)..."

# Clone or update
if [ -d "$INSTALL_DIR" ]; then
    echo "📦 Updating existing installation..."
    cd "$INSTALL_DIR" && git pull
else
    echo "📦 Cloning repository..."
    git clone https://github.com/wjlgatech/agentic-company.git "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# Install Python package
echo "🐍 Installing Python package..."
pip install -e . --quiet 2>/dev/null || pip install -e . --quiet --break-system-packages

# Install bundled workflows
echo "📋 Installing workflows..."
python -m agenticom.cli install

# Copy skill files if in assistant environment
if [ -n "$SKILL_DIR" ]; then
    echo "📁 Installing skill files..."
    mkdir -p "$SKILL_DIR"
    if [ "$ENV" = "openclaw" ]; then
        cp -r skills/agenticom-workflows "$SKILL_DIR/"
    elif [ "$ENV" = "nanobot" ]; then
        cp -r skills/agenticom-nanobot "$SKILL_DIR/agenticom"
    fi
fi

# Add to PATH if standalone
if [ "$ENV" = "standalone" ]; then
    SCRIPT_DIR=$(python -c "import site; print(site.USER_BASE)")/bin
    if [[ ":$PATH:" != *":$SCRIPT_DIR:"* ]]; then
        echo "💡 Add to PATH: export PATH=\"\$PATH:$SCRIPT_DIR\""
    fi
fi

echo ""
echo "✅ Agenticom installed successfully!"
echo ""
echo "🚀 Quick start:"
echo "   python -m agenticom.cli workflow list"
echo "   python -m agenticom.cli workflow run feature-dev \"Add user login\""
echo ""
