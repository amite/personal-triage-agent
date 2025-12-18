# Complete Click CLI Example

A production-ready Click CLI demonstrating all major patterns and best practices.

## Full Implementation

```python
#!/usr/bin/env python3
"""
Production-ready Click CLI with all major patterns.

Features:
- Command groups and nested subcommands
- Options and arguments with validation
- Context sharing across commands
- Error handling and colored output
- Configuration management
- Environment-specific commands
"""

import click
from rich.console import Console
from pathlib import Path
import json

console = Console()


# Custom validators
def validate_email(ctx, param, value):
    """Validate email format"""
    import re
    if value and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
        raise click.BadParameter('Invalid email format')
    return value


# Main CLI group
@click.group()
@click.version_option(version='1.0.0')
@click.option('--config', type=click.Path(), default='config.json',
              help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """
    A powerful CLI tool for project management.

    Examples:
        cli init --template basic
        cli deploy production --mode safe
        cli config get api-key
        cli database migrate --create-tables
    """
    ctx.ensure_object(dict)
    ctx.obj['console'] = console
    ctx.obj['verbose'] = verbose
    ctx.obj['config_file'] = config

    if verbose:
        console.print(f"[dim]Config file: {config}[/dim]")


# Initialize command
@cli.command()
@click.option('--template', '-t',
              type=click.Choice(['basic', 'advanced', 'minimal']),
              default='basic',
              help='Project template')
@click.option('--name', prompt=True, help='Project name')
@click.option('--description', prompt=True, help='Project description')
@click.pass_context
def init(ctx, template, name, description):
    """Initialize a new project"""
    console = ctx.obj['console']
    verbose = ctx.obj['verbose']

    console.print(f"[cyan]Initializing project: {name}[/cyan]")
    console.print(f"[dim]Template: {template}[/dim]")
    console.print(f"[dim]Description: {description}[/dim]")

    # Create project structure
    project_dir = Path(name)
    if project_dir.exists():
        console.print(f"[red]✗[/red] Directory already exists: {name}")
        raise click.Abort()

    try:
        project_dir.mkdir(parents=True)
        (project_dir / 'src').mkdir()
        (project_dir / 'tests').mkdir()
        (project_dir / 'docs').mkdir()

        # Create config file
        config = {
            'name': name,
            'description': description,
            'template': template,
            'version': '1.0.0'
        }
        with open(project_dir / 'config.json', 'w') as f:
            json.dump(config, f, indent=2)

        console.print(f"[green]✓[/green] Project initialized successfully!")

        if verbose:
            console.print(f"[dim]Created directories: src/, tests/, docs/[/dim]")
            console.print(f"[dim]Created config.json[/dim]")

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise click.Abort()


# Deploy command
@cli.command()
@click.argument('environment',
                type=click.Choice(['dev', 'staging', 'production']))
@click.option('--force', '-f', is_flag=True, help='Force deployment')
@click.option('--mode', '-m',
              type=click.Choice(['fast', 'safe', 'rollback']),
              default='safe',
              help='Deployment mode')
@click.option('--skip-tests', is_flag=True, help='Skip test execution')
@click.pass_context
def deploy(ctx, environment, force, mode, skip_tests):
    """Deploy to specified environment"""
    console = ctx.obj['console']
    verbose = ctx.obj['verbose']

    console.print(f"[cyan]Deploying to {environment} in {mode} mode[/cyan]")

    if force:
        console.print("[yellow]⚠ Force mode enabled - skipping safety checks[/yellow]")

    # Pre-deployment checks
    if not skip_tests and not force:
        console.print("[dim]Running tests...[/dim]")
        # Simulate test execution
        if verbose:
            console.print("[green]✓[/green] All tests passed")

    # Deployment simulation
    steps = [
        "Building artifacts",
        "Uploading to server",
        "Running migrations",
        "Restarting services",
        "Verifying deployment"
    ]

    for step in steps:
        console.print(f"[dim]- {step}...[/dim]")

    console.print(f"[green]✓[/green] Deployment completed successfully!")

    if mode == 'safe':
        console.print("[dim]Rollback available for 24 hours[/dim]")


# Config group
@cli.group()
def config():
    """Manage configuration settings"""
    pass


@config.command()
@click.argument('key')
@click.pass_context
def get(ctx, key):
    """Get configuration value"""
    console = ctx.obj['console']
    config_file = ctx.obj['config_file']

    try:
        if Path(config_file).exists():
            with open(config_file) as f:
                config_data = json.load(f)
                if key in config_data:
                    console.print(f"[dim]Config[/dim] {key}: [green]{config_data[key]}[/green]")
                else:
                    console.print(f"[yellow]Key not found: {key}[/yellow]")
        else:
            console.print(f"[red]Config file not found: {config_file}[/red]")
    except Exception as e:
        console.print(f"[red]Error reading config: {e}[/red]")


@config.command()
@click.argument('key')
@click.argument('value')
@click.pass_context
def set(ctx, key, value):
    """Set configuration value"""
    console = ctx.obj['console']
    config_file = ctx.obj['config_file']

    try:
        config_data = {}
        if Path(config_file).exists():
            with open(config_file) as f:
                config_data = json.load(f)

        config_data[key] = value

        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        console.print(f"[green]✓[/green] Set {key} = {value}")
    except Exception as e:
        console.print(f"[red]Error writing config: {e}[/red]")


@config.command()
@click.pass_context
def list(ctx):
    """List all configuration settings"""
    console = ctx.obj['console']
    config_file = ctx.obj['config_file']

    try:
        if Path(config_file).exists():
            with open(config_file) as f:
                config_data = json.load(f)
                console.print("[cyan]Configuration Settings:[/cyan]")
                for key, value in config_data.items():
                    console.print(f"  {key}: [green]{value}[/green]")
        else:
            console.print("[yellow]No configuration file found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error reading config: {e}[/red]")


# Database group
@cli.group()
def database():
    """Database management commands"""
    pass


@database.command()
@click.option('--create-tables', is_flag=True, help='Create tables')
@click.option('--seed-data', is_flag=True, help='Seed initial data')
@click.pass_context
def migrate(ctx, create_tables, seed_data):
    """Run database migrations"""
    console = ctx.obj['console']

    console.print("[cyan]Running migrations...[/cyan]")

    if create_tables:
        console.print("[dim]- Creating tables...[/dim]")
        console.print("[green]✓[/green] Tables created")

    if seed_data:
        console.print("[dim]- Seeding data...[/dim]")
        console.print("[green]✓[/green] Data seeded")

    console.print("[green]✓[/green] Migrations completed")


@database.command()
@click.option('--confirm', is_flag=True,
              prompt='This will delete all data. Continue?',
              help='Confirm reset')
@click.pass_context
def reset(ctx, confirm):
    """Reset database (destructive operation)"""
    console = ctx.obj['console']

    if not confirm:
        console.print("[yellow]Operation cancelled[/yellow]")
        raise click.Abort()

    console.print("[red]Resetting database...[/red]")
    console.print("[dim]- Dropping tables...[/dim]")
    console.print("[dim]- Clearing cache...[/dim]")
    console.print("[green]✓[/green] Database reset completed")


# User management group
@cli.group()
def user():
    """User management commands"""
    pass


@user.command()
@click.option('--email', callback=validate_email, prompt=True,
              help='User email address')
@click.option('--name', prompt=True, help='User full name')
@click.option('--role',
              type=click.Choice(['admin', 'user', 'guest']),
              default='user',
              help='User role')
@click.pass_context
def create(ctx, email, name, role):
    """Create a new user"""
    console = ctx.obj['console']

    console.print(f"[cyan]Creating user: {name}[/cyan]")
    console.print(f"[dim]Email: {email}[/dim]")
    console.print(f"[dim]Role: {role}[/dim]")

    console.print(f"[green]✓[/green] User created successfully")


@user.command()
@click.argument('email')
@click.pass_context
def delete(ctx, email):
    """Delete a user"""
    console = ctx.obj['console']

    if not click.confirm(f"Delete user {email}?"):
        console.print("[yellow]Operation cancelled[/yellow]")
        return

    console.print(f"[cyan]Deleting user: {email}[/cyan]")
    console.print(f"[green]✓[/green] User deleted")


# Error handling wrapper
def main():
    """Main entry point with error handling"""
    try:
        cli(obj={})
    except click.Abort:
        console.print("[yellow]Operation aborted[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise


if __name__ == '__main__':
    main()
```

## Usage Examples

### Initialize a project
```bash
python cli.py init --template advanced --name myproject --description "My awesome project"
```

### Deploy to production
```bash
python cli.py deploy production --mode safe
python cli.py deploy staging --force --skip-tests
```

### Configuration management
```bash
python cli.py config set api-key abc123
python cli.py config get api-key
python cli.py config list
```

### Database operations
```bash
python cli.py database migrate --create-tables --seed-data
python cli.py database reset --confirm
```

### User management
```bash
python cli.py user create --email user@example.com --name "John Doe" --role admin
python cli.py user delete user@example.com
```

### With verbose output
```bash
python cli.py --verbose deploy production
```

### With custom config file
```bash
python cli.py --config /path/to/config.json config list
```

## Key Features Demonstrated

1. **Command Groups**: Organized commands into logical groups (config, database, user)
2. **Context Sharing**: Using @click.pass_context to share state
3. **Input Validation**: Custom validators for email, built-in validators for choices
4. **Colored Output**: Using Rich console for beautiful output
5. **Error Handling**: Graceful error handling and user feedback
6. **Interactive Prompts**: Using prompt=True for interactive input
7. **Confirmation Dialogs**: Using click.confirm() for dangerous operations
8. **File Operations**: Reading/writing JSON configuration files
9. **Flags and Options**: Boolean flags, default values, short flags
10. **Version Information**: @click.version_option() decorator

## Best Practices Applied

- Clear help text for all commands and options
- Sensible defaults for options
- Validation for user inputs
- Colored output for better UX
- Verbose mode for debugging
- Confirmation for destructive operations
- Proper error handling and messages
- Clean separation of concerns with command groups
- Context object for sharing state
