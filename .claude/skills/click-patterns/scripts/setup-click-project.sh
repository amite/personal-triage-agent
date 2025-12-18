#!/bin/bash
#
# setup-click-project.sh - Setup Click project dependencies and environment
#
# Usage: setup-click-project.sh [project-directory]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() { echo -e "${CYAN}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1" >&2; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

PROJECT_DIR="${1:-.}"

print_info "Setting up Click project in: $PROJECT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION detected"

# Navigate to project directory
cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "pip upgraded"

# Install Click and dependencies
print_info "Installing Click and dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Installed from requirements.txt"
else
    pip install click rich
    print_success "Installed click and rich"
fi

# Install development dependencies
print_info "Installing development dependencies..."
pip install pytest pytest-cov black pylint mypy
print_success "Development dependencies installed"

# Create .env.example if it doesn't exist
if [ ! -f ".env.example" ]; then
    cat > .env.example <<'EOF'
# Environment variables for CLI
API_KEY=your_api_key_here
DEBUG=false
LOG_LEVEL=info
EOF
    print_success "Created .env.example"
fi

# Setup pre-commit hooks if git repo
if [ -d ".git" ]; then
    print_info "Setting up git hooks..."
    cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash
# Run tests before commit
source venv/bin/activate
black src/ tests/ --check || exit 1
pylint src/ || exit 1
pytest tests/ || exit 1
EOF
    chmod +x .git/hooks/pre-commit
    print_success "Git hooks configured"
fi

# Verify installation
print_info "Verifying installation..."
python3 -c "import click; print(f'Click version: {click.__version__}')"
print_success "Click is properly installed"

echo ""
print_success "Setup completed successfully!"
echo ""
print_info "Next steps:"
echo "  1. source venv/bin/activate"
echo "  2. python src/cli.py --help"
echo "  3. pytest tests/"
