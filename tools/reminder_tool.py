"""
Reminder Tool - Writes reminders to database
"""

import logging
from typing import Optional, Dict, Any

class ReminderTool:
    """Writes reminders to database"""

    name = "reminder_tool"
    description = "Sets a reminder for a specific task or event. Use this when the user wants to remember something or be reminded about an action."

    @staticmethod
    def execute(
        content: str, 
        thread_id: Optional[str] = None,
        checkpoint_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute reminder tool with database storage.
        
        Args:
            content: Reminder content
            thread_id: Optional thread ID for linking to execution
            checkpoint_id: Optional checkpoint ID
        
        Returns:
            Dictionary with success, reminder_id, and message
        """

        # Create database record
        try:
            from utils.artifacts_db import ArtifactsDB
            
            db = ArtifactsDB()
            reminder_id = db.create_reminder(
                thread_id=thread_id or "unknown",
                content=content,
                checkpoint_id=checkpoint_id
            )
            return {
                "success": True,
                "reminder_id": reminder_id,
                "message": f"✓ Reminder created (ID: {reminder_id}): '{content}'"
            }
        except Exception as e:
            logging.error(f"Failed to create reminder in database: {e}")
            return {
                "success": False,
                "reminder_id": None,
                "message": f"✗ Failed to set reminder: {str(e)}"
            }
