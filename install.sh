#!/usr/bin/env bash
# salt-cisco-mcp — one-shot installer
# Usage: curl -sSL https://raw.githubusercontent.com/Muminur/salt-mcp-server/main/install.sh | bash
set -euo pipefail

BOLD='\033[1m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

info()  { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[x]${NC} $*" >&2; exit 1; }
step()  { echo -e "\n${BOLD}==> $*${NC}"; }

step "salt-cisco-mcp installer"

# --- Python version check ---
PYTHON=$(command -v python3 || command -v python || true)
[ -z "$PYTHON" ] && error "Python 3.10+ is required but was not found on PATH."
PY_VER=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    error "Python 3.10+ required (found $PY_VER)."
fi
info "Python $PY_VER — OK"

# --- salt-call check ---
if ! command -v salt-call &>/dev/null; then
    warn "salt-call not found on PATH — salt-cisco-mcp can still serve docs, but live Salt tools will be unavailable."
    warn "Install Salt 3007 from https://docs.saltproject.io/salt/install-guide/en/latest/"
else
    SALT_VER=$(salt-call --version 2>/dev/null | awk '{print $2}' || echo "unknown")
    info "salt-call $SALT_VER — found"
fi

# --- pipx ---
step "Installing salt-cisco-mcp via pipx"
if ! command -v pipx &>/dev/null; then
    info "pipx not found — installing..."
    $PYTHON -m pip install --quiet --user pipx
    $PYTHON -m pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
fi
pipx install "salt-cisco-mcp" --force
info "salt-cisco-mcp installed"

# --- initial setup ---
step "Running initial setup"
if [ "$EUID" -eq 0 ]; then
    salt-cisco-mcp install
else
    warn "Not running as root — skipping 'salt-cisco-mcp install' (needs sudo for /etc/salt/mcp/)."
    warn "Run manually:  sudo salt-cisco-mcp install"
fi

# --- doc index ---
step "Building offline documentation index"
echo ""
echo "  This downloads and indexes the Salt 3007 module docs (~5 min, ~50 MB)."
read -r -p "  Build the index now? [Y/n] " REPLY
REPLY=${REPLY:-Y}
if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    salt-cisco-mcp scrape
    info "Index built"
else
    warn "Skipped. Run 'salt-cisco-mcp scrape' before starting the server."
fi

# --- verify ---
step "Verifying install"
salt-cisco-mcp verify || warn "Verify reported warnings — check output above."

# --- done ---
echo ""
echo -e "${BOLD}${GREEN}Done!${NC}"
echo ""
echo "  Start the server (stdio, for Claude Code / Codex CLI):"
echo "    salt-cisco-mcp serve --transport stdio"
echo ""
echo "  Start the server (HTTP, for Copilot / Continue / Cursor):"
echo "    salt-cisco-mcp serve --transport http --port 7842"
echo ""
echo "  Add to Claude Code:"
echo "    claude mcp add salt-cisco-mcp -- salt-cisco-mcp serve --transport stdio"
echo ""
echo "  Full docs:  https://github.com/Muminur/salt-mcp-server"
