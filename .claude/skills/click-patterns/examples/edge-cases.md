# Click Framework Edge Cases and Solutions

Common edge cases, gotchas, and their solutions when working with Click.

## Table of Contents

1. [Parameter Handling Edge Cases](#parameter-handling-edge-cases)
2. [Context and State Edge Cases](#context-and-state-edge-cases)
3. [Error Handling Edge Cases](#error-handling-edge-cases)
4. [Testing Edge Cases](#testing-edge-cases)
5. [Platform-Specific Edge Cases](#platform-specific-edge-cases)

---

## Parameter Handling Edge Cases

### Case 1: Multiple Values with Same Option

**Problem**: User specifies the same option multiple times

```bash
cli --tag python --tag docker --tag kubernetes
```

**Solution**: Use `multiple=True`

```python
@click.option('--tag', multiple=True)
def command(tag):
    """Handle multiple values"""
    for t in tag:
        click.echo(t)
```

### Case 2: Option vs Argument Ambiguity

**Problem**: Argument that looks like an option

```bash
cli process --file=-myfile.txt  # -myfile.txt looks like option
```

**Solution**: Use `--` separator or quotes

```python
@click.command()
@click.argument('filename')
def process(filename):
    pass

# Usage:
# cli process -- -myfile.txt
# cli process "-myfile.txt"
```

### Case 3: Empty String vs None

**Problem**: Distinguishing between no value and empty string

```python
@click.option('--name')
def command(name):
    # name is None when not provided
    # name is '' when provided as empty
    if name is None:
        click.echo('Not provided')
    elif name == '':
        click.echo('Empty string provided')
```

**Solution**: Use callback for custom handling

```python
def handle_empty(ctx, param, value):
    if value == '':
        return None  # Treat empty as None
    return value

@click.option('--name', callback=handle_empty)
def command(name):
    pass
```

### Case 4: Boolean Flag with Default True

**Problem**: Need a flag that's True by default, but can be disabled

```python
# Wrong approach:
@click.option('--enable', is_flag=True, default=True)  # Doesn't work as expected

# Correct approach:
@click.option('--disable', is_flag=True)
def command(disable):
    enabled = not disable
```

**Better Solution**: Use flag_value

```python
@click.option('--ssl/--no-ssl', default=True)
def command(ssl):
    """SSL is enabled by default, use --no-ssl to disable"""
    pass
```

### Case 5: Required Option with Environment Variable

**Problem**: Make option required unless env var is set

```python
def require_if_no_env(ctx, param, value):
    """Require option if environment variable not set"""
    if value is None:
        import os
        env_value = os.getenv('API_KEY')
        if env_value:
            return env_value
        raise click.MissingParameter(param=param)
    return value

@click.option('--api-key', callback=require_if_no_env)
def command(api_key):
    pass
```

---

## Context and State Edge Cases

### Case 6: Context Not Available in Callbacks

**Problem**: Need context in parameter callback

```python
# This doesn't work - context not yet initialized:
def my_callback(ctx, param, value):
    config = ctx.obj['config']  # Error: ctx.obj is None
    return value
```

**Solution**: Use command decorator to set up context first

```python
@click.command()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config()

@cli.command()
@click.option('--value', callback=validate_with_config)
@click.pass_context
def subcommand(ctx, value):
    # Now ctx.obj is available
    pass
```

### Case 7: Sharing State Between Command Groups

**Problem**: State not persisting across nested groups

```python
@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj['data'] = 'test'

@cli.group()
@click.pass_context
def subgroup(ctx):
    # ctx.obj is still available here
    assert ctx.obj['data'] == 'test'

@subgroup.command()
@click.pass_context
def command(ctx):
    # ctx.obj is still available here too
    assert ctx.obj['data'] == 'test'
```

### Case 8: Mutating Context Objects

**Problem**: Changes to context not persisting

```python
# This works:
ctx.obj['key'] = 'value'  # Modifying dict

# This doesn't persist:
ctx.obj = {'key': 'value'}  # Replacing dict
```

---

## Error Handling Edge Cases

### Case 9: Graceful Handling of Ctrl+C

**Problem**: Ugly traceback on keyboard interrupt

```python
def main():
    try:
        cli()
    except KeyboardInterrupt:
        click.echo('\n\nOperation cancelled by user')
        raise SystemExit(130)  # Standard exit code for Ctrl+C

if __name__ == '__main__':
    main()
```

### Case 10: Custom Error Messages for Validation

**Problem**: Default error messages aren't user-friendly

```python
# Default error:
@click.option('--port', type=click.IntRange(1, 65535))
# Error: Invalid value for '--port': 70000 is not in the range 1<=x<=65535

# Custom error:
def validate_port(ctx, param, value):
    if not 1 <= value <= 65535:
        raise click.BadParameter(
            f'Port {value} is out of range. Please use a port between 1 and 65535.'
        )
    return value

@click.option('--port', type=int, callback=validate_port)
```

### Case 11: Handling Mutually Exclusive Options

**Problem**: Options that can't be used together

```python
def validate_exclusive(ctx, param, value):
    """Ensure mutually exclusive options"""
    if value and ctx.params.get('other_option'):
        raise click.UsageError(
            'Cannot use --option and --other-option together'
        )
    return value

@click.command()
@click.option('--option', callback=validate_exclusive)
@click.option('--other-option')
def command(option, other_option):
    pass
```

### Case 12: Dependent Options

**Problem**: One option requires another

```python
@click.command()
@click.option('--ssl', is_flag=True)
@click.option('--cert', type=click.Path(exists=True))
@click.option('--key', type=click.Path(exists=True))
def server(ssl, cert, key):
    """Validate dependent options"""
    if ssl:
        if not cert or not key:
            raise click.UsageError(
                '--ssl requires both --cert and --key'
            )
```

---

## Testing Edge Cases

### Case 13: Testing with Environment Variables

**Problem**: Tests failing due to environment pollution

```python
def test_with_clean_env():
    """Test with isolated environment"""
    runner = CliRunner()

    # This isolates environment variables:
    result = runner.invoke(
        cli,
        ['command'],
        env={'API_KEY': 'test'},
        catch_exceptions=False
    )

    assert result.exit_code == 0
```

### Case 14: Testing Interactive Prompts with Validation

**Problem**: Prompts with retry logic

```python
def test_interactive_retry():
    """Test prompt with retry on invalid input"""
    runner = CliRunner()

    # Provide multiple inputs (first invalid, second valid)
    result = runner.invoke(
        cli,
        ['create'],
        input='invalid-email\nvalid@email.com\n'
    )

    assert 'Invalid email' in result.output
    assert result.exit_code == 0
```

### Case 15: Testing File Operations

**Problem**: Tests creating actual files

```python
def test_file_operations():
    """Test with isolated filesystem"""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create test file
        with open('input.txt', 'w') as f:
            f.write('test data')

        result = runner.invoke(cli, ['process', 'input.txt'])

        # Verify output file
        assert Path('output.txt').exists()
```

---

## Platform-Specific Edge Cases

### Case 16: Windows Path Handling

**Problem**: Backslashes in Windows paths

```python
@click.option('--path', type=click.Path())
def command(path):
    # Use pathlib for cross-platform compatibility
    from pathlib import Path
    p = Path(path)  # Handles Windows/Unix paths
```

### Case 17: Unicode in Command Line Arguments

**Problem**: Non-ASCII characters in arguments

```python
@click.command()
@click.argument('name')
def greet(name):
    """Handle unicode properly"""
    # Click handles unicode automatically on Python 3
    click.echo(f'Hello, {name}!')

# This works:
# cli greet "José"
# cli greet "北京"
```

### Case 18: Terminal Width Detection

**Problem**: Output formatting for different terminal sizes

```python
@click.command()
def status():
    """Adapt to terminal width"""
    terminal_width = click.get_terminal_size()[0]

    if terminal_width < 80:
        # Compact output for narrow terminals
        click.echo('Status: OK')
    else:
        # Detailed output for wide terminals
        click.echo('='  * terminal_width)
        click.echo('Detailed Status Information')
        click.echo('=' * terminal_width)
```

---

## Advanced Edge Cases

### Case 19: Dynamic Command Registration

**Problem**: Register commands at runtime

```python
class DynamicGroup(click.Group):
    """Group that discovers commands dynamically"""

    def list_commands(self, ctx):
        """List available commands"""
        # Dynamically discover commands
        return ['cmd1', 'cmd2', 'cmd3']

    def get_command(self, ctx, name):
        """Load command on demand"""
        if name in self.list_commands(ctx):
            # Import and return command
            module = __import__(f'commands.{name}')
            return getattr(module, name).cli
        return None

@click.command(cls=DynamicGroup)
def cli():
    pass
```

### Case 20: Command Aliases

**Problem**: Support command aliases

```python
class AliasedGroup(click.Group):
    """Group that supports command aliases"""

    def get_command(self, ctx, cmd_name):
        """Resolve aliases"""
        aliases = {
            'ls': 'list',
            'rm': 'remove',
            'cp': 'copy'
        }

        # Resolve alias
        resolved = aliases.get(cmd_name, cmd_name)
        return super().get_command(ctx, resolved)

@click.group(cls=AliasedGroup)
def cli():
    pass

@cli.command()
def list():
    """List items (alias: ls)"""
    pass
```

### Case 21: Progress Bar with Unknown Length

**Problem**: Show progress when total is unknown

```python
@click.command()
def process():
    """Process with indeterminate progress"""
    import time

    # For unknown length, use length=None
    with click.progressbar(
        range(100),
        length=None,
        label='Processing'
    ) as bar:
        for _ in bar:
            time.sleep(0.1)
```

---

## Summary

Key takeaways for handling edge cases:

1. **Parameters**: Use callbacks and custom types for complex validation
2. **Context**: Ensure context is initialized before accessing ctx.obj
3. **Errors**: Provide clear, actionable error messages
4. **Testing**: Use CliRunner's isolation features
5. **Platform**: Use pathlib and Click's built-in utilities for portability

For more edge cases, consult the [Click documentation](https://click.palletsprojects.com/) and [GitHub issues](https://github.com/pallets/click/issues).
