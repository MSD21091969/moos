"""Template Registry Core Logic.

Loads TemplateClusters from YAML files in the `src/templates` directory.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import ValidationError

from src.schemas.templates import TemplateCluster, TemplateEntry

logger = logging.getLogger(__name__)

# Default location for templates
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


class TemplateRegistry:
    """In-memory registry of loaded templates."""

    def __init__(self, load_dir: Path = TEMPLATE_DIR):
        self._load_dir = load_dir
        self._clusters: dict[str, TemplateCluster] = {}
        self._templates: dict[str, TemplateEntry] = {}

    def load_all(self):
        """Load all YAML/JSON files from the template directory."""
        if not self._load_dir.exists():
            logger.warning(f"Template directory not found: {self._load_dir}")
            return

        self._clusters.clear()
        self._templates.clear()

        for file_path in self._load_dir.glob("*.yaml"):
            try:
                self._load_file(file_path)
            except Exception as e:
                logger.error(f"Failed to load template file {file_path}: {e}")

        logger.info(
            f"Loaded {len(self._clusters)} clusters and {len(self._templates)} templates."
        )

    def _load_file(self, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        try:
            cluster = TemplateCluster(**data)
            self._clusters[cluster.name] = cluster
            for template in cluster.templates:
                # Last write wins for same-named templates across clusters
                self._templates[template.name] = template
        except ValidationError as e:
            logger.error(f"Validation error in {path}: {e}")
            raise

    def get_template(self, name: str) -> TemplateEntry | None:
        """Get a specific template by name."""
        return self._templates.get(name)

    def list_templates(self) -> list[TemplateEntry]:
        """List all available templates."""
        return list(self._templates.values())


# Global singleton instance
registry = TemplateRegistry()
