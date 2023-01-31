import os


def get_file_size(fp) -> int:
    pos = fp.tell()
    fp.seek(0, os.SEEK_END)
    size = fp.tell()
    fp.seek(pos)
    return size


def chunk_file(file, chunk_size):
    while data := file.read(chunk_size):
        yield data


def format_locations(*location_urls):
    return "final;" + " ".join(location_urls)
