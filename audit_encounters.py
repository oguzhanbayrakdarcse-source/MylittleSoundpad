from pathlib import Path
import struct

ROM = Path("Pokemon - FireRed Version (USA).gba")
START = 0x3C9CB8

TABLES = [
    ("Land", 12),
    ("Water", 5),
    ("Rock Smash", 5),
    ("Fishing", 10),
]

data = ROM.read_bytes()

def ptr_to_offset(ptr):
    if ptr == 0:
        return None
    if 0x08000000 <= ptr <= 0x09FFFFFF:
        off = ptr - 0x08000000
        if off < len(data):
            return off
    return None

headers = []
for i in range(1000):
    off = START + i * 20
    if off + 20 > len(data):
        break

    group, map_num = data[off], data[off + 1]

    # FireRed's undefined-map sentinel
    if group == 0xFF:
        print(f"Sentinel: 0x{off:X}")
        break

    pointers = struct.unpack_from("<4I", data, off + 4)
    headers.append((off, group, map_num, pointers))

valid_tables = 0
invalid_tables = []
total_slots = 0

for header_off, group, map_num, pointers in headers:
    for (name, count), ptr in zip(TABLES, pointers):
        if ptr == 0:
            continue

        info_off = ptr_to_offset(ptr)
        if info_off is None or info_off + 8 > len(data):
            invalid_tables.append((header_off, name, "invalid info pointer"))
            continue

        rate = data[info_off]
        mons_ptr = struct.unpack_from("<I", data, info_off + 4)[0]
        mons_off = ptr_to_offset(mons_ptr)

        if mons_off is None or mons_off + count * 4 > len(data):
            invalid_tables.append((header_off, name, "invalid Pokémon pointer"))
            continue

        entries = []
        for j in range(count):
            pos = mons_off + j * 4
            min_level, max_level, species = struct.unpack_from("<BBH", data, pos)
            entries.append((min_level, max_level, species))

        if not (0 <= rate <= 100):
            invalid_tables.append((header_off, name, f"unexpected rate {rate}"))
            continue

        if any(
            not (1 <= lo <= 100 and 1 <= hi <= 100 and 1 <= species <= 386)
            for lo, hi, species in entries
        ):
            invalid_tables.append((header_off, name, "unexpected slot values"))
            continue

        valid_tables += 1
        total_slots += count

print(f"ROM: {ROM.name}")
print(f"Header records before sentinel: {len(headers)}")
print(f"Valid encounter tables: {valid_tables}")
print(f"Valid Pokémon slots: {total_slots}")
print(f"Tables needing review: {len(invalid_tables)}")

print("\nFirst 10 header records:")
for off, group, map_num, pointers in headers[:10]:
    print(
        f"0x{off:06X} group={group} map={map_num} "
        + " ".join(f"{p:08X}" for p in pointers)
    )

if invalid_tables:
    print("\nFirst 20 tables needing review:")
    for item in invalid_tables[:20]:
        print(item)

print("\nAudit only: ROM was not modified.")
