"""
A module for encoding and decoding data in the bencode format.

This module implements functions for working with bencode, including encoding and decoding strings (UTF-8 support), integers, lists, and dictionaries from stream or bytes.
Bencode is a serialization format used in BitTorrent.
"""

from io import SEEK_SET, SEEK_CUR, BufferedReader, BytesIO
from pathlib import Path

type SupportedTypes = int | str | list[SupportedTypes] | dict[
    str, SupportedTypes
] | bytes


def encode(value: SupportedTypes) -> bytes:
    if isinstance(value, int):
        return encode_int(value)
    elif isinstance(value, str):
        return encode_str(value)
    elif isinstance(value, list):
        return encode_list(value)
    elif isinstance(value, dict):
        return encode_dict(value)
    elif isinstance(value, bytes):
        return encode_bytes(value)
    raise TypeError(f"Unsupported type: {type(value)}")


def encode_str(value: str) -> bytes:
    if not isinstance(value, str):
        raise TypeError(f"Expected str, got {type(value)}")
    encoded = value.encode()
    return str(len(encoded)).encode() + b":" + encoded


def encode_int(value: int) -> bytes:
    if not isinstance(value, int):
        raise TypeError(f"Expected int, got {type(value)}")
    return f"i{value}e".encode()


def encode_list(value: list[SupportedTypes]) -> bytes:
    if not isinstance(value, list):
        raise TypeError(f"Expected list, got {type(value)}")
    return b"l" + b"".join([encode(v) for v in value]) + b"e"


def encode_dict(value: dict[str, SupportedTypes]) -> bytes:
    if not isinstance(value, dict):
        raise TypeError(f"Expected a dictionary, got {type(value)}")
    buf = b"d"
    for key, val in sorted(value.items()):
        buf += encode(key)
        buf += encode(val)
    return buf + b"e"


def encode_bytes(value: bytes) -> bytes:
    if not isinstance(value, bytes):
        raise TypeError(f"Expected bytes, got {type(value)}")
    return f"{len(value)}:".encode() + value


def decode_str_from_stream(stream: BytesIO | BufferedReader) -> str:
    if not isinstance(stream, (BytesIO, BufferedReader)):
        raise TypeError(f"Expected BytesIO or BufferedReader, got {type(stream)}")
    length_str = b""
    while True:
        byte = stream.read(1)
        if not byte:
            raise ValueError("Unterminated string length")
        if byte == b":":
            break
        length_str += byte
    length = int(length_str)
    buf = stream.read(length)
    return buf.decode()


def decode_int_from_stream(
    stream: BytesIO | BufferedReader, skip_signature: bool = True
) -> int:
    if not isinstance(stream, (BytesIO, BufferedReader)):
        raise TypeError(f"Expected BytesIO or BufferedReader, got {type(stream)}")
    if skip_signature:
        stream.read(1)  # skip signature (i)
    num_str = b""
    while True:
        byte = stream.read(1)
        if not byte:
            raise ValueError("Unterminated integer")
        if byte == b"e":
            return int(num_str)
        num_str += byte


def decode_from_stream(stream: BytesIO | BufferedReader) -> SupportedTypes:
    if not isinstance(stream, (BytesIO, BufferedReader)):
        raise TypeError(f"Expected BytesIO or BufferedReader, got {type(stream)}")
    byte = stream.read(1)
    if not byte:
        raise ValueError("Unexpected end of file")
    if byte == b"i":
        return decode_int_from_stream(stream, skip_signature=False)
    elif byte == b"l":
        return decode_list_from_stream(stream, skip_signature=False)
    elif byte == b"d":
        return decode_dict_from_stream(stream, skip_signature=False)
    elif byte.isdigit():
        stream.seek(-1, SEEK_CUR)
        pos = stream.tell()
        try:
            return decode_str_from_stream(stream)
        except UnicodeDecodeError:
            stream.seek(pos, SEEK_SET)
            return decode_bytes_from_stream(stream)
    else:
        raise ValueError(f"Invalid bencode byte: {byte}")


def decode_list_from_stream(
    stream: BytesIO | BufferedReader, skip_signature: bool = True
) -> list[SupportedTypes]:
    if not isinstance(stream, (BytesIO, BufferedReader)):
        raise TypeError(f"Expected BytesIO or BufferedReader, got {type(stream)}")
    if skip_signature:
        stream.read(1)  # skip signature (l)
    items = []
    while True:
        pos = stream.tell()
        byte = stream.read(1)
        if byte == b"e":
            break
        stream.seek(pos)
        items.append(decode_from_stream(stream))
    return items


def decode_dict_from_stream(
    stream: BytesIO | BufferedReader, skip_signature: bool = True
) -> dict[str, SupportedTypes]:
    if not isinstance(stream, (BytesIO, BufferedReader)):
        raise TypeError(f"Expected BytesIO or BufferedReader, got {type(stream)}")
    if skip_signature:
        stream.read(1)  # skip signature (d)
    data = {}
    while True:
        pos = stream.tell()
        byte = stream.read(1)
        if byte == b"e":
            break
        stream.seek(pos)
        key = decode_from_stream(stream)
        value = decode_from_stream(stream)
        data[key] = value
    return data


def decode_bytes_from_stream(stream: BytesIO | BufferedReader) -> bytes:
    if not isinstance(stream, (BytesIO, BufferedReader)):
        raise TypeError(f"Expected BytesIO or BufferedReader, got {type(stream)}")
    length_str = b""
    while True:
        byte = stream.read(1)
        if not byte:
            raise ValueError("Unterminated bytes length")
        if byte == b":":
            break
        length_str += byte
    length = int(length_str)
    buf = stream.read(length)
    return buf


def decode_str_from_bytes(value: bytes) -> str:
    if not isinstance(value, bytes):
        raise TypeError(f"Expected bytes, got {type(value)}")
    return decode_str_from_stream(BytesIO(value))


def decode_str(value: bytes) -> str:
    return decode_str_from_bytes(value)


def decode_int_from_bytes(value: bytes) -> int:
    if not isinstance(value, bytes):
        raise TypeError(f"Expected bytes, got {type(value)}")
    return decode_int_from_stream(BytesIO(value))


def decode_int(value: bytes) -> int:
    return decode_int_from_bytes(value)


def decode_list_from_bytes(value: bytes) -> list[SupportedTypes]:
    if not isinstance(value, bytes):
        raise TypeError(f"Expected bytes, got {type(value)}")
    return decode_list_from_stream(BytesIO(value))


def decode_list(value: bytes) -> list[SupportedTypes]:
    return decode_list_from_bytes(value)


def decode_dict_from_bytes(value: bytes) -> dict[str, SupportedTypes]:
    if not isinstance(value, bytes):
        raise TypeError(f"Expected bytes, got {type(value)}")
    return decode_dict_from_stream(BytesIO(value))


def decode_dict(value: bytes) -> dict[str, SupportedTypes]:
    return decode_dict_from_bytes(value)


def decode_bytes_from_bytes(value: bytes) -> bytes:
    if not isinstance(value, bytes):
        raise TypeError(f"Expected bytes, got {type(value)}")
    return decode_bytes_from_stream(BytesIO(value))


def decode_bytes(value: bytes) -> bytes:
    return decode_bytes_from_bytes(value)


def decode_from_bytes(value: bytes) -> SupportedTypes:
    if not isinstance(value, bytes):
        raise TypeError(f"Expected bytes, got {type(value)}")
    return decode_from_stream(BytesIO(value))


def decode(value: bytes) -> SupportedTypes:
    return decode_from_bytes(value)


def decode_from_torrent_file(file_path: str | Path) -> dict[str, SupportedTypes]:
    if not isinstance(file_path, (str, Path)):
        raise TypeError(f"Expected str or Path, got {type(file_path)}")
    file_path = Path(file_path)
    with file_path.open("rb") as br:
        return decode_dict_from_stream(br)
