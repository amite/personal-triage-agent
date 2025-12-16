#!/usr/bin/env nu

def main [
    --thread-id: string  # Optional thread ID to filter by (omit to list all drafts)
] {
    let output = if $thread_id != null {
        uv run python -m scripts.list_drafts --json ($thread_id) | from json
    } else {
        uv run python -m scripts.list_drafts --json | from json
    }
    
    $output 
    | update subject {|row| 
        let subject = ($row.subject | default "")
        if ($subject | str length) > 60 {
            ($subject | str substring 0..60) + "..."
        } else {
            $subject
        }
    }
    | select id thread_id subject created_at status 
    | table
}

