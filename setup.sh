#!/usr/bin/env bash
# Agenticom 1-click setup
# Usage: bash setup.sh        (or: curl ... | bash)
#
# What it does:
#   1. Detects OS (macOS / Ubuntu-Debian / Fedora-RHEL / Arch)
#   2. Installs missing prerequisites (python3, pip, venv, make, git)
#   3. Creates .venv and installs the package
#   4. Runs agenticom install (bundled workflows)
#   5. Prints next-steps summary

set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[info]${NC}  $*"; }
ok()    { echo -e "${GREEN}[ok]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $*"; }
fail()  { echo -e "${RED}[error]${NC} $*"; exit 1; }

# ── Detect OS & package manager ─────────────────────────────────────────────
detect_os() {
    if [[ "$OSTYPE" == darwin* ]]; then
        OS="macos"
        PKG="brew"
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"
        PKG="apt"
    elif [[ -f /etc/fedora-release ]] || [[ -f /etc/redhat-release ]]; then
        OS="fedora"
        PKG="dnf"
    elif [[ -f /etc/arch-release ]]; then
        OS="arch"
        PKG="pacman"
    else
        OS="unknown"
        PKG=""
    fi
    info "Detected OS: $OS"
}

# ── Install a system package if missing ──────────────────────────────────────
need_cmd() {
    command -v "$1" &>/dev/null
}

pkg_install() {
    local pkg_name="$1"
    info "Installing $pkg_name..."
    case "$PKG" in
        brew)   brew install "$pkg_name" ;;
        apt)    sudo apt-get update -qq && sudo apt-get install -y -qq "$pkg_name" ;;
        dnf)    sudo dnf install -y -q "$pkg_name" ;;
        pacman) sudo pacman -S --noconfirm "$pkg_name" ;;
        *)      fail "Cannot auto-install $pkg_name on this OS. Please install it manually." ;;
    esac
}

# ── Ensure prerequisites ─────────────────────────────────────────────────────
ensure_python() {
    if need_cmd python3; then
        ok "python3 found: $(python3 --version)"
        PYTHON=python3
        return
    fi
    if need_cmd python; then
        local ver
        ver=$(python --version 2>&1)
        if [[ "$ver" == *"3."* ]]; then
            ok "python found: $ver"
            PYTHON=python
            return
        fi
    fi
    warn "python3 not found — installing..."
    case "$PKG" in
        brew)   pkg_install python@3 ;;
        apt)    pkg_install python3 ;;
        dnf)    pkg_install python3 ;;
        pacman) pkg_install python ;;
        *)      fail "Please install Python 3.10+ manually." ;;
    esac
    PYTHON=python3
    ok "python3 installed: $($PYTHON --version)"
}

ensure_pip() {
    if $PYTHON -m pip --version &>/dev/null; then
        ok "pip found: $($PYTHON -m pip --version 2>&1 | head -1)"
        return
    fi
    warn "pip not found — installing..."
    case "$PKG" in
        brew)   : ;;  # brew's python includes pip
        apt)    pkg_install python3-pip ;;
        dnf)    pkg_install python3-pip ;;
        pacman) pkg_install python-pip ;;
        *)      $PYTHON -m ensurepip --upgrade 2>/dev/null || fail "Cannot install pip. Please install it manually." ;;
    esac
    ok "pip installed"
}

ensure_venv_module() {
    if $PYTHON -m venv --help &>/dev/null; then
        ok "venv module available"
        return
    fi
    warn "venv module not found — installing..."
    case "$PKG" in
        brew)   : ;;  # brew's python includes venv
        apt)    pkg_install python3-venv ;;
        dnf)    pkg_install python3-devel ;;
        pacman) : ;;  # arch python includes venv
        *)      fail "Cannot install python venv module. Please install it manually." ;;
    esac
    ok "venv module installed"
}

ensure_make() {
    if need_cmd make; then
        ok "make found"
        return
    fi
    warn "make not found — installing..."
    case "$PKG" in
        brew)   : ;;  # macOS includes make via Xcode CLT
        apt)    pkg_install make ;;
        dnf)    pkg_install make ;;
        pacman) pkg_install make ;;
        *)      warn "make not found — optional, skipping." ;;
    esac
}

ensure_git() {
    if need_cmd git; then
        ok "git found"
        return
    fi
    warn "git not found — installing..."
    pkg_install git
    ok "git installed"
}

ensure_brew() {
    # macOS only: ensure Homebrew is available before trying to install anything
    if [[ "$OS" == "macos" ]] && ! need_cmd brew; then
        warn "Homebrew not found — installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        # Add brew to PATH for the rest of this script
        eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null)"
        ok "Homebrew installed"
    fi
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo -e "${CYAN}=============================${NC}"
    echo -e "${CYAN}  Agenticom 1-Click Setup${NC}"
    echo -e "${CYAN}=============================${NC}"
    echo ""

    # Where is the project?
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"
    info "Project directory: $SCRIPT_DIR"

    # Step 1: Detect OS
    detect_os
    [[ "$OS" == "macos" ]] && ensure_brew

    # Step 2: Install prerequisites
    info "Checking prerequisites..."
    ensure_git
    ensure_python
    ensure_pip
    ensure_venv_module
    ensure_make
    echo ""

    # Step 3: Create venv & install
    VENV_DIR="$SCRIPT_DIR/.venv"
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        info "Already in a virtual environment: $VIRTUAL_ENV"
        PIP="$PYTHON -m pip"
    elif [[ -d "$VENV_DIR" ]]; then
        info "Using existing venv at $VENV_DIR"
        PYTHON="$VENV_DIR/bin/python"
        PIP="$VENV_DIR/bin/python -m pip"
    else
        info "Creating virtual environment..."
        $PYTHON -m venv "$VENV_DIR"
        ok "Created .venv"
        PYTHON="$VENV_DIR/bin/python"
        PIP="$VENV_DIR/bin/python -m pip"
    fi

    info "Installing agenticom..."
    $PIP install --upgrade pip --quiet 2>/dev/null || true
    $PIP install -e . --quiet
    ok "Package installed"
    echo ""

    # Step 4: Install bundled workflows
    info "Installing bundled workflows..."
    "$VENV_DIR/bin/agenticom" install 2>/dev/null || "$VENV_DIR/bin/python" -m agenticom.cli install
    echo ""

    # Step 5: Summary
    echo -e "${GREEN}=============================${NC}"
    echo -e "${GREEN}  Setup complete!${NC}"
    echo -e "${GREEN}=============================${NC}"
    echo ""
    echo "  Activate the environment:"
    echo "    source .venv/bin/activate"
    echo ""
    echo "  Then run:"
    echo "    agenticom workflow list    # see available workflows"
    echo "    agenticom workflow run feature-dev \"your task here\""
    echo ""
    echo "  For development:"
    echo "    make dev                  # install dev/test deps"
    echo "    make test                 # run tests"
    echo ""
}

main "$@"
