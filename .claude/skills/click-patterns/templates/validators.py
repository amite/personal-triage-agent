#!/usr/bin/env python3
"""
Click Custom Validators Template

Demonstrates custom parameter validation, callbacks, and type conversion.
"""

import click
import re
from pathlib import Path
from rich.console import Console

console = Console()


# Custom validator callbacks
def validate_email(ctx, param, value):
    """Validate email format"""
    if value and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
        raise click.BadParameter('Invalid email format')
    return value


def validate_port(ctx, param, value):
    """Validate port number"""
    if value < 1 or value > 65535:
        raise click.BadParameter('Port must be between 1 and 65535')
    return value


def validate_path_exists(ctx, param, value):
    """Validate that path exists"""
    if value and not Path(value).exists():
        raise click.BadParameter(f'Path does not exist: {value}')
    return value


def validate_url(ctx, param, value):
    """Validate URL format"""
    if value and not re.match(r'^https?://[^\s]+$', value):
        raise click.BadParameter('Invalid URL format (must start with http:// or https://)')
    return value


# Custom Click types
class CommaSeparatedList(click.ParamType):
    """Custom type for comma-separated lists"""
    name = 'comma-list'

    def convert(self, value, param, ctx):
        if isinstance(value, list):
            return value
        try:
            return [item.strip() for item in value.split(',') if item.strip()]
        except Exception:
            self.fail(f'{value} is not a valid comma-separated list', param, ctx)


class EnvironmentVariable(click.ParamType):
    """Custom type for environment variables"""
    name = 'env-var'

    def convert(self, value, param, ctx):
        if not re.match(r'^[A-Z_][A-Z0-9_]*$', value):
            self.fail(f'{value} is not a valid environment variable name', param, ctx)
        return value


@click.group()
def cli():
    """CLI with custom validators"""
    pass


@cli.command()
@click.option('--email', callback=validate_email, required=True, help='User email address')
@click.option('--age', type=click.IntRange(0, 150), required=True, help='User age')
@click.option('--username', type=click.STRING, required=True,
              help='Username (3-20 characters)',
              callback=lambda ctx, param, value: value if 3 <= len(value) <= 20
              else ctx.fail('Username must be 3-20 characters'))
def create_user(email, age, username):
    """Create a new user with validation"""
    console.print(f"[green]✓[/green] User created: {username} ({email}), age {age}")


@cli.command()
@click.option('--port', type=int, callback=validate_port, default=8080, help='Server port')
@click.option('--host', default='localhost', help='Server host')
@click.option('--workers', type=click.IntRange(1, 32), default=4, help='Number of workers')
@click.option('--ssl', is_flag=True, help='Enable SSL')
def start_server(port, host, workers, ssl):
    """Start server with validated parameters"""
    protocol = 'https' if ssl else 'http'
    console.print(f"[cyan]Starting server at {protocol}://{host}:{port}[/cyan]")
    console.print(f"[dim]Workers: {workers}[/dim]")


@cli.command()
@click.option('--config', type=click.Path(exists=True, dir_okay=False),
              callback=validate_path_exists, required=True, help='Config file path')
@click.option('--output', type=click.Path(dir_okay=False), required=True, help='Output file path')
@click.option('--format', type=click.Choice(['json', 'yaml', 'toml']), default='json',
              help='Output format')
def convert_config(config, output, format):
    """Convert configuration file"""
    console.print(f"[cyan]Converting {config} to {format} format[/cyan]")
    console.print(f"[green]✓[/green] Output: {output}")


@cli.command()
@click.option('--url', callback=validate_url, required=True, help='API URL')
@click.option('--method', type=click.Choice(['GET', 'POST', 'PUT', 'DELETE']),
              default='GET', help='HTTP method')
@click.option('--headers', type=CommaSeparatedList(), help='Headers (comma-separated key:value)')
@click.option('--timeout', type=click.FloatRange(0.1, 300.0), default=30.0,
              help='Request timeout in seconds')
def api_call(url, method, headers, timeout):
    """Make API call with validation"""
    console.print(f"[cyan]{method} {url}[/cyan]")
    console.print(f"[dim]Timeout: {timeout}s[/dim]")
    if headers:
        console.print(f"[dim]Headers: {headers}[/dim]")


@cli.command()
@click.option('--env-var', type=EnvironmentVariable(), required=True,
              help='Environment variable name')
@click.option('--value', required=True, help='Environment variable value')
@click.option('--scope', type=click.Choice(['user', 'system', 'project']),
              default='user', help='Variable scope')
def set_env(env_var, value, scope):
    """Set environment variable with validation"""
    console.print(f"[green]✓[/green] Set {env_var}={value} (scope: {scope})")


@cli.command()
@click.option('--min', type=float, required=True, help='Minimum value')
@click.option('--max', type=float, required=True, help='Maximum value')
@click.option('--step', type=click.FloatRange(0.01, None), default=1.0, help='Step size')
def generate_range(min, max, step):
    """Generate numeric range with validation"""
    if min >= max:
        raise click.BadParameter('min must be less than max')

    count = int((max - min) / step) + 1
    console.print(f"[cyan]Generating range from {min} to {max} (step: {step})[/cyan]")
    console.print(f"[dim]Total values: {count}[/dim]")


# Example combining multiple validators
@cli.command()
@click.option('--name', required=True, help='Project name',
              callback=lambda ctx, param, value: value.lower().replace(' ', '-'))
@click.option('--tags', type=CommaSeparatedList(), help='Project tags (comma-separated)')
@click.option('--priority', type=click.IntRange(1, 10), default=5, help='Priority (1-10)')
@click.option('--template', type=click.Path(exists=True), help='Template directory')
def create_project(name, tags, priority, template):
    """Create project with multiple validators"""
    console.print(f"[green]✓[/green] Project created: {name}")
    console.print(f"[dim]Priority: {priority}[/dim]")
    if tags:
        console.print(f"[dim]Tags: {', '.join(tags)}[/dim]")
    if template:
        console.print(f"[dim]Template: {template}[/dim]")


if __name__ == '__main__':
    cli()
