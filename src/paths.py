import os

# Holds directory paths for the local directory
# and disk image mounts
class Paths:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    BASH_DIR = os.path.join(PROJECT_ROOT, "../bash")
    TEXT_SCREENS_DIR = os.path.join(PROJECT_ROOT, "../TextScreens")
    IMAGES_DIR = "/var/lib/mountscript"
    SESSION_FILE = "/var/lib/mountscript/session"
