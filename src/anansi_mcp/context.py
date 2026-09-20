"""Shared runtime state passed to every tool module."""

from __future__ import annotations

from dataclasses import dataclass

from .client import AnansiClient
from .config import Settings


@dataclass
class AppContext:
    settings: Settings
    client: AnansiClient
