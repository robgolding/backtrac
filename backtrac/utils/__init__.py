import os
import uuid
import magic
import hashlib
import datetime

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

def get_file_hash(filename):
    """
    Get the MD5 digest for the file at `filename'. Reads the file in chunks so
    the whole thing doesn't have to be loaded into memory first.
    """
    f = open(filename, 'rb')
    md5 = hashlib.md5()
    while True:
        data = f.read(128)
        if not data:
            break
        md5.update(data)
    return md5.digest()

def get_seconds_till_midnight():
    """
    Get the number of seconds remaining until midnight tonight. Pretty useful
    for scheduling and whatnot.
    """
    now = datetime.datetime.now()
    today = datetime.datetime(year=now.year, month=now.month, day=now.day)
    tomorrow = now + datetime.timedelta(days=1)
    return (tomorrow - today).seconds

def get_seconds_since_midnight():
    """
    Get the number of seconds since midnight last night. Again, pretty useful
    for scheduling.
    """
    now = datetime.datetime.now()
    today = datetime.datetime(year=now.year, month=now.month, day=now.day)
    return (now - today).seconds
