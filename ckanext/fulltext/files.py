import tempfile
from xmlrpc.client import boolean

def fix_local_url(url: str) -> str:
    if url.startswith("/"):
        return f"file://{url}"

def create_temp_file_path(url: str):
    path = tempfile.mkdtemp()
    filename = url.split("/")[-1]

    return "/".join([path,filename]), path

def is_web(url: str) -> boolean:
    pass

def is_local(url: str) -> boolean:
    pass
