"""
External Search Tool - Simulates external data lookup
"""

class ExternalSearchTool:
    """Simulates external data lookup"""

    name = "search_tool"
    description = "Searches for information, looks up data, checks files, or retrieves external information. Use this for queries about stock prices, weather, file checks, or any factual lookup."

    @staticmethod
    def execute(query: str) -> str:
        query_lower = query.lower()

        if "stock" in query_lower and "google" in query_lower:
            return "✓ Google (GOOGL) stock price: $142.50 (Last updated: Today)"
        elif "stock" in query_lower:
            return f"✓ Stock information: Market data retrieved for '{query}'"
        elif "weather" in query_lower:
            return "✓ Weather: 72°F, Partly Cloudy, 10% chance of rain"
        elif "file" in query_lower or "document" in query_lower or "attach" in query_lower:
            return f"✓ File check: Found 3 relevant files ready for review"
        else:
            return f"✓ Search result: Information retrieved for '{query}'"
