import subprocess
import json
from typing import List
from .models import Volume
from .paths import Paths

class VolumeCache:
    def __init__(self):
        self.volumes: List[Volume] = []
        self.refresh()

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
        # Casefold mounts are identified by being ext4 on a loop device.
        # This is a heuristic — not all ext4 loop mounts have casefold enabled,
        # but all anneal mounts do.
        is_casefold = fstype == "ext4" and source.startswith("/dev/loop")
        source_image = self._resolve_loop(source) if is_casefold else ""
        self.volumes.append(Volume(
            loop_device=source,
            directory=fs.get("target", ""),
            mounted=True,
            casefold=is_casefold,
            source_image=source_image
        ))
        for child in fs.get("children", []):
            self._add_entry(child)

    # Resolves a loop device path (e.g. /dev/loop0) to its backing file path.
    def _resolve_loop(self, loop_device: str) -> str:
        result = subprocess.run(
            ["losetup", "--output", "BACK-FILE", "--noheadings", loop_device],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def is_mounted(self, directory: str) -> bool:
        return any(v.directory == directory for v in self.volumes)

    def get(self, directory: str) -> Volume | None:
        return next((v for v in self.volumes if v.directory == directory), None)

    def get_by_source(self, image_path: str) -> Volume | None:
        return next((v for v in self.volumes if v.source_image == image_path), None)

    # A anneal mount is a casefold volume whose image lives in IMAGES_DIR.
    def is_casefold_mount(self, directory: str) -> bool:
        volume = self.get(directory)
        return volume is not None and volume.casefold and volume.source_image.startswith(Paths.IMAGES_DIR)

    # An external casefold is a casefold loop mount not created by anneal.
    def is_external_casefold(self, directory: str) -> bool:
        volume = self.get(directory)
        return volume is not None and volume.casefold and not volume.source_image.startswith(Paths.IMAGES_DIR)

    def casefold_volumes(self) -> List[Volume]:
        return [v for v in self.volumes if v.casefold and v.source_image.startswith(Paths.IMAGES_DIR)]
