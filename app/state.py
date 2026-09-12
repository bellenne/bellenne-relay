"""Application lifecycle states shared by GUI and controller."""

from enum import StrEnum


class ApplicationState(StrEnum):
    STOPPED = "STOPPED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"

