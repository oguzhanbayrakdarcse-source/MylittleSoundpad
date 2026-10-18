from pathlib import Path
import struct

ROM = Path("Pokemon - FireRed Version (USA).gba")
START = 0x3C9CB8
HEADER_SIZE = 20
MAX_HEADERS = 1000

data = ROM.read_bytes()

print(f"ROM size: {len(data):,} bytes")
print(f"Testing header start: 0x{START:X}")

headers = []
terminator_found = False

for i in range(MAX_HEADERS):
    off = START + i * HEADER_SIZE

    if off + HEADER_SIZE > len(data):
        break

    group = data[off]
    map_num = data[off + 1]

    if group == 0xFF:
        terminator_found = True
        print(f"\nTerminator found at 0x{off:X}")
        break

    pointers = struct.unpack_from("<4I", data, off + 4)
    headers.append((off, group, map_num, pointers))

print(f"Headers before terminator: {len(headers)}")
print(f"Terminator found: {terminator_found}")

print("\nFirst 12 headers:")
for off, group, map_num, pointers in headers[:12]:
    formatted = [
        f"0x{p:08X}" if p else "NULL"
        for p in pointers
    ]
    print(
        f"0x{off:06X} | group={group:3} map={map_num:3} | "
        + " | ".join(formatted)
    )

print("\nLast 5 headers:")
for off, group, map_num, pointers in headers[-5:]:
    print(
        f"0x{off:06X} | group={group:3} map={map_num:3} | "
        + " ".join(f"{p:08X}" for p in pointers)
    )

print("\nRead-only inspection complete. ROM was not modified.")
