import os
import json
from enum import Enum, auto
from dataclasses import dataclass
from .paths import Paths

class DirectoryState(Enum):
    MISSING           = auto()
    FOLDMOUNT         = auto()
    EXTERNAL_CASEFOLD = auto()
    MOUNTED           = auto()
    NOT_EMPTY         = auto()
    EMPTY             = auto()

@dataclass
class Volume:
    loop_device: str
    directory: str
    mounted: bool
    casefold: bool
    source_image: str = ""

@dataclass
class DiskImage:
    path: str
    size_gb: int
    mount_point: str
    permanent: bool = False

class VersionInfo:
    version: str = ""
    meets_minimum: bool = False

class Session:
    selected_directory: str = ""
    permanent_directories: list = []

    @staticmethod
    def save():
        data = {
            "selected": Session.selected_directory,
            "permanent": Session.permanent_directories,
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
            Session.selected_directory = data.get("selected", "")
            Session.permanent_directories = data.get("permanent", [])
        except (json.JSONDecodeError, AttributeError):
            # backward compat: old format was a bare path
            Session.selected_directory = content
            Session.permanent_directories = []

    @staticmethod
    def clear():
        Session.selected_directory = ""
        if Session.permanent_directories:
            Session.save()
        elif os.path.exists(Paths.SESSION_FILE):
            os.remove(Paths.SESSION_FILE)
