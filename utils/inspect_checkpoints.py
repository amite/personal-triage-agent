"""
Utility script to inspect checkpoint database contents.
Usage: python -m utils.inspect_checkpoints
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table

console = Console()


def inspect_database(db_path: str = "data/checkpoints.db") -> None:
    """Inspect and display checkpoint database contents"""

    db_file = Path(db_path)
    if not db_file.exists():
        console.print("[yellow]No checkpoint database found.[/yellow]")
        console.print(f"[dim]Expected at: {db_path}[/dim]")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all threads
    console.print("[bold cyan]Checkpoint Database Inspection[/bold cyan]\n")

    # Thread summary
    cursor.execute("""
        SELECT thread_id, COUNT(*) as checkpoint_count
        FROM checkpoints
        GROUP BY thread_id
        ORDER BY MAX(rowid) DESC
    """)

    threads = cursor.fetchall()

    if not threads:
        console.print("[yellow]No checkpoints found in database.[/yellow]")
        conn.close()
        return

    # Display thread summary table
    table = Table(title=f"Threads in Database ({len(threads)} total)")
    table.add_column("Thread ID", style="cyan")
    table.add_column("Checkpoints", style="magenta")

    for thread_id, count in threads:
        table.add_row(
            thread_id[:16] + "..." if len(thread_id) > 16 else thread_id,
            str(count),
        )

    console.print(table)

    # Database size
    cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
    result = cursor.fetchone()
    if result:
        size_bytes = result[0]
        size_mb = size_bytes / (1024 * 1024)
        console.print(f"\n[dim]Database size: {size_mb:.2f} MB ({size_bytes:,} bytes)[/dim]")

    conn.close()


def get_thread_history(thread_id: str, db_path: str = "data/checkpoints.db") -> List[Dict[str, Any]]:
    """Get checkpoint history for a specific thread"""

    db_file = Path(db_path)
    if not db_file.exists():
        console.print(f"[yellow]Database not found at {db_path}[/yellow]")
        return []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT checkpoint_id, parent_checkpoint_id
        FROM checkpoints
        WHERE thread_id = ?
        ORDER BY rowid ASC
    """, (thread_id,))

    checkpoints = cursor.fetchall()
    conn.close()

    return [
        {
            "checkpoint_id": cp[0],
            "parent_checkpoint_id": cp[1],
        }
        for cp in checkpoints
    ]


def get_all_thread_ids(db_path: str = "data/checkpoints.db") -> List[str]:
    """Get all unique thread IDs from the database"""

    db_file = Path(db_path)
    if not db_file.exists():
        return []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY MAX(rowid) DESC")
    threads = [row[0] for row in cursor.fetchall()]
    conn.close()

    return threads


if __name__ == "__main__":
    inspect_database()
