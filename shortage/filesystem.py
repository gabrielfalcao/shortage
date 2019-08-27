import re
import logging
import json
from pathlib import Path
from shortage.config import SMS_STORAGE_PATH

logger = logging.getLogger(__name__)


def slugify(string: str, separator: str = "_"):
    return re.sub(r"\W+", separator, string)


def sanitize(string: str):
    if not isinstance(string, str):
        raise TypeError(
            f"sanitize takes a string but got {string!r} ({type(string)!r})"
        )

    if len(string) == 0:
        raise ValueError(f"string is empty")

    return slugify(string)


def ensure_path_exists_as_directory(path: Path):
    if not path.is_dir() and path.exists():
        raise IOError(f"{path} already exists and is not a directory.")

    path.mkdir(parents=True, exist_ok=True)
    return path


class FileStorage(object):
    def __init__(self, base_path: [Path, str]):
        self.base_path = Path(base_path)

    def path_to_key(self, name: str):
        sanitized = sanitize(name)
        return ensure_path_exists_as_directory(
            self.base_path.joinpath(sanitized)
        )

    def path_to_blob(self, key_name, key_value):
        key_path = self.path_to_key(key_name)
        blob_path = key_path.joinpath(f"{key_value}.json")
        return blob_path

    def add(self, key_name, key_value, data):
        blob_path = self.path_to_blob(key_name, key_value)
        if isinstance(data, bytes):
            data = data.decode("utf-8")

        blob = json.dumps(data, indent=2)
        with blob_path.open("w") as fd:
            fd.write(blob)

        logger.info(f"wrote blob: {blob_path}")
        return blob_path


def get_storage_path():
    return Path(SMS_STORAGE_PATH or "~/.shortage/data").expanduser().absolute()


def default_storage():
    blob_path = get_storage_path()
    return FileStorage(ensure_path_exists_as_directory(blob_path))
