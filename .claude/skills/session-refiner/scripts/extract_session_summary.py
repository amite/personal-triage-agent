#!/usr/bin/env python3
"""
Session Refiner: Extracts key technical decisions, resolved bugs, and TODOs
from a long conversation to create a compact markdown summary.

Usage:
    python extract_session_summary.py <input_file> [--output summary.md] [--max-tokens 5000]

Input format: Plain text conversation (copy-paste from chat)
Output: Compact markdown summary suitable for starting a fresh session
"""

import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class SessionExtractor:
    """Extract and summarize key information from a technical session."""

    def __init__(self, max_tokens=5000):
        self.max_tokens = max_tokens
        self.decisions = []
        self.bugs = []
        self.todos = []
        self.code_snippets = defaultdict(list)
        self.key_findings = []

    def extract_from_text(self, text):
        """Parse conversation and extract key information."""
        lines = text.split('\n')

        # Extract explicit TODOs (marked with "TODO", "FIXME", "- [ ]", etc.)
        self._extract_todos(lines)

        # Extract bug fixes and resolutions
        self._extract_bug_resolutions(lines)

        # Extract technical decisions
        self._extract_decisions(lines)

        # Extract code snippets (marked with triple backticks or indentation)
        self._extract_code_snippets(lines)

        # Extract key findings
        self._extract_key_findings(lines)

    def _extract_todos(self, lines):
        """Extract TODO items, including checkbox lists."""
        todo_patterns = [
            r'(?:^|\s)(?:TODO|FIXME|XXX|HACK):\s*(.+)',
            r'^\s*-\s*\[\s*\]\s+(.+)',  # Unchecked boxes
            r'^\s*\d+\.\s+\[.*\]\s+(.+)',  # Numbered unchecked
        ]

        for line in lines:
            for pattern in todo_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and match.group(1) not in self.todos:
                    self.todos.append(match.group(1).strip())

    def _extract_bug_resolutions(self, lines):
        """Extract bug fixes and resolutions."""
        bug_patterns = [
            r'(?:Fixed|Resolved|Fixed bug|Bug fix):\s*(.+)',
            r'(?:Issue|Error|Problem).*?(?:was|is).*?(?:fixed|resolved):\s*(.+)',
        ]

        for i, line in enumerate(lines):
            for pattern in bug_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and match.group(1) not in self.bugs:
                    self.bugs.append({
                        'title': match.group(1).strip(),
                        'context': ' '.join(lines[max(0, i-1):min(len(lines), i+2)])
                    })

    def _extract_decisions(self, lines):
        """Extract technical decisions."""
        decision_patterns = [
            r'(?:Decided to|We will|Using|Chose|Selected|going with)\s+(.+?)(?:\.|$)',
            r'(?:Architecture|Design|Pattern|Approach):\s*(.+?)(?:\.|$)',
            r'(?:using|using )(.+?)\s+(?:for|because|to)',
        ]

        for line in lines:
            for pattern in decision_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and match.group(1).strip():
                    decision = match.group(1).strip()
                    if decision not in [d['title'] for d in self.decisions] and len(decision) > 3:
                        self.decisions.append({
                            'title': decision,
                            'context': line.strip()
                        })

    def _extract_code_snippets(self, lines):
        """Extract code blocks and important code references."""
        in_code_block = False
        current_snippet = []
        language = None

        for line in lines:
            # Detect code block markers
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    if current_snippet:
                        snippet_text = '\n'.join(current_snippet)
                        if language not in self.code_snippets or len(self.code_snippets[language]) < 3:
                            self.code_snippets[language].append(snippet_text)
                    in_code_block = False
                    current_snippet = []
                else:
                    # Start of code block
                    in_code_block = True
                    language = line.strip()[3:].strip() or 'text'
            elif in_code_block and line.strip():
                current_snippet.append(line)

    def _extract_key_findings(self, lines):
        """Extract notable findings and insights."""
        finding_patterns = [
            r'(?:Found|Discovered|Realized|Important|Key finding):\s*(.+?)(?:\.|$)',
            r'(?:Note|FYI|Remember|Note:|Important:)\s+(.+?)(?:\.|$)',
            r'(?:need|needs|requires?)\s+(.+?)(?:for|because)',
        ]

        for line in lines:
            for pattern in finding_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and match.group(1).strip():
                    finding = match.group(1).strip()
                    if finding not in self.key_findings and len(finding) > 5:
                        self.key_findings.append(finding)

    def generate_markdown(self):
        """Generate a compact markdown summary."""
        sections = []

        sections.append(f"# Session Summary\n")
        sections.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Current Status
        sections.append("## Current Status\n")
        if self.todos:
            sections.append("### Active Tasks\n")
            for i, todo in enumerate(self.todos[:10], 1):  # Limit to 10
                sections.append(f"- [ ] {todo}\n")

        # Key Decisions
        if self.decisions:
            sections.append("\n## Key Technical Decisions\n")
            for decision in self.decisions[:5]:  # Top 5
                sections.append(f"- **{decision['title']}**\n")

        # Resolved Issues
        if self.bugs:
            sections.append("\n## Resolved Issues\n")
            for bug in self.bugs[:5]:  # Top 5
                sections.append(f"- {bug['title']}\n")

        # Important Findings
        if self.key_findings:
            sections.append("\n## Key Findings\n")
            for finding in self.key_findings[:5]:
                sections.append(f"- {finding}\n")

        # Code References
        if self.code_snippets:
            sections.append("\n## Code References\n")
            for lang, snippets in list(self.code_snippets.items())[:3]:
                sections.append(f"\n### {lang.upper()}\n")
                for snippet in snippets[:2]:  # Limit snippets
                    sections.append(f"```{lang}\n{snippet[:500]}\n```\n")

        # Instructions for next session
        sections.append("\n## Next Steps\n")
        sections.append("1. Review the active tasks above\n")
        sections.append("2. Paste this summary into a fresh chat session\n")
        sections.append("3. Continue from where you left off\n")

        return ''.join(sections)


def main():
    parser = argparse.ArgumentParser(
        description='Extract session summary from conversation text'
    )
    parser.add_argument('input_file', help='Input conversation text file')
    parser.add_argument(
        '--output', '-o',
        default='session-summary.md',
        help='Output markdown file (default: session-summary.md)'
    )
    parser.add_argument(
        '--max-tokens', '-m',
        type=int,
        default=5000,
        help='Maximum tokens for summary (default: 5000)'
    )

    args = parser.parse_args()

    # Read input
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text()

    # Extract
    extractor = SessionExtractor(max_tokens=args.max_tokens)
    extractor.extract_from_text(text)

    # Generate
    summary = extractor.generate_markdown()

    # Write output
    output_path = Path(args.output)
    output_path.write_text(summary)

    print(f"✓ Summary generated: {output_path}")
    print(f"  - {len(extractor.todos)} active tasks")
    print(f"  - {len(extractor.decisions)} key decisions")
    print(f"  - {len(extractor.bugs)} resolved issues")
    print(f"  - {len(extractor.key_findings)} key findings")


if __name__ == '__main__':
    main()
