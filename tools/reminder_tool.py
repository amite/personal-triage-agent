"""
Reminder Tool - Writes reminders to persistent files
"""

import re
from datetime import datetime

class ReminderTool:
    """Writes reminders to a persistent file"""

    name = "reminder_tool"
    description = "Sets a reminder for a specific task or event. Use this when the user wants to remember something or be reminded about an action."

    @staticmethod
    def execute(content: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reminder_text = f"[{timestamp}] REMINDER: {content}\n"

        try:
            # Create inbox/reminders directory if it doesn't exist
            import os
            os.makedirs("inbox/reminders", exist_ok=True)

            # Create filename with timestamp
            safe_content = re.sub(r'[^\w\s-]', '', content[:30]).strip()
            filename = f"inbox/reminders/reminder_{file_timestamp}_{safe_content}.txt"

            with open(filename, "w") as f:
                f.write(reminder_text)
            return f"✓ Reminder saved to {filename}: '{content}'"
        except Exception as e:
            return f"✗ Failed to set reminder: {str(e)}"
