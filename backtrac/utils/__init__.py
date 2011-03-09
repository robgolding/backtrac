import os
import uuid
import magic

def generate_version_id():
    return str(uuid.uuid4())

def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_mimetype(fd):
    """
    Get the mimetype from the given open file descriptor `fd'.

    Reads the first 1024 bytes and restores `fd' to it's original position.
    """
    pos = fd.tell()
    fd.seek(0)
    mime = magic.from_buffer(fd.read(1024), mime=True)
    fd.seek(pos)
    return mime
