"""Shim module — re-exports from meditation_evolution_simple for backward compatibility."""

from .meditation_evolution_simple import (
    analyze_and_adjust_simple as analyze_and_adjust,
    execute_meditation_with_evolution,
)

class MeditationLogManager:
    """Minimal stub so the import does not fail."""
    def __init__(self, *args, **kwargs):
        pass
    def log(self, *args, **kwargs):
        pass
    def get_logs(self, *args, **kwargs):
        return []
