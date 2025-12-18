#!/bin/bash
#
# validate-click.sh - Validate Click CLI implementation
#
# Usage: validate-click.sh <cli-file.py>

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
    print_error "Usage: $0 <cli-file.py>"
    exit 1
fi

CLI_FILE="$1"

# Check if file exists
if [ ! -f "$CLI_FILE" ]; then
    print_error "File not found: $CLI_FILE"
    exit 1
fi

print_info "Validating Click CLI: $CLI_FILE"
echo ""

VALIDATION_PASSED=true

# Check 1: File is a Python file
if [[ ! "$CLI_FILE" =~ \.py$ ]]; then
    print_error "File must be a Python file (.py)"
    VALIDATION_PASSED=false
else
    print_success "File extension is valid (.py)"
fi

# Check 2: File imports Click
if grep -q "import click" "$CLI_FILE"; then
    print_success "Click module is imported"
else
    print_error "Click module is not imported"
    VALIDATION_PASSED=false
fi

# Check 3: Has at least one Click decorator
DECORATOR_COUNT=$(grep -c "@click\." "$CLI_FILE" || true)
if [ "$DECORATOR_COUNT" -gt 0 ]; then
    print_success "Found $DECORATOR_COUNT Click decorator(s)"
else
    print_error "No Click decorators found"
    VALIDATION_PASSED=false
fi

# Check 4: Has main entry point or group
if grep -q "@click.command()\|@click.group()" "$CLI_FILE"; then
    print_success "Has Click command or group decorator"
else
    print_error "Missing @click.command() or @click.group()"
    VALIDATION_PASSED=false
fi

# Check 5: Has if __name__ == '__main__' block
if grep -q "if __name__ == '__main__':" "$CLI_FILE"; then
    print_success "Has main execution block"
else
    print_warning "Missing main execution block (if __name__ == '__main__':)"
fi

# Check 6: Python syntax is valid
if python3 -m py_compile "$CLI_FILE" 2>/dev/null; then
    print_success "Python syntax is valid"
else
    print_error "Python syntax errors detected"
    VALIDATION_PASSED=false
fi

# Check 7: Has help text
if grep -q '"""' "$CLI_FILE"; then
    print_success "Contains docstrings/help text"
else
    print_warning "No docstrings found (recommended for help text)"
fi

# Check 8: Has option or argument decorators
if grep -q "@click.option\|@click.argument" "$CLI_FILE"; then
    print_success "Has options or arguments defined"
else
    print_warning "No options or arguments defined"
fi

# Check 9: Uses recommended patterns
echo ""
print_info "Checking best practices..."

# Check for version option
if grep -q "@click.version_option" "$CLI_FILE"; then
    print_success "Has version option"
else
    print_warning "Consider adding @click.version_option()"
fi

# Check for help parameter
if grep -q "help=" "$CLI_FILE"; then
    print_success "Uses help parameters"
else
    print_warning "Consider adding help text to options"
fi

# Check for context usage
if grep -q "@click.pass_context" "$CLI_FILE"; then
    print_success "Uses context for state sharing"
else
    print_info "No context usage detected (optional)"
fi

# Check for command groups
if grep -q "@click.group()" "$CLI_FILE"; then
    print_success "Uses command groups"
    # Check for subcommands
    SUBCOMMAND_COUNT=$(grep -c "\.command()" "$CLI_FILE" || true)
    if [ "$SUBCOMMAND_COUNT" -gt 0 ]; then
        print_success "Has $SUBCOMMAND_COUNT subcommand(s)"
    fi
fi

# Check for validation
if grep -q "click.Choice\|click.IntRange\|click.FloatRange\|click.Path" "$CLI_FILE"; then
    print_success "Uses Click's built-in validators"
else
    print_info "No built-in validators detected (optional)"
fi

# Check for colored output (Rich or Click's styling)
if grep -q "from rich\|click.style\|click.echo.*fg=" "$CLI_FILE"; then
    print_success "Uses colored output"
else
    print_info "No colored output detected (optional)"
fi

# Summary
echo ""
if [ "$VALIDATION_PASSED" = true ]; then
    print_success "All critical validations passed!"
    echo ""
    print_info "Try running: python3 $CLI_FILE --help"
    exit 0
else
    print_error "Validation failed. Please fix the errors above."
    exit 1
fi
