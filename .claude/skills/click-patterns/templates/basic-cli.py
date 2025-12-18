#!/usr/bin/env python3
"""
Basic Click CLI Template

A simple single-command CLI using Click framework.
"""

import click
from rich.console import Console

console = Console()


@click.command()
@click.version_option(version='1.0.0')
@click.option('--name', '-n', default='World', help='Name to greet')
@click.option('--count', '-c', default=1, type=int, help='Number of greetings')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def cli(name, count, verbose):
    """
    A simple greeting CLI tool.

    Example:
        python cli.py --name Alice --count 3
    """
    if verbose:
        console.print(f"[dim]Running with name={name}, count={count}[/dim]")

    for i in range(count):
        console.print(f"[green]Hello, {name}![/green]")

    if verbose:
        console.print(f"[dim]Completed {count} greeting(s)[/dim]")


if __name__ == '__main__':
    cli()
