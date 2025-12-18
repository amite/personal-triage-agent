#!/usr/bin/env python3
"""
Nested Commands Click Template

Demonstrates command groups, nested subcommands, and context sharing.
"""

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version='1.0.0')
@click.pass_context
def cli(ctx):
    """
    A powerful CLI tool with nested commands.

    Example:
        python cli.py init --template basic
        python cli.py deploy production --mode safe
        python cli.py config get api-key
    """
    ctx.ensure_object(dict)
    ctx.obj['console'] = console


@cli.command()
@click.option('--template', '-t', default='basic',
              type=click.Choice(['basic', 'advanced', 'minimal']),
              help='Project template')
@click.pass_context
def init(ctx, template):
    """Initialize a new project"""
    console = ctx.obj['console']
    console.print(f"[green]✓[/green] Initializing project with {template} template...")


@cli.command()
@click.argument('environment', type=click.Choice(['dev', 'staging', 'production']))
@click.option('--force', '-f', is_flag=True, help='Force deployment')
@click.option('--mode', '-m',
              type=click.Choice(['fast', 'safe', 'rollback']),
              default='safe',
              help='Deployment mode')
@click.pass_context
def deploy(ctx, environment, force, mode):
    """Deploy to specified environment"""
    console = ctx.obj['console']
    console.print(f"[cyan]Deploying to {environment} in {mode} mode[/cyan]")
    if force:
        console.print("[yellow]⚠ Force mode enabled[/yellow]")


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
    # Placeholder for actual config retrieval
    value = "example_value"
    console.print(f"[dim]Config[/dim] {key}: [green]{value}[/green]")


@config.command()
@click.argument('key')
@click.argument('value')
@click.pass_context
def set(ctx, key, value):
    """Set configuration value"""
    console = ctx.obj['console']
    # Placeholder for actual config storage
    console.print(f"[green]✓[/green] Set {key} = {value}")


@config.command()
@click.pass_context
def list(ctx):
    """List all configuration settings"""
    console = ctx.obj['console']
    console.print("[cyan]Configuration Settings:[/cyan]")
    # Placeholder for actual config listing
    console.print("  api-key: [dim]***hidden***[/dim]")
    console.print("  debug: [green]true[/green]")


@cli.group()
def database():
    """Database management commands"""
    pass


@database.command()
@click.option('--create-tables', is_flag=True, help='Create tables')
@click.pass_context
def migrate(ctx, create_tables):
    """Run database migrations"""
    console = ctx.obj['console']
    console.print("[cyan]Running migrations...[/cyan]")
    if create_tables:
        console.print("[green]✓[/green] Tables created")


@database.command()
@click.option('--confirm', is_flag=True, help='Confirm reset')
@click.pass_context
def reset(ctx, confirm):
    """Reset database (destructive)"""
    console = ctx.obj['console']
    if not confirm:
        console.print("[yellow]⚠ Use --confirm to proceed[/yellow]")
        return
    console.print("[red]Resetting database...[/red]")


if __name__ == '__main__':
    cli(obj={})
