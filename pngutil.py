import struct
from zlib import crc32

PNG_HEADER = b"\x89PNG\x0d\x0a\x1a\x0a"
EXIF_MARKER = b"eXIf"

def split(data):
    if data[0:8] != PNG_HEADER:
        raise ValueError("Not PNG")

    start = 8
    pointer = start
    CHUNK_FOURCC_LENGTH = 4
    LENGTH_BYTES_LENGTH = 4
    CRC_LENGTH = 4
    file_size = len(data)
    END_SIGN = b"IEND"

    chunks = []
    while pointer + CHUNK_FOURCC_LENGTH + LENGTH_BYTES_LENGTH < file_size:
        data_length_bytes = data[pointer:pointer + LENGTH_BYTES_LENGTH]
        data_length = struct.unpack(">L", data_length_bytes)[0]
        pointer += LENGTH_BYTES_LENGTH

        fourcc = data[pointer:pointer + CHUNK_FOURCC_LENGTH]
        pointer += CHUNK_FOURCC_LENGTH

        chunk_data = data[pointer:pointer + data_length]
        pointer += data_length

        crc = data[pointer:pointer + CRC_LENGTH]
        pointer += CRC_LENGTH
        chunks.append({
            "fourcc":fourcc,
            "length_bytes":data_length_bytes,
            "data":chunk_data,
            "crc":crc
        })

        if fourcc == END_SIGN:
            break
        
    return chunks

def merge_chunks(chunks):
    merged = b"".join([chunk["length_bytes"] 
                       + chunk["fourcc"]
                       + chunk["data"]
                       + chunk["crc"]
                        for chunk in chunks])
    return merged


def get_exif(data):
    if data[0:8] != PNG_HEADER:
        raise ValueError("Not PNG")

    chunks = split(data)
    exif = None
    for chunk in chunks:
        if chunk["fourcc"] == EXIF_MARKER:
            return chunk["data"]
    return exif


def insert_exif_into_chunks(chunks, exif_bytes):
    exif_length_bytes = struct.pack("<L", len(exif_bytes))
    crc = struct.pack("<L", crc32(EXIF_MARKER + data))
    exif_chunk = {
        "fourcc":EXIF_MARKER,
        "length_bytes":exif_length_bytes,
        "data":exif_bytes,
        "crc":crc
    }

    for index, chunk in enumerate(chunks):
        if chunk["fourcc"] == EXIF_MARKER:
            chunks[index] = exif_chunk
            return chunks
    chunks.insert(-1, exif_chunk)
    return chunks


def insert(png_bytes, exif_bytes):
    chunks = split(data)
    chunks = insert_exif_into_chunks(chunks, exif_bytes)
    merged = merge_chunks(chunks)
    new_png_bytes = PNG_HEADER + merged
    return new_png_bytes


def remove(png_bytes):
    chunks = split(data)
    for index, chunk in enumerate(chunks):
        if chunk["fourcc"] == EXIF_MARKER:
            chunks.pop(index)
            break
    merged = merge_chunks(chunks)
    new_png_bytes = PNG_HEADER + merged
    return new_png_bytes

if __name__ == "__main__":
    import glob
    import piexif
    from PIL import Image

    IMAGE_DIR = "samples/"
    OUT_DIR = "samples/out/"
    files = [
        "i01.png",
    ]


    exif_dict = {
        "0th":{
            piexif.ImageIFD.Software: b"PIL",
            piexif.ImageIFD.Make: b"Make",
        }
    }

    for filename in files:
        print("\n\n\n**********\n" + filename)
        with open(IMAGE_DIR + filename, "rb") as f:
            data = f.read()

        print("  -----------\n")
        exif_bytes = piexif.dump(exif_dict)
        exif_inserted = insert(data, exif_bytes)
        with open(OUT_DIR + "i_" + filename, "wb") as f:
            f.write(exif_inserted)
        try:
            Image.open(OUT_DIR + "i_" + filename)
        except Exception as e:
            print(e.args)

        print("  -----------\n")
        exif_loaded = get_exif(exif_inserted)
        print(exif_loaded[0:10])

        print("  -----------\n")
        with open(OUT_DIR + "i_" + filename, "rb") as f:
            data = f.read()
        exif_removed = remove(data)
        with open(OUT_DIR + "r_" + filename, "wb") as f:
            f.write(exif_removed)
        try:
            Image.open(OUT_DIR + "r_" + filename)
        except Exception as e:
            print(e.args)
