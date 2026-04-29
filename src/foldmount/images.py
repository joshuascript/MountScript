import os
from typing import List
from .models import DiskImage
from .paths import Paths

class ImageCache:
    def __init__(self):
        self.images: List[DiskImage] = []
        self.refresh()

    def refresh(self):
        self.images = []
        if not os.path.isdir(Paths.IMAGES_DIR):
            return
        for filename in os.listdir(Paths.IMAGES_DIR):
            if filename.endswith(".img"):
                path = os.path.join(Paths.IMAGES_DIR, filename)
                self.images.append(DiskImage(
                    path=path,
                    size_gb=self._size_gb(path),
                    mount_point=""
                ))

    def _size_gb(self, path: str) -> int:
        return os.path.getsize(path) // (1024 ** 3)

    def get(self, path: str) -> DiskImage | None:
        return next((i for i in self.images if i.path == path), None)
