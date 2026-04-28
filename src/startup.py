import os
import subprocess
from packaging.version import Version
from src.info_states import VersionInfo, SessionState
from src.volume_cache import VolumeCache
from src.image_cache import ImageCache
from src.paths import Paths

volume_cache: VolumeCache = None
image_cache: ImageCache = None

def initialize():
    global volume_cache, image_cache

    os.makedirs(Paths.IMAGES_DIR, exist_ok=True)
    SessionState.load()
    _check_version()
    _populate_volumes()
    _populate_images()
    _cross_reference()

def _check_version():
    result = subprocess.run(
        ["bash", Paths.BASH_DIR + "/version_check.bash"],
        capture_output=True,
        text=True
    )
    version_str = result.stdout.strip()
    if not version_str:
        print("Could not determine e2fsprogs version")
        VersionInfo.version = ""
        VersionInfo.meets_minimum = False
        return
    minimum = Version("1.45")
    VersionInfo.version = version_str
    VersionInfo.meets_minimum = Version(version_str) >= minimum

def _populate_volumes():
    global volume_cache
    volume_cache = VolumeCache()

def _populate_images():
    global image_cache
    image_cache = ImageCache()

def _cross_reference():
    for image in image_cache.images:
        volume = volume_cache.get_by_source(image.image_path)
        if volume:
            image.mounted_to = volume.directory
