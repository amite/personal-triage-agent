"""
Drafting Tool - Generates and saves draft emails
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from agents.llm_client_base import LLMClientBase

class DraftingTool:
    """Generates and saves draft emails"""

    name = "drafting_tool"
    description = "Drafts an email based on the given topic or content. Use this when the user needs to write, compose, or draft an email or message."

    @staticmethod
    def execute(
        content: str, 
        llm_client: Optional[LLMClientBase] = None,
        thread_id: Optional[str] = None,
        checkpoint_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute drafting tool with database storage.
        
        Args:
            content: Email topic or content
            llm_client: Optional LLM client for generating email body
            thread_id: Optional thread ID for linking to execution
            checkpoint_id: Optional checkpoint ID
        
        Returns:
            Dictionary with success, draft_id, subject, and message
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Use LLM to generate email body
        if llm_client:
            email_prompt = f"""Write a professional email about: {content}

Generate ONLY the email body (no subject line, no greeting, no signature). Keep it concise and professional, maximum 3-4 sentences.

Email body:"""

            try:
                email_body = llm_client.generate(email_prompt, temperature=0.7).strip()
            except:
                email_body = f"I wanted to reach out regarding {content}. Please let me know your thoughts at your earliest convenience."
        else:
            email_body = f"I wanted to reach out regarding {content}. Please let me know your thoughts at your earliest convenience."

        # Extract subject from content
        subject = f"Re: {content}"

        draft = f"""
{'='*60}
DRAFT EMAIL - {timestamp}
{'='*60}

Subject: {subject}

Dear Recipient,

{email_body}

Best regards,
[Your Name]

{'='*60}
"""

        # Create database record
        try:
            from utils.artifacts_db import ArtifactsDB
            
            db = ArtifactsDB()
            draft_id = db.create_draft(
                thread_id=thread_id or "unknown",
                body=draft,
                subject=subject,
                checkpoint_id=checkpoint_id
            )
            return {
                "success": True,
                "draft_id": draft_id,
                "subject": subject,
                "message": f"✓ Email draft created (ID: {draft_id}): '{subject}'"
            }
        except Exception as e:
            logging.error(f"Failed to create draft in database: {e}")
            return {
                "success": False,
                "draft_id": None,
                "subject": subject,
                "message": f"✗ Failed to save draft: {str(e)}"
            }
