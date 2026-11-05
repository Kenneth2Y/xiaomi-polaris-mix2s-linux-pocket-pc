#!/usr/bin/env python3
"""Offline readers/writers for this project's Android v0 boot image and newc.

No device access. Unsupported headers, extra trailers and corrupt IDs are rejected.
The Android layout/ID algorithm follows AOSP system/tools/mkbootimg/mkbootimg.py.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import struct
import zlib


def align(size: int, boundary: int) -> int:
    return (size + boundary - 1) // boundary * boundary


@dataclass
class BootImage:
    header: bytes
    page: int
    kernel: bytes
    ramdisk: bytes
    second: bytes

    @classmethod
    def parse(cls, data: bytes) -> BootImage:
        if len(data) < 1632 or data[:8] != b"ANDROID!":
            raise ValueError("Not an Android boot image")
        fields = struct.unpack_from("<10I", data, 8)
        page, version = fields[7:9]
        if version != 0 or page not in (2048, 4096, 8192, 16384):
            raise ValueError("Only the verified v0 boot layout is supported")
        offset, parts = page, []
        for size in (fields[0], fields[2], fields[4]):
            parts.append(data[offset:offset + size])
            if len(parts[-1]) != size:
                raise ValueError("Truncated boot component")
            offset += align(size, page)
        if offset != len(data):
            raise ValueError("Unexpected boot footer or truncation")
        image = cls(data[:page], page, *parts)
        if data[576:608] != image.image_id():
            raise ValueError("Android component SHA1 ID does not match")
        return image

    def image_id(self) -> bytes:
        digest = hashlib.sha1()
        for part in (self.kernel, self.ramdisk, self.second):
            digest.update(part)
            digest.update(struct.pack("<I", len(part)))
        return digest.digest().ljust(32, b"\0")

    def encode(self) -> bytes:
        header = bytearray(self.header)
        for offset, part in ((8, self.kernel), (16, self.ramdisk), (24, self.second)):
            struct.pack_into("<I", header, offset, len(part))
        header[576:608] = self.image_id()
        return bytes(header) + b"".join(
            part.ljust(align(len(part), self.page), b"\0")
            for part in (self.kernel, self.ramdisk, self.second)
        )

    def kernel_and_dtb(self) -> tuple[bytes, bytes]:
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        decoder.decompress(self.kernel)
        if not decoder.eof:
            raise ValueError("Kernel gzip stream is incomplete")
        dtb = decoder.unused_data
        if len(dtb) < 40 or dtb[:4] != b"\xd0\x0d\xfe\xed":
            raise ValueError("Expected an appended flattened device tree")
        if struct.unpack_from(">I", dtb, 4)[0] != len(dtb):
            raise ValueError("Unexpected bytes after appended DTB")
        return self.kernel[:-len(dtb)], dtb


@dataclass
class CpioEntry:
    name: str
    fields: tuple[int, ...]
    data: bytes

    @property
    def mode(self) -> int:
        return self.fields[1]


def read_cpio(data: bytes) -> list[CpioEntry]:
    entries, names, offset = [], set(), 0
    while offset + 110 <= len(data):
        header = data[offset:offset + 110]
        if header[:6] != b"070701":
            raise ValueError("Expected unchecksummed newc archive")
        fields = tuple(int(header[i:i + 8], 16) for i in range(6, 110, 8))
        size, namesize = fields[6], fields[11]
        if not namesize or offset + 110 + namesize > len(data):
            raise ValueError("Invalid CPIO name length")
        rawname = data[offset + 110:offset + 110 + namesize]
        if rawname[-1:] != b"\0":
            raise ValueError("Unterminated CPIO name")
        name = rawname[:-1].decode()
        offset = align(offset + 110 + namesize, 4)
        payload = data[offset:offset + size]
        if len(payload) != size:
            raise ValueError("Truncated CPIO payload")
        offset = align(offset + size, 4)
        if name == "TRAILER!!!":
            if any(data[offset:]):
                raise ValueError("Unsupported concatenated CPIO archives")
            return entries
        if name.startswith("/") or ".." in PurePosixPath(name).parts or name in names:
            raise ValueError("Unsafe or duplicate CPIO path")
        names.add(name)
        entries.append(CpioEntry(name, fields, payload))
    raise ValueError("CPIO trailer missing")


def write_cpio(entries: list[CpioEntry]) -> bytes:
    result = bytearray()
    trailer = CpioEntry("TRAILER!!!", (0,) * 13, b"")
    for entry in [*entries, trailer]:
        name = entry.name.encode() + b"\0"
        fields = list(entry.fields)
        fields[6], fields[11], fields[12] = len(entry.data), len(name), 0
        result += b"070701" + b"".join(f"{v:08x}".encode() for v in fields)
        result += name
        result += b"\0" * (-len(result) % 4)
        result += entry.data
        result += b"\0" * (-len(result) % 4)
    return bytes(result)


def new_entry(name: str, data: bytes, inode: int, mode: int = 0o100644) -> CpioEntry:
    return CpioEntry(name, (inode, mode, 0, 0, 1, 1793750400, len(data),
                            0, 0, 0, 0, len(name.encode()) + 1, 0), data)


def add_with_parents(entries: list[CpioEntry], name: str, data: bytes) -> None:
    known = {entry.name for entry in entries}
    if name in known:
        raise ValueError(f"Refusing to overwrite CPIO entry: {name}")
    inode = max(entry.fields[0] for entry in entries) + 1
    for parent in reversed(PurePosixPath(name).parents):
        p = str(parent)
        if p != "." and p not in known:
            entries.append(new_entry(p, b"", inode, 0o40755))
            known.add(p)
            inode += 1
    entries.append(new_entry(name, data, inode))


def module_names(entries: list[CpioEntry]) -> list[str]:
    return [e.name for e in entries if "/modules/" in e.name and ".ko" in e.name]


def self_check(baseline: Path) -> dict:
    from compression import zstd
    raw = baseline.read_bytes()
    image = BootImage.parse(raw)
    if image.encode() != raw:
        raise ValueError("Baseline boot image round trip changed bytes")
    kernel, dtb = image.kernel_and_dtb()
    entries = read_cpio(zstd.decompress(image.ramdisk))
    restored = read_cpio(write_cpio(entries))
    if entries != restored:
        raise ValueError("CPIO round trip changed metadata or payloads")
    # Ensure corrupt and oversized declarations are rejected before assembly.
    for position in (8, 576):
        damaged = bytearray(raw)
        damaged[position] ^= 1
        try:
            BootImage.parse(bytes(damaged))
        except ValueError:
            pass
        else:
            raise ValueError("Corrupt image was accepted")
    return {"boot_roundtrip": "byte-identical", "cpio_roundtrip": "metadata and payload identical",
            "corruption_checks": "passed", "kernel_gzip_bytes": len(kernel),
            "dtb_bytes": len(dtb), "entries": len(entries), "modules": len(module_names(entries))}


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    args = parser.parse_args()
    print(json.dumps(self_check(args.baseline), indent=2))
