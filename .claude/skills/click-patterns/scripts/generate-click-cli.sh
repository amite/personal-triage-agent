#!/bin/bash
#
# generate-click-cli.sh - Generate Click CLI project structure
#
# Usage: generate-click-cli.sh <project-name> [cli-type]
#   cli-type: basic, nested, or advanced (default: basic)

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

# Validate arguments
if [ $# -lt 1 ]; then
    print_error "Usage: $0 <project-name> [cli-type]"
    echo "  cli-type: basic, nested, or advanced (default: basic)"
    exit 1
fi

PROJECT_NAME="$1"
CLI_TYPE="${2:-basic}"

# Validate CLI type
if [[ ! "$CLI_TYPE" =~ ^(basic|nested|advanced)$ ]]; then
    print_error "Invalid CLI type: $CLI_TYPE"
    echo "  Valid types: basic, nested, advanced"
    exit 1
fi

# Validate project name
if [[ ! "$PROJECT_NAME" =~ ^[a-z0-9_-]+$ ]]; then
    print_error "Invalid project name: $PROJECT_NAME"
    echo "  Must contain only lowercase letters, numbers, hyphens, and underscores"
    exit 1
fi

# Create project directory
if [ -d "$PROJECT_NAME" ]; then
    print_error "Directory already exists: $PROJECT_NAME"
    exit 1
fi

print_info "Creating Click CLI project: $PROJECT_NAME (type: $CLI_TYPE)"

# Create directory structure
mkdir -p "$PROJECT_NAME"/{src,tests,docs}

# Determine which template to use
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE_FILE=""

case "$CLI_TYPE" in
    basic)
        TEMPLATE_FILE="$SKILL_DIR/templates/basic-cli.py"
        ;;
    nested)
        TEMPLATE_FILE="$SKILL_DIR/templates/nested-commands.py"
        ;;
    advanced)
        # For advanced, use nested as base with validators
        TEMPLATE_FILE="$SKILL_DIR/templates/nested-commands.py"
        ;;
esac

# Copy template
if [ ! -f "$TEMPLATE_FILE" ]; then
    print_error "Template file not found: $TEMPLATE_FILE"
    exit 1
fi

cp "$TEMPLATE_FILE" "$PROJECT_NAME/src/cli.py"
print_success "Created src/cli.py from template"

# Copy validators if advanced type
if [ "$CLI_TYPE" = "advanced" ]; then
    VALIDATORS_FILE="$SKILL_DIR/templates/validators.py"
    if [ -f "$VALIDATORS_FILE" ]; then
        cp "$VALIDATORS_FILE" "$PROJECT_NAME/src/validators.py"
        print_success "Created src/validators.py"
    fi
fi

# Create __init__.py
cat > "$PROJECT_NAME/src/__init__.py" <<'EOF'
"""
CLI application package
"""
from .cli import cli

__version__ = "1.0.0"
__all__ = ["cli"]
EOF
print_success "Created src/__init__.py"

# Create requirements.txt
cat > "$PROJECT_NAME/requirements.txt" <<'EOF'
click>=8.0.0
rich>=13.0.0
EOF
print_success "Created requirements.txt"

# Create setup.py
cat > "$PROJECT_NAME/setup.py" <<EOF
from setuptools import setup, find_packages

setup(
    name="${PROJECT_NAME}",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "${PROJECT_NAME}=src.cli:cli",
        ],
    },
    python_requires=">=3.8",
)
EOF
print_success "Created setup.py"

# Create pyproject.toml
cat > "$PROJECT_NAME/pyproject.toml" <<EOF
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "${PROJECT_NAME}"
version = "1.0.0"
description = "A Click-based CLI tool"
requires-python = ">=3.8"
dependencies = [
    "click>=8.0.0",
    "rich>=13.0.0",
]

[project.scripts]
${PROJECT_NAME} = "src.cli:cli"
EOF
print_success "Created pyproject.toml"

# Create README.md
cat > "$PROJECT_NAME/README.md" <<EOF
# ${PROJECT_NAME}

A CLI tool built with Click framework.

## Installation

\`\`\`bash
pip install -e .
\`\`\`

## Usage

\`\`\`bash
# Show help
${PROJECT_NAME} --help

# Run command
${PROJECT_NAME} <command>
\`\`\`

## Development

\`\`\`bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Format code
black src/ tests/

# Lint code
pylint src/ tests/
\`\`\`

## Project Structure

\`\`\`
${PROJECT_NAME}/
├── src/
│   ├── __init__.py
│   └── cli.py          # Main CLI implementation
├── tests/
│   └── test_cli.py     # Unit tests
├── docs/
│   └── usage.md        # Usage documentation
├── requirements.txt    # Dependencies
├── setup.py           # Setup configuration
└── README.md          # This file
\`\`\`

## License

MIT
EOF
print_success "Created README.md"

# Create basic test file
cat > "$PROJECT_NAME/tests/test_cli.py" <<'EOF'
import pytest
from click.testing import CliRunner
from src.cli import cli


def test_cli_help():
    """Test CLI help output"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output


def test_cli_version():
    """Test CLI version output"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert '1.0.0' in result.output
EOF
print_success "Created tests/test_cli.py"

# Create .gitignore
cat > "$PROJECT_NAME/.gitignore" <<'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/

# Environment
.env
.env.local
EOF
print_success "Created .gitignore"

# Create usage documentation
cat > "$PROJECT_NAME/docs/usage.md" <<EOF
# ${PROJECT_NAME} Usage Guide

## Installation

Install the CLI tool:

\`\`\`bash
pip install -e .
\`\`\`

## Commands

### Help

Show available commands:

\`\`\`bash
${PROJECT_NAME} --help
\`\`\`

### Version

Show version information:

\`\`\`bash
${PROJECT_NAME} --version
\`\`\`

## Examples

Add specific examples for your CLI commands here.
EOF
print_success "Created docs/usage.md"

# Print summary
echo ""
print_success "Click CLI project created successfully!"
echo ""
print_info "Next steps:"
echo "  1. cd $PROJECT_NAME"
echo "  2. python -m venv venv"
echo "  3. source venv/bin/activate"
echo "  4. pip install -e ."
echo "  5. $PROJECT_NAME --help"
echo ""
print_info "Project type: $CLI_TYPE"
print_info "Location: $(pwd)/$PROJECT_NAME"
