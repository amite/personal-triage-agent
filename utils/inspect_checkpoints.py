"""
Utility script to inspect checkpoint database contents.
Usage: python -m utils.inspect_checkpoints
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
import msgpack
import logging

logger = logging.getLogger(__name__)

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


def get_checkpoint_state(
    thread_id: str, checkpoint_id: Optional[str] = None, db_path: str = "data/checkpoints.db"
) -> Dict[str, Any]:
    """Get deserialized AgentState from checkpoint.

    Args:
        thread_id: Thread ID to query
        checkpoint_id: Specific checkpoint ID (if None, gets latest)
        db_path: Path to checkpoint database

    Returns:
        Deserialized AgentState dict
    """
    db_file = Path(db_path)
    if not db_file.exists():
        logger.warning(f"Database not found at {db_path}")
        return {}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        if checkpoint_id:
            # Get specific checkpoint
            cursor.execute(
                """
                SELECT checkpoint, parent_checkpoint_id
                FROM checkpoints
                WHERE thread_id = ? AND checkpoint_id = ?
                """,
                (thread_id, checkpoint_id),
            )
        else:
            # Get latest checkpoint
            cursor.execute(
                """
                SELECT checkpoint, parent_checkpoint_id
                FROM checkpoints
                WHERE thread_id = ?
                ORDER BY rowid DESC
                LIMIT 1
                """,
                (thread_id,),
            )

        result = cursor.fetchone()
        if not result:
            logger.warning(f"No checkpoint found for thread {thread_id}")
            return {}

        checkpoint_blob, _ = result

        # Deserialize msgpack checkpoint
        state = msgpack.unpackb(checkpoint_blob, raw=False)
        logger.debug(f"Deserialized checkpoint for thread {thread_id}")
        return state
    except Exception as e:
        logger.error(f"Failed to deserialize checkpoint: {e}")
        return {}
    finally:
        conn.close()


def get_latest_checkpoint(thread_id: str, db_path: str = "data/checkpoints.db") -> Dict[str, Any]:
    """Get latest checkpoint state for a thread.

    Args:
        thread_id: Thread ID to query
        db_path: Path to checkpoint database

    Returns:
        Deserialized AgentState dict
    """
    return get_checkpoint_state(thread_id, checkpoint_id=None, db_path=db_path)


if __name__ == "__main__":
    inspect_database()
