import uuid
from collections import OrderedDict
from threading import Lock

MAX_IMAGES = 200

# Penyimpanan sementara di memori; foto dirujuk lewat id dari pesan chat
# supaya gambar tidak ikut tersimpan di riwayat percakapan.
_images: OrderedDict[str, tuple[bytes, str]] = OrderedDict()
_lock = Lock()


def save_image(data: bytes, mime_type: str) -> str:
    image_id = f"foto_{uuid.uuid4().hex[:8]}"
    with _lock:
        _images[image_id] = (data, mime_type)
        while len(_images) > MAX_IMAGES:
            _images.popitem(last=False)
    return image_id


def get_image(image_id: str) -> tuple[bytes, str] | None:
    with _lock:
        return _images.get(image_id)
