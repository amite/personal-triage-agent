# Click Framework Common Patterns

Best practices and common patterns for building production-ready Click CLIs.

## Table of Contents

1. [Command Structure Patterns](#command-structure-patterns)
2. [Parameter Patterns](#parameter-patterns)
3. [Validation Patterns](#validation-patterns)
4. [Error Handling Patterns](#error-handling-patterns)
5. [Output Patterns](#output-patterns)
6. [Configuration Patterns](#configuration-patterns)
7. [Testing Patterns](#testing-patterns)

---

## Command Structure Patterns

### Single Command CLI

For simple tools with one main function:

```python
@click.command()
@click.option('--name', default='World')
def hello(name):
    """Simple greeting CLI"""
    click.echo(f'Hello, {name}!')
```

### Command Group Pattern

For CLIs with multiple related commands:

```python
@click.group()
def cli():
    """Main CLI entry point"""
    pass

@cli.command()
def cmd1():
    """First command"""
    pass

@cli.command()
def cmd2():
    """Second command"""
    pass
```

### Nested Command Groups

For complex CLIs with logical grouping:

```python
@click.group()
def cli():
    """Main CLI"""
    pass

@cli.group()
def database():
    """Database commands"""
    pass

@database.command()
def migrate():
    """Run migrations"""
    pass

@database.command()
def reset():
    """Reset database"""
    pass
```

### Context-Aware Commands

Share state across commands:

```python
@click.group()
@click.pass_context
def cli(ctx):
    """Main CLI with shared context"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config()

@cli.command()
@click.pass_context
def deploy(ctx):
    """Use shared config"""
    config = ctx.obj['config']
```

---

## Parameter Patterns

### Options vs Arguments

**Options** (optional, named):
```python
@click.option('--name', '-n', default='World', help='Name to greet')
@click.option('--count', '-c', default=1, type=int)
```

**Arguments** (required, positional):
```python
@click.argument('filename')
@click.argument('output', type=click.Path())
```

### Required Options

```python
@click.option('--api-key', required=True, help='API key (required)')
@click.option('--config', required=True, type=click.Path(exists=True))
```

### Multiple Values

```python
# Multiple option values
@click.option('--tag', multiple=True, help='Tags (can specify multiple times)')
def command(tag):
    for t in tag:
        click.echo(t)

# Variable arguments
@click.argument('files', nargs=-1, type=click.Path(exists=True))
def process(files):
    for f in files:
        click.echo(f)
```

### Environment Variables

```python
@click.option('--api-key', envvar='API_KEY', help='API key (from env: API_KEY)')
@click.option('--debug', envvar='DEBUG', is_flag=True)
```

### Interactive Prompts

```python
@click.option('--name', prompt=True, help='Your name')
@click.option('--password', prompt=True, hide_input=True)
@click.option('--confirm', prompt='Continue?', confirmation_prompt=True)
```

---

## Validation Patterns

### Built-in Validators

```python
# Choice validation
@click.option('--env', type=click.Choice(['dev', 'staging', 'prod']))

# Range validation
@click.option('--port', type=click.IntRange(1, 65535))
@click.option('--rate', type=click.FloatRange(0.0, 1.0))

# Path validation
@click.option('--input', type=click.Path(exists=True, dir_okay=False))
@click.option('--output', type=click.Path(writable=True))
@click.option('--dir', type=click.Path(exists=True, file_okay=False))
```

### Custom Validators with Callbacks

```python
def validate_email(ctx, param, value):
    """Validate email format"""
    import re
    if value and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
        raise click.BadParameter('Invalid email format')
    return value

@click.option('--email', callback=validate_email)
def command(email):
    pass
```

### Custom Click Types

```python
class EmailType(click.ParamType):
    """Custom email type"""
    name = 'email'

    def convert(self, value, param, ctx):
        import re
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
            self.fail(f'{value} is not a valid email', param, ctx)
        return value

@click.option('--email', type=EmailType())
def command(email):
    pass
```

### Conditional Validation

```python
@click.command()
@click.option('--ssl', is_flag=True)
@click.option('--cert', type=click.Path(exists=True))
@click.option('--key', type=click.Path(exists=True))
def server(ssl, cert, key):
    """Start server with SSL validation"""
    if ssl and (not cert or not key):
        raise click.UsageError('SSL requires --cert and --key')
```

---

## Error Handling Patterns

### Graceful Error Handling

```python
@click.command()
def command():
    """Command with error handling"""
    try:
        # Operation that might fail
        result = risky_operation()
    except FileNotFoundError as e:
        raise click.FileError(str(e))
    except Exception as e:
        raise click.ClickException(f'Operation failed: {e}')
```

### Custom Exit Codes

```python
@click.command()
def deploy():
    """Deploy with custom exit codes"""
    if not check_prerequisites():
        ctx = click.get_current_context()
        ctx.exit(1)

    if not deploy_application():
        ctx = click.get_current_context()
        ctx.exit(2)

    click.echo('Deployment successful')
    ctx = click.get_current_context()
    ctx.exit(0)
```

### Confirmation for Dangerous Operations

```python
@click.command()
@click.option('--force', is_flag=True, help='Skip confirmation')
def delete(force):
    """Delete with confirmation"""
    if not force:
        click.confirm('This will delete all data. Continue?', abort=True)

    # Proceed with deletion
    click.echo('Deleting...')
```

---

## Output Patterns

### Colored Output with Click

```python
@click.command()
def status():
    """Show status with colors"""
    click.secho('Success!', fg='green', bold=True)
    click.secho('Warning!', fg='yellow')
    click.secho('Error!', fg='red', bold=True)
    click.echo(click.style('Info', fg='cyan'))
```

### Rich Console Integration

```python
from rich.console import Console
console = Console()

@click.command()
def deploy():
    """Deploy with Rich output"""
    console.print('[cyan]Starting deployment...[/cyan]')
    console.print('[green]✓[/green] Build successful')
    console.print('[yellow]⚠[/yellow] Warning: Cache cleared')
```

### Progress Bars

```python
@click.command()
@click.argument('files', nargs=-1)
def process(files):
    """Process with progress bar"""
    with click.progressbar(files, label='Processing files') as bar:
        for file in bar:
            # Process file
            time.sleep(0.1)
```

### Verbose Mode Pattern

```python
@click.command()
@click.option('--verbose', '-v', is_flag=True)
def command(verbose):
    """Command with verbose output"""
    click.echo('Starting operation...')

    if verbose:
        click.echo('Debug: Loading configuration')
        click.echo('Debug: Connecting to database')

    # Main operation
    click.echo('Operation completed')
```

---

## Configuration Patterns

### Configuration File Loading

```python
import json
from pathlib import Path

@click.group()
@click.option('--config', type=click.Path(), default='config.json')
@click.pass_context
def cli(ctx, config):
    """CLI with config file"""
    ctx.ensure_object(dict)
    if Path(config).exists():
        with open(config) as f:
            ctx.obj['config'] = json.load(f)
    else:
        ctx.obj['config'] = {}

@cli.command()
@click.pass_context
def deploy(ctx):
    """Use config"""
    config = ctx.obj['config']
    api_key = config.get('api_key')
```

### Environment-Based Configuration

```python
@click.command()
@click.option('--env', type=click.Choice(['dev', 'staging', 'prod']), default='dev')
def deploy(env):
    """Deploy with environment config"""
    config_file = f'config.{env}.json'
    with open(config_file) as f:
        config = json.load(f)
    # Use environment-specific config
```

### Configuration Priority

```python
def get_config_value(ctx, param_value, env_var, config_key, default):
    """Get value with priority: param > env > config > default"""
    if param_value:
        return param_value
    if env_var in os.environ:
        return os.environ[env_var]
    if config_key in ctx.obj['config']:
        return ctx.obj['config'][config_key]
    return default
```

---

## Testing Patterns

### Basic Testing with CliRunner

```python
from click.testing import CliRunner
import pytest

def test_command():
    """Test Click command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output

def test_command_with_args():
    """Test with arguments"""
    runner = CliRunner()
    result = runner.invoke(cli, ['deploy', 'production'])
    assert result.exit_code == 0
    assert 'Deploying to production' in result.output
```

### Testing with Temporary Files

```python
def test_with_file():
    """Test with temporary file"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('test.txt', 'w') as f:
            f.write('test content')

        result = runner.invoke(cli, ['process', 'test.txt'])
        assert result.exit_code == 0
```

### Testing Interactive Prompts

```python
def test_interactive():
    """Test interactive prompts"""
    runner = CliRunner()
    result = runner.invoke(cli, ['create'], input='username\npassword\n')
    assert result.exit_code == 0
    assert 'User created' in result.output
```

### Testing Environment Variables

```python
def test_with_env():
    """Test with environment variables"""
    runner = CliRunner()
    result = runner.invoke(cli, ['deploy'], env={'API_KEY': 'test123'})
    assert result.exit_code == 0
```

---

## Advanced Patterns

### Plugin System

```python
@click.group()
def cli():
    """CLI with plugin support"""
    pass

# Allow plugins to register commands
def register_plugin(group, plugin_name):
    """Register plugin commands"""
    plugin_module = importlib.import_module(f'plugins.{plugin_name}')
    for name, cmd in plugin_module.commands.items():
        group.add_command(cmd, name)
```

### Lazy Loading

```python
class LazyGroup(click.Group):
    """Lazy load commands"""

    def get_command(self, ctx, cmd_name):
        """Load command on demand"""
        module = importlib.import_module(f'commands.{cmd_name}')
        return module.cli

@click.command(cls=LazyGroup)
def cli():
    """CLI with lazy loading"""
    pass
```

### Middleware Pattern

```python
def with_database(f):
    """Decorator to inject database connection"""
    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        ctx.obj['db'] = connect_database()
        try:
            return f(*args, **kwargs)
        finally:
            ctx.obj['db'].close()
    return wrapper

@cli.command()
@with_database
@click.pass_context
def query(ctx):
    """Command with database"""
    db = ctx.obj['db']
```

---

## Summary

These patterns cover the most common use cases for Click CLIs:

1. **Structure**: Choose between single command, command group, or nested groups
2. **Parameters**: Use options for named parameters, arguments for positional
3. **Validation**: Leverage built-in validators or create custom ones
4. **Errors**: Handle errors gracefully with proper messages
5. **Output**: Use colored output and progress bars for better UX
6. **Config**: Load configuration from files with proper priority
7. **Testing**: Test thoroughly with CliRunner

For more patterns and advanced usage, see the [Click documentation](https://click.palletsprojects.com/).
