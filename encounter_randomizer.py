from pathlib import Path
import random
import struct
import hashlib

ROM = Path("Pokemon - FireRed Version (USA).gba")
OUTPUT_DIR = Path("output")
OUTPUT = OUTPUT_DIR / "FireRed_Randomized.gba"

# Verified for the inspected FireRed USA v1.0 ROM.
HEADER_START = 0x3C9CB8
HEADER_SIZE = 20

# Header order in FireRed: land, water, rock smash, fishing.
TABLE_TYPES = [
    ("Land", 12),
    ("Water", 5),
    ("Rock Smash", 5),
    ("Fishing", 10),
]

# National Pokédex species IDs available in FireRed.
SPECIES_POOL = list(range(1, 387))


def gba_pointer_to_offset(pointer, rom_size):
    if pointer == 0:
        return None

    if 0x08000000 <= pointer <= 0x09FFFFFF:
        offset = pointer - 0x08000000
        if offset < rom_size:
            return offset

    raise ValueError(f"Invalid ROM pointer: 0x{pointer:08X}")


def main():
    if not ROM.is_file():
        raise FileNotFoundError(
            f"ROM not found: {ROM.resolve()}"
        )

    original = ROM.read_bytes()

    if len(original) != 16 * 1024 * 1024:
        raise ValueError("Expected a 16 MiB FireRed ROM.")

    # Verify the exact ROM revision before writing anything.
    sha1 = hashlib.sha1(original).hexdigest().upper()
    expected_sha1 = "41CB23D8DCCC8EBD7C649CD8FBB58EEACE6E2FDC"

    if sha1 != expected_sha1:
        raise ValueError(f"Unexpected ROM SHA1: {sha1}")

    if original[0xAC:0xB0] != b"BPRE" or original[0xBC] != 0:
        raise ValueError("ROM header is not FireRed USA v1.0.")

    # Collect unique Pokémon arrays first. Some headers may share data.
    arrays = {}
    header_count = 0
    sentinel_found = False

    for index in range(1000):
        header_off = HEADER_START + index * HEADER_SIZE

        if header_off + HEADER_SIZE > len(original):
            break

        group = original[header_off]

        if group == 0xFF:
            sentinel_found = True
            break

        header_count += 1
        pointers = struct.unpack_from(
            "<4I", original, header_off + 4
        )

        for (table_name, slot_count), info_ptr in zip(
            TABLE_TYPES, pointers
        ):
            if info_ptr == 0:
                continue

            info_off = gba_pointer_to_offset(
                info_ptr, len(original)
            )

            if info_off + 8 > len(original):
                raise ValueError("Encounter info exceeds ROM bounds.")

            encounter_rate = original[info_off]
            if encounter_rate > 100:
                raise ValueError(
                    f"Unexpected encounter rate at 0x{info_off:X}"
                )

            mons_ptr = struct.unpack_from(
                "<I", original, info_off + 4
            )[0]
            mons_off = gba_pointer_to_offset(
                mons_ptr, len(original)
            )

            if mons_off + slot_count * 4 > len(original):
                raise ValueError("Pokémon table exceeds ROM bounds.")

            previous_count = arrays.get(mons_off)
            if previous_count is not None:
                if previous_count != slot_count:
                    raise ValueError(
                        f"Conflicting table sizes at 0x{mons_off:X}"
                    )
                continue

            # Validate every slot before modifying any data.
            for slot in range(slot_count):
                pos = mons_off + slot * 4
                min_level, max_level, species = struct.unpack_from(
                    "<BBH", original, pos
                )

                if not (1 <= min_level <= 100):
                    raise ValueError(
                        f"Invalid minimum level at 0x{pos:X}"
                    )
                if not (1 <= max_level <= 100):
                    raise ValueError(
                        f"Invalid maximum level at 0x{pos:X}"
                    )
                if not (1 <= species <= 386):
                    raise ValueError(
                        f"Unexpected species ID {species} at 0x{pos:X}"
                    )

            arrays[mons_off] = slot_count

    if not sentinel_found:
        raise ValueError("Header terminator was not found.")

    if header_count != 132:
        raise ValueError(
            f"Expected 132 headers; found {header_count}. "
            "Aborting without writing."
        )

    if not arrays:
        raise ValueError("No encounter arrays were validated.")

    # Only after validation, randomize species IDs in memory.
    rng = random.Random()
    seed = rng.getrandbits(32)
    rng.seed(seed)

    randomized = bytearray(original)
    total_slots = 0

    for mons_off, slot_count in arrays.items():
        for slot in range(slot_count):
            pos = mons_off + slot * 4

            # Preserve both levels; replace only the species ID.
            new_species = rng.choice(SPECIES_POOL)
            struct.pack_into("<H", randomized, pos + 2, new_species)
            total_slots += 1

    # Confirm the level bytes and ROM size remain unchanged.
    for mons_off, slot_count in arrays.items():
        for slot in range(slot_count):
            pos = mons_off + slot * 4
            if randomized[pos:pos + 2] != original[pos:pos + 2]:
                raise RuntimeError("A Pokémon level was unexpectedly changed.")

    OUTPUT_DIR.mkdir(exist_ok=True)
    OUTPUT.write_bytes(randomized)

    print("Randomization complete!")
    print(f"ROM: {OUTPUT.resolve()}")
    print(f"Seed: {seed}")
    print(f"Headers: {header_count}")
    print(f"Unique encounter arrays: {len(arrays)}")
    print(f"Pokémon slots randomized: {total_slots}")
    print("Levels preserved: yes")
    print("Encounter rates preserved: yes")
    print("Original ROM modified: no")


if __name__ == "__main__":
    main()
