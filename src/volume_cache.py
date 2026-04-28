import subprocess
import json
from typing import List
from src.info_states import Volume
from src.paths import Paths

class VolumeCache:
    def __init__(self):
        self.volumes: List[Volume] = []
        self.refresh()

    # queries findmnt and repopulates the volume list
    def refresh(self):
        self.volumes = []
        result = subprocess.run(
            ["findmnt", "-J", "--output", "TARGET,SOURCE,FSTYPE"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return
        data = json.loads(result.stdout)
        for fs in data.get("filesystems", []):
            self._add_entry(fs)

    def _add_entry(self, fs: dict):
        source = fs.get("source", "")
        fstype = fs.get("fstype", "")
        is_casefold = fstype == "ext4" and source.startswith("/dev/loop")
        source_image = self._resolve_loop(source) if is_casefold else ""
        self.volumes.append(Volume(
            name=source,
            directory=fs.get("target", ""),
            mounted=True,
            casefold=is_casefold,
            source_image=source_image
        ))
        for child in fs.get("children", []):
            self._add_entry(child)

    # resolves a loop device to its backing image file path
    def _resolve_loop(self, loop_device: str) -> str:
        result = subprocess.run(
            ["losetup", "--output", "BACK-FILE", "--noheadings", loop_device],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    # returns True if the given directory is currently mounted
    def is_mounted(self, directory: str) -> bool:
        return any(v.directory == directory for v in self.volumes)

    # returns the Volume for a given directory, or None if not found
    def get(self, directory: str):
        return next((v for v in self.volumes if v.directory == directory), None)

    # returns the Volume whose backing image matches the given path
    def get_by_source(self, image_path: str):
        return next((v for v in self.volumes if v.source_image == image_path), None)

    # returns True if the directory is a MountScript casefold mount
    def is_casefold_mount(self, directory: str) -> bool:
        volume = self.get(directory)
        return volume is not None and volume.casefold and volume.source_image.startswith(Paths.IMAGES_DIR)

    # returns True if the directory is a casefold mount not created by MountScript
    def is_external_casefold(self, directory: str) -> bool:
        volume = self.get(directory)
        return volume is not None and volume.casefold and not volume.source_image.startswith(Paths.IMAGES_DIR)

    # returns only MountScript casefold volumes
    def casefold_volumes(self) -> List[Volume]:
        return [v for v in self.volumes if v.casefold and v.source_image.startswith(Paths.IMAGES_DIR)]

    # returns casefold volumes not created by MountScript
    def external_casefold_volumes(self) -> List[Volume]:
        return [v for v in self.volumes if v.casefold and not v.source_image.startswith(Paths.IMAGES_DIR)]
