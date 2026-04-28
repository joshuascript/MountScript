import os
from dataclasses import dataclass
from src.paths import Paths

@dataclass
class Volume:
    name: str
    directory: str
    mounted: bool
    casefold: bool
    source_image: str = ""

@dataclass
class MountImage:
    image_path: str
    size_gb: int
    mounted_to: str

class VersionInfo:
    version: str = ""
    meets_minimum: bool = False

class SessionState:
    selected_directory: str = ""
    status_message: str = ""

    @staticmethod
    def save():
        with open(Paths.SESSION_FILE, "w") as f:
            f.write(SessionState.selected_directory)

    @staticmethod
    def load():
        if os.path.exists(Paths.SESSION_FILE):
            with open(Paths.SESSION_FILE, "r") as f:
                SessionState.selected_directory = f.read().strip()

    @staticmethod
    def clear():
        SessionState.selected_directory = ""
        if os.path.exists(Paths.SESSION_FILE):
            os.remove(Paths.SESSION_FILE)
