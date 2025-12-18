#!/usr/bin/env python3
"""
Advanced Click CLI Template

Demonstrates advanced patterns including:
- Custom parameter types
- Command chaining
- Plugin architecture
- Configuration management
- Logging integration
"""

import click
import logging
from rich.console import Console
from pathlib import Path
import json
from typing import Optional

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Custom parameter types
class JsonType(click.ParamType):
    """Custom type for JSON parsing"""
    name = 'json'

    def convert(self, value, param, ctx):
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            self.fail(f'Invalid JSON: {e}', param, ctx)


class PathListType(click.ParamType):
    """Custom type for comma-separated paths"""
    name = 'pathlist'

    def convert(self, value, param, ctx):
        paths = [Path(p.strip()) for p in value.split(',')]
        for path in paths:
            if not path.exists():
                self.fail(f'Path does not exist: {path}', param, ctx)
        return paths


# Configuration class
class Config:
    """Application configuration"""

    def __init__(self):
        self.debug = False
        self.log_level = 'INFO'
        self.config_file = 'config.json'
        self._data = {}

    def load(self, config_file: Optional[str] = None):
        """Load configuration from file"""
        file_path = Path(config_file or self.config_file)
        if file_path.exists():
            with open(file_path) as f:
                self._data = json.load(f)
            logger.info(f"Loaded config from {file_path}")

    def get(self, key: str, default=None):
        """Get configuration value"""
        return self._data.get(key, default)

    def set(self, key: str, value):
        """Set configuration value"""
        self._data[key] = value

    def save(self):
        """Save configuration to file"""
        file_path = Path(self.config_file)
        with open(file_path, 'w') as f:
            json.dump(self._data, f, indent=2)
        logger.info(f"Saved config to {file_path}")


# Pass config between commands
pass_config = click.make_pass_decorator(Config, ensure=True)


# Main CLI group
@click.group(chain=True)
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config', type=click.Path(), default='config.json',
              help='Configuration file')
@click.option('--log-level',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              default='INFO',
              help='Logging level')
@click.version_option(version='2.0.0')
@pass_config
def cli(config: Config, debug: bool, config: str, log_level: str):
    """
    Advanced CLI with chaining and plugin support.

    Commands can be chained together:
        cli init process deploy
        cli config set key=value process --validate
    """
    config.debug = debug
    config.log_level = log_level
    config.config_file = config
    config.load()

    # Set logging level
    logger.setLevel(getattr(logging, log_level))

    if debug:
        console.print("[dim]Debug mode enabled[/dim]")


# Pipeline commands (chainable)
@cli.command()
@click.option('--template', type=click.Choice(['basic', 'advanced', 'api']),
              default='basic')
@pass_config
def init(config: Config, template: str):
    """Initialize project (chainable)"""
    console.print(f"[cyan]Initializing with {template} template...[/cyan]")
    config.set('template', template)
    return config


@cli.command()
@click.option('--validate', is_flag=True, help='Validate before processing')
@click.option('--parallel', is_flag=True, help='Process in parallel')
@pass_config
def process(config: Config, validate: bool, parallel: bool):
    """Process data (chainable)"""
    console.print("[cyan]Processing data...[/cyan]")

    if validate:
        console.print("[dim]Validating input...[/dim]")

    mode = "parallel" if parallel else "sequential"
    console.print(f"[dim]Processing mode: {mode}[/dim]")

    return config


@cli.command()
@click.argument('environment', type=click.Choice(['dev', 'staging', 'prod']))
@click.option('--dry-run', is_flag=True, help='Simulate deployment')
@pass_config
def deploy(config: Config, environment: str, dry_run: bool):
    """Deploy to environment (chainable)"""
    prefix = "[yellow][DRY RUN][/yellow] " if dry_run else ""
    console.print(f"{prefix}[cyan]Deploying to {environment}...[/cyan]")

    template = config.get('template', 'unknown')
    console.print(f"[dim]Template: {template}[/dim]")

    return config


# Advanced configuration commands
@cli.group()
def config():
    """Advanced configuration management"""
    pass


@config.command()
@click.argument('key')
@pass_config
def get(config: Config, key: str):
    """Get configuration value"""
    value = config.get(key)
    if value is not None:
        console.print(f"{key}: [green]{value}[/green]")
    else:
        console.print(f"[yellow]Key not found: {key}[/yellow]")


@config.command()
@click.argument('pair')
@pass_config
def set(config: Config, pair: str):
    """Set configuration (format: key=value)"""
    if '=' not in pair:
        raise click.BadParameter('Format must be key=value')

    key, value = pair.split('=', 1)
    config.set(key, value)
    config.save()
    console.print(f"[green]✓[/green] Set {key} = {value}")


@config.command()
@click.option('--format', type=click.Choice(['json', 'yaml', 'env']),
              default='json')
@pass_config
def export(config: Config, format: str):
    """Export configuration in different formats"""
    console.print(f"[cyan]Exporting config as {format}...[/cyan]")

    if format == 'json':
        output = json.dumps(config._data, indent=2)
    elif format == 'yaml':
        # Simplified YAML output
        output = '\n'.join(f"{k}: {v}" for k, v in config._data.items())
    else:  # env
        output = '\n'.join(f"{k.upper()}={v}" for k, v in config._data.items())

    console.print(output)


# Advanced data operations
@cli.group()
def data():
    """Data operations with advanced types"""
    pass


@data.command()
@click.option('--json-data', type=JsonType(), help='JSON data to import')
@click.option('--paths', type=PathListType(), help='Comma-separated paths')
@pass_config
def import_data(config: Config, json_data: Optional[dict], paths: Optional[list]):
    """Import data from various sources"""
    console.print("[cyan]Importing data...[/cyan]")

    if json_data:
        console.print(f"[dim]JSON data: {json_data}[/dim]")

    if paths:
        console.print(f"[dim]Processing {len(paths)} path(s)[/dim]")
        for path in paths:
            console.print(f"  - {path}")


@data.command()
@click.option('--input', type=click.File('r'), help='Input file')
@click.option('--output', type=click.File('w'), help='Output file')
@click.option('--format',
              type=click.Choice(['json', 'csv', 'xml']),
              default='json')
def transform(input, output, format):
    """Transform data between formats"""
    console.print(f"[cyan]Transforming data to {format}...[/cyan]")

    if input:
        data = input.read()
        console.print(f"[dim]Read {len(data)} bytes[/dim]")

    if output:
        # Would write transformed data here
        output.write('{}')  # Placeholder
        console.print("[green]✓[/green] Transformation complete")


# Plugin system
@cli.group()
def plugin():
    """Plugin management"""
    pass


@plugin.command()
@click.argument('plugin_name')
@click.option('--version', help='Plugin version')
def install(plugin_name: str, version: Optional[str]):
    """Install a plugin"""
    version_str = f"@{version}" if version else "@latest"
    console.print(f"[cyan]Installing plugin: {plugin_name}{version_str}...[/cyan]")
    console.print("[green]✓[/green] Plugin installed successfully")


@plugin.command()
def list():
    """List installed plugins"""
    console.print("[cyan]Installed Plugins:[/cyan]")
    # Placeholder plugin list
    plugins = [
        {"name": "auth-plugin", "version": "1.0.0", "status": "active"},
        {"name": "database-plugin", "version": "2.1.0", "status": "active"},
    ]
    for p in plugins:
        status_color = "green" if p["status"] == "active" else "yellow"
        console.print(f"  - {p['name']} ({p['version']}) [{status_color}]{p['status']}[/{status_color}]")


# Batch operations
@cli.command()
@click.argument('commands', nargs=-1, required=True)
@pass_config
def batch(config: Config, commands: tuple):
    """Execute multiple commands in batch"""
    console.print(f"[cyan]Executing {len(commands)} command(s)...[/cyan]")

    for i, cmd in enumerate(commands, 1):
        console.print(f"[dim]{i}. {cmd}[/dim]")
        # Would execute actual commands here

    console.print("[green]✓[/green] Batch execution completed")


if __name__ == '__main__':
    cli()
