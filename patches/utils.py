import hashlib

def generate_checksum(fp):
    md5 = hashlib.md5()
    for chunk in fp.chunks():
        md5.update(chunk)
    return md5.hexdigest()


