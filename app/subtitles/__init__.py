"""Subtitle output and duplicate suppression."""

from .deduplicator import SubtitleDeduplicator
from .manager import SubtitleManager
from .output import SubtitleOutput

__all__ = ["SubtitleDeduplicator", "SubtitleManager", "SubtitleOutput"]

