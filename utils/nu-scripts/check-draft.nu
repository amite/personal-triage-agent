#!/usr/bin/env nu

def main [
    --draft-id: int = 1  # Draft ID to check (default: 1)
] {
    uv run python -m scripts.check_draft ($draft_id | into string)
}

