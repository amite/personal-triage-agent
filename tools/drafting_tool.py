"""
Drafting Tool - Generates and saves draft emails
"""

import re
from datetime import datetime
from typing import Optional

from agents.ollama_client import OllamaClient

class DraftingTool:
    """Generates and saves draft emails"""

    name = "drafting_tool"
    description = "Drafts an email based on the given topic or content. Use this when the user needs to write, compose, or draft an email or message."

    @staticmethod
    def execute(content: str, llm_client: Optional[OllamaClient] = None) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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

        draft = f"""
{'='*60}
DRAFT EMAIL - {timestamp}
{'='*60}

Subject: Re: {content}

Dear Recipient,

{email_body}

Best regards,
[Your Name]

{'='*60}
"""

        try:
            # Create inbox/drafts directory if it doesn't exist
            import os
            os.makedirs("inbox/drafts", exist_ok=True)

            # Create filename with timestamp
            safe_content = re.sub(r'[^\w\s-]', '', content[:30]).strip()
            filename = f"inbox/drafts/draft_{file_timestamp}_{safe_content}.txt"

            with open(filename, "w") as f:
                f.write(draft)
            return f"✓ Email draft saved to {filename} about: '{content[:50]}...'"
        except Exception as e:
            return f"✗ Failed to save draft: {str(e)}"
