"""Dump the raw block structure + string table of a NIF.

pynifly's DLL only exposes nodes/shapes, so this reads the file header
directly:  block type table, per-block sizes and the string table (which holds
texture paths, shader names and anything else referenced by string).

NIF header layout (little endian):
    version line \n, endian line \n, user line \n
    uint32 num_blocks
    uint32 block_type_offset   (file offset of the block type string table)
    uint32 block_size[num_blocks]
    uint32 num_strings
    strings (uint16 length + bytes)

    py src/scripts/nif_blocks.py <file.nif> [...]
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path


def read_cstring_header(data: bytes, pos: int) -> tuple[str, int]:
    end = data.index(b"\n", pos)
    return data[pos:end].decode("utf-8", "replace"), end + 1


def parse(path: Path) -> None:
    data = path.read_bytes()
    pos = 0
    version, pos = read_cstring_header(data, pos)
    endian, pos = read_cstring_header(data, pos)
    user, pos = read_cstring_header(data, pos)
    (num_blocks,) = struct.unpack_from("<I", data, pos)
    (type_offset,) = struct.unpack_from("<I", data, pos + 4)
    pos += 8
    if num_blocks > 100000:
        raise ValueError(f"implausible block count {num_blocks}")
    sizes = list(struct.unpack_from(f"<{num_blocks}I", data, pos))
    pos += 4 * num_blocks
    (num_strings,) = struct.unpack_from("<I", data, pos)
    pos += 4
    strings = []
    for _ in range(num_strings):
        (length,) = struct.unpack_from("<H", data, pos)
        pos += 2
        strings.append(data[pos:pos + length].decode("utf-8", "replace"))
        pos += length

    # block type table: null terminated names, one per block, at type_offset
    types: list[str] = []
    tpos = type_offset
    for _ in range(num_blocks):
        end = data.index(b"\x00", tpos)
        types.append(data[tpos:end].decode("utf-8", "replace"))
        tpos = end + 1

    print(f"=== {path}")
    print(f"    version={version!r} endian={endian!r} user={user!r}")
    print(f"    {num_blocks} blocks")
    counts: dict[str, int] = {}
    for t in types:
        counts[t] = counts.get(t, 0) + 1
    for t, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"      {c:>3} x {t}")
    print("    strings:")
    for s in strings:
        print(f"      | {s}")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        parse(Path(arg))
