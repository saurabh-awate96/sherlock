#!/bin/bash
# ==============================================================================
# GOOGLE ANTIGRAVITY - MYCROFT TOOL INSTALLER
# ==============================================================================
# Installs all required security tools with version management and isolation
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${FRAMEWORK_ROOT}/_audit_tools/venv"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_success() { echo -e "${GREEN}[✓]${NC}     $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           GOOGLE ANTIGRAVITY - MYCROFT INSTALLER              ║${NC}"
echo -e "${CYAN}║                     System v3.0                               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ==============================================================================
# PREREQUISITE CHECKS
# ==============================================================================
log_info "Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { log_error "Python3 required but not installed."; exit 1; }
command -v git >/dev/null 2>&1 || { log_error "Git required but not installed."; exit 1; }

log_success "Prerequisites OK"

# ==============================================================================
# PYTHON VIRTUAL ENVIRONMENT (Isolation)
# ==============================================================================
log_info "Setting up Python virtual environment..."

mkdir -p "${FRAMEWORK_ROOT}/_audit_tools"

if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
    log_success "Created virtual environment at $VENV_DIR"
else
    log_info "Virtual environment already exists"
fi

# Activate venv
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip --quiet
pip install openai langchain qdrant-client --quiet
log_success "Installed AGI dependencies (openai, langchain, qdrant-client)"

log_success "Python virtual environment activated"

# ==============================================================================
# FOUNDRY
# ==============================================================================
log_info "Installing Foundry..."

if command -v forge &> /dev/null; then
    FORGE_VERSION=$(forge --version 2>/dev/null | head -1 || echo "installed")
    log_success "Foundry already installed: $FORGE_VERSION"
else
    curl -L https://foundry.paradigm.xyz | bash
    export PATH="$HOME/.foundry/bin:$PATH"
    foundryup
    log_success "Foundry installed"
fi

# ==============================================================================
# SLITHER (via pip in venv)
# ==============================================================================
log_info "Installing Slither..."

pip install slither-analyzer --quiet
log_success "Slither installed in virtual environment"

# ==============================================================================
# SOLC-SELECT (Compiler Version Manager)
# ==============================================================================
log_info "Installing solc-select..."

pip install solc-select --quiet
solc-select install 0.8.20 --quiet 2>/dev/null || true
solc-select install 0.8.24 --quiet 2>/dev/null || true
solc-select use 0.8.20 2>/dev/null || true

log_success "solc-select installed with versions 0.8.20, 0.8.24"

# ==============================================================================
# MYTHRIL
# ==============================================================================
log_info "Installing Mythril..."

pip install mythril --quiet || log_warn "Mythril installation failed (may require additional deps)"

if command -v myth &> /dev/null; then
    log_success "Mythril installed"
else
    log_warn "Mythril binary not in PATH"
fi

# ==============================================================================
# HALMOS
# ==============================================================================
log_info "Installing Halmos..."

pip install halmos --quiet

if command -v halmos &> /dev/null; then
    log_success "Halmos installed"
else
    log_warn "Halmos binary not in PATH"
fi

# ==============================================================================
# ADERYN (Rust-based)
# ==============================================================================
log_info "Installing Aderyn..."

if command -v aderyn &> /dev/null; then
    log_success "Aderyn already installed"
elif command -v cargo &> /dev/null; then
    cargo install aderyn --quiet 2>/dev/null || log_warn "Aderyn installation failed"
    log_success "Aderyn installed via Cargo"
else
    log_warn "Cargo not found - skipping Aderyn (install Rust first)"
fi

# ==============================================================================
# MEDUSA (Go-based)
# ==============================================================================
log_info "Installing Medusa..."

if command -v medusa &> /dev/null; then
    log_success "Medusa already installed"
elif command -v go &> /dev/null; then
    go install github.com/crytic/medusa@latest 2>/dev/null || log_warn "Medusa installation failed"
    log_success "Medusa installed via Go"
else
    log_warn "Go not found - skipping Medusa (install Go first)"
fi

# ==============================================================================
# ECHIDNA (via Homebrew on Mac)
# ==============================================================================
log_info "Installing Echidna..."

if command -v echidna &> /dev/null; then
    log_success "Echidna already installed"
elif [[ "$OSTYPE" == "darwin"* ]] && command -v brew &> /dev/null; then
    brew install echidna 2>/dev/null || log_warn "Echidna installation failed"
    log_success "Echidna installed via Homebrew"
else
    log_warn "Echidna requires manual installation: https://github.com/crytic/echidna/releases"
fi

# ==============================================================================
# CLOC (Code Metrics)
# ==============================================================================
log_info "Installing cloc..."

if command -v cloc &> /dev/null; then
    log_success "cloc already installed"
elif [[ "$OSTYPE" == "darwin"* ]] && command -v brew &> /dev/null; then
    brew install cloc 2>/dev/null || log_warn "cloc installation failed"
    log_success "cloc installed via Homebrew"
else
    log_warn "cloc requires manual installation"
fi

# ==============================================================================
# GRAPHVIZ (For graph generation)
# ==============================================================================
log_info "Installing Graphviz..."

if command -v dot &> /dev/null; then
    log_success "Graphviz already installed"
elif [[ "$OSTYPE" == "darwin"* ]] && command -v brew &> /dev/null; then
    brew install graphviz 2>/dev/null || log_warn "Graphviz installation failed"
    log_success "Graphviz installed via Homebrew"
else
    log_warn "Graphviz requires manual installation"
fi

# ==============================================================================
# PANDOC (Report Generation)
# ==============================================================================
log_info "Installing Pandoc..."

if command -v pandoc &> /dev/null; then
    log_success "Pandoc already installed"
elif [[ "$OSTYPE" == "darwin"* ]] && command -v brew &> /dev/null; then
    brew install pandoc 2>/dev/null || log_warn "Pandoc installation failed"
    log_success "Pandoc installed via Homebrew"
else
    log_warn "Pandoc requires manual installation"
fi

# ==============================================================================
# TREE-SITTER (AST Parsing)
# ==============================================================================
log_info "Installing Tree-Sitter..."

if command -v tree-sitter &> /dev/null; then
    log_success "Tree-Sitter already installed"
elif command -v npm &> /dev/null; then
    npm install -g tree-sitter-cli 2>/dev/null || log_warn "Tree-Sitter installation failed"
    log_success "Tree-Sitter installed via npm"
else
    log_warn "npm not found - skipping Tree-Sitter"
fi

# ==============================================================================
# SURYA (Contract Visualization)
# ==============================================================================
log_info "Installing Surya..."

if command -v surya &> /dev/null; then
    log_success "Surya already installed"
elif command -v npm &> /dev/null; then
    npm install -g surya 2>/dev/null || log_warn "Surya installation failed"
    log_success "Surya installed via npm"
else
    log_warn "npm not found - skipping Surya"
fi

# ==============================================================================
# VECTOR DATABASE (Qdrant)
# ==============================================================================
log_info "Checking Vector Database prerequisites..."

if command -v docker &> /dev/null; then
    log_success "Docker is installed"
    echo -e "${YELLOW}[NOTE]${NC} To start the Vector DB, run: docker run -p 6333:6333 qdrant/qdrant"
else
    log_warn "Docker not found. Vector DB (Qdrant) must be installed manually or run remotely."
fi

# ==============================================================================
# MAKE SCRIPTS EXECUTABLE
# ==============================================================================
log_info "Making scripts executable..."

chmod +x "${FRAMEWORK_ROOT}/scripts/"*.sh 2>/dev/null || true

log_success "Scripts are executable"

# ==============================================================================
# CREATE ACTIVATION SCRIPT
# ==============================================================================
log_info "Creating activation script..."

cat > "${FRAMEWORK_ROOT}/activate.sh" << 'EOF'
#!/bin/bash
# Activate Mycroft environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate Python venv
if [[ -f "${SCRIPT_DIR}/_audit_tools/venv/bin/activate" ]]; then
    source "${SCRIPT_DIR}/_audit_tools/venv/bin/activate"
    echo "✓ Python virtual environment activated"
fi

# Add Foundry to PATH
export PATH="$HOME/.foundry/bin:$PATH"

# Add Go binaries to PATH
export PATH="$HOME/go/bin:$PATH"

echo "✓ Mycroft Antigravity v3.0 environment ready"
echo ""
echo "Available commands:"
echo "  ./scripts/audit_workflow.sh {metrics|static|dynamic|report|all} [project_path]"
EOF

chmod +x "${FRAMEWORK_ROOT}/activate.sh"

log_success "Activation script created: activate.sh"

# ==============================================================================
# SUMMARY
# ==============================================================================
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                 INSTALLATION COMPLETE${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Installed tools:"
command -v forge &> /dev/null && echo "  ✓ Foundry (forge, cast, anvil, chisel)"
command -v slither &> /dev/null && echo "  ✓ Slither"
command -v myth &> /dev/null && echo "  ✓ Mythril"
command -v halmos &> /dev/null && echo "  ✓ Halmos"
command -v aderyn &> /dev/null && echo "  ✓ Aderyn"
command -v medusa &> /dev/null && echo "  ✓ Medusa"
command -v echidna &> /dev/null && echo "  ✓ Echidna"
command -v cloc &> /dev/null && echo "  ✓ cloc"
command -v dot &> /dev/null && echo "  ✓ Graphviz"
command -v pandoc &> /dev/null && echo "  ✓ Pandoc"
command -v surya &> /dev/null && echo "  ✓ Surya"
command -v tree-sitter &> /dev/null && echo "  ✓ Tree-Sitter"
echo ""
echo "To activate environment:"
echo "  source ${FRAMEWORK_ROOT}/activate.sh"
echo ""
echo "To run audit:"
echo "  ./scripts/audit_workflow.sh all /path/to/project"
echo ""
