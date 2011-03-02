import os
import uuid

def generate_version_id():
    return str(uuid.uuid4())

def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)
