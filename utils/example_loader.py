"""Load and parse example requests from YAML configuration."""

import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Example:
    """Structured example request with metadata."""

    id: str
    name: str
    description: str
    category: str
    complexity: str
    request: str
    expected_tools: List[str]
    expected_task_count: int
    tags: List[str]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Example":
        """Create Example from dictionary."""
        return Example(
            id=data.get("id", "unknown"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            complexity=data.get("complexity", "medium"),
            request=data.get("request", ""),
            expected_tools=data.get("expected_tools", []),
            expected_task_count=data.get("expected_task_count", 0),
            tags=data.get("tags", []),
        )


class ExampleLoader:
    """Loads and manages examples from YAML configuration."""

    def __init__(self, config_path: str = "data/examples.yaml"):
        """Initialize loader.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.examples: List[Example] = []
        self.categories: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load and parse YAML file."""
        try:
            if not self.config_path.exists():
                logger.warning(
                    f"Examples file not found at {self.config_path}, using fallback"
                )
                return

            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config or "examples" not in config:
                logger.warning("No examples found in YAML file")
                return

            # Load categories
            if "categories" in config:
                for cat in config["categories"]:
                    self.categories[cat["name"]] = cat.get("description", "")

            # Load examples
            for ex_data in config.get("examples", []):
                try:
                    example = Example.from_dict(ex_data)
                    self.examples.append(example)
                except Exception as e:
                    logger.error(f"Failed to load example {ex_data.get('id')}: {e}")

            logger.info(f"Loaded {len(self.examples)} examples from {self.config_path}")

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file: {e}")
        except Exception as e:
            logger.error(f"Error loading examples: {e}")

    def get_all_requests(self) -> List[str]:
        """Get list of request strings for backward compatibility.

        Returns:
            List of request strings in order
        """
        return [ex.request for ex in self.examples]

    def get_by_category(self, category: str) -> List[Example]:
        """Filter examples by category.

        Args:
            category: Category name to filter by

        Returns:
            List of examples in the category
        """
        return [ex for ex in self.examples if ex.category == category]

    def get_by_tag(self, tag: str) -> List[Example]:
        """Filter examples by tag.

        Args:
            tag: Tag name to filter by

        Returns:
            List of examples with the tag
        """
        return [ex for ex in self.examples if tag in ex.tags]

    def get_by_complexity(self, complexity: str) -> List[Example]:
        """Filter examples by complexity level.

        Args:
            complexity: 'simple', 'medium', or 'complex'

        Returns:
            List of examples with the specified complexity
        """
        return [ex for ex in self.examples if ex.complexity == complexity]

    def get_example(self, example_id: str) -> Optional[Example]:
        """Get a specific example by ID.

        Args:
            example_id: Example ID to retrieve

        Returns:
            Example object or None if not found
        """
        for ex in self.examples:
            if ex.id == example_id:
                return ex
        return None

    def validate_example(
        self, example: Example, actual_tools: List[str]
    ) -> Dict[str, Any]:
        """Compare expected vs actual tool selection for testing.

        Args:
            example: Example to validate
            actual_tools: List of tools actually selected by LLM

        Returns:
            Dictionary with validation results
        """
        expected_set = set(example.expected_tools)
        actual_set = set(actual_tools)

        return {
            "passed": expected_set == actual_set,
            "expected": example.expected_tools,
            "actual": actual_tools,
            "missing": list(expected_set - actual_set),
            "extra": list(actual_set - expected_set),
            "expected_count": example.expected_task_count,
            "actual_count": len(actual_tools),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded examples.

        Returns:
            Dictionary with example statistics
        """
        complexity_counts = {}
        category_counts = {}
        tag_counts = {}

        for ex in self.examples:
            complexity_counts[ex.complexity] = complexity_counts.get(ex.complexity, 0) + 1
            category_counts[ex.category] = category_counts.get(ex.category, 0) + 1
            for tag in ex.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            "total_examples": len(self.examples),
            "total_categories": len(self.categories),
            "complexity_distribution": complexity_counts,
            "category_distribution": category_counts,
            "most_common_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        }

    def print_statistics(self) -> None:
        """Print example statistics to logger."""
        stats = self.get_statistics()
        logger.info(f"Total Examples: {stats['total_examples']}")
        logger.info(f"Total Categories: {stats['total_categories']}")
        logger.info(f"Complexity Distribution: {stats['complexity_distribution']}")
        logger.info(f"Top Categories: {dict(list(stats['category_distribution'].items())[:3])}")
