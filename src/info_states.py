import os
import json
from dataclasses import dataclass
from paths import Paths

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
    permanent: bool = False

class VersionInfo:
    version: str = ""
    meets_minimum: bool = False

class SessionState:
    selected_directory: str = ""
    status_message: str = ""
    permanent_directories: list = []

    @staticmethod
    def save():
        data = {
            "selected": SessionState.selected_directory,
            "permanent": SessionState.permanent_directories,
        }
        with open(Paths.SESSION_FILE, "w") as f:
            json.dump(data, f)

    @staticmethod
    def load():
        if not os.path.exists(Paths.SESSION_FILE):
            return
        with open(Paths.SESSION_FILE, "r") as f:
            content = f.read().strip()
        try:
            data = json.loads(content)
            SessionState.selected_directory = data.get("selected", "")
            SessionState.permanent_directories = data.get("permanent", [])
        except (json.JSONDecodeError, AttributeError):
            # backward compat: old format was a bare path
            SessionState.selected_directory = content
            SessionState.permanent_directories = []

    @staticmethod
    def clear():
        SessionState.selected_directory = ""
        if SessionState.permanent_directories:
            SessionState.save()
        elif os.path.exists(Paths.SESSION_FILE):
            os.remove(Paths.SESSION_FILE)
