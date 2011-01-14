def normpath(path):
    """Normalise a path to have a leading slash but no trailing slash."""
    return '/' + path.strip('/')
