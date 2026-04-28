import os
from typing import List
from src.info_states import MountImage
from src.paths import Paths

class ImageCache:
    def __init__(self):
        self.images: List[MountImage] = []
        self.refresh()

    # scans the images directory and repopulates the image list
    def refresh(self):
        self.images = []
        if not os.path.isdir(Paths.IMAGES_DIR):
            return
        for filename in os.listdir(Paths.IMAGES_DIR):
            if filename.endswith(".img"):
                image_path = os.path.join(Paths.IMAGES_DIR, filename)
                self.images.append(MountImage(
                    image_path=image_path,
                    size_gb=self._size_gb(image_path),
                    mounted_to=""
                ))

    # returns the size of the image file in GB
    def _size_gb(self, image_path: str) -> int:
        return os.path.getsize(image_path) // (1024 ** 3)

    # returns the MountImage for a given path, or None if not found
    def get(self, image_path: str):
        return next((i for i in self.images if i.image_path == image_path), None)
