#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR Code generator - standard library only.

QR Model 2, Byte mode, UTF-8, ECC-L, versions 1 to 10.
No pip dependencies.

Examples:
    python qrcode.py https://example.com
    python qrcode.py 192.168.1.10 --save
    python qrcode.py example.com --save example.png
"""

import argparse
import ipaddress
import struct
import zlib
from urllib.parse import urlsplit


# ECC-L block layout: (number_of_blocks, total_codewords_per_block,
#                      data_codewords_per_block)
# For version 10, there are two groups with different block sizes.
ECC_L_BLOCKS = {
    1: [(1, 26, 19)],
    2: [(1, 44, 34)],
    3: [(1, 70, 55)],
    4: [(1, 100, 80)],
    5: [(1, 134, 108)],
    6: [(2, 86, 68)],
    7: [(2, 98, 78)],
    8: [(2, 121, 97)],
    9: [(2, 146, 116)],
    10: [(2, 86, 68), (2, 87, 69)],
}

ALIGNMENT_CENTERS = {
    1: [],
    2: [6, 18],
    3: [6, 22],
    4: [6, 26],
    5: [6, 30],
    6: [6, 34],
    7: [6, 22, 38],
    8: [6, 24, 42],
    9: [6, 26, 46],
    10: [6, 28, 50],
}


def gf_mul(x, y):
    """Multiplication in GF(256), primitive polynomial 0x11D."""
    result = 0
    while y:
        if y & 1:
            result ^= x
        y >>= 1
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    return result


def rs_generator(degree):
    """Return the Reed-Solomon generator polynomial."""
    poly = [1]
    root = 1
    for _ in range(degree):
        new_poly = [0] * (len(poly) + 1)
        for i, coefficient in enumerate(poly):
            new_poly[i] ^= coefficient
            new_poly[i + 1] ^= gf_mul(coefficient, root)
        poly = new_poly
        root = gf_mul(root, 2)
    return poly


def rs_remainder(data, degree):
    """Return Reed-Solomon error correction codewords."""
    generator = rs_generator(degree)
    remainder = list(data) + [0] * degree
    for i in range(len(data)):
        factor = remainder[i]
        if factor:
            for j, coefficient in enumerate(generator):
                remainder[i + j] ^= gf_mul(coefficient, factor)
    return remainder[-degree:]


class BitBuffer:
    def __init__(self):
        self.bits = []

    def append(self, value, count):
        for shift in range(count - 1, -1, -1):
            self.bits.append((value >> shift) & 1)

    def to_bytes(self):
        result = bytearray()
        for offset in range(0, len(self.bits), 8):
            value = 0
            for bit in self.bits[offset:offset + 8]:
                value = (value << 1) | bit
            result.append(value)
        return result


def block_layout(version):
    return [
        (count, total, data)
        for count, total, data in ECC_L_BLOCKS[version]
    ]


def data_capacity(version):
    return sum(count * data for count, _, data in block_layout(version))


def make_codewords(payload, version):
    """Encode byte-mode data, add padding, ECC, then interleave blocks."""
    layout = block_layout(version)
    data_capacity_bytes = data_capacity(version)

    bits = BitBuffer()
    bits.append(0b0100, 4)  # Byte mode
    count_bits = 8 if version <= 9 else 16
    bits.append(len(payload), count_bits)

    for byte in payload:
        bits.append(byte, 8)

    capacity_bits = data_capacity_bytes * 8
    if len(bits.bits) > capacity_bits:
        raise ValueError("Données trop longues pour la version QR sélectionnée.")

    bits.append(0, min(4, capacity_bits - len(bits.bits)))
    while len(bits.bits) % 8:
        bits.append(0, 1)

    data = list(bits.to_bytes())
    pad_bytes = (0xEC, 0x11)
    pad_index = 0
    while len(data) < data_capacity_bytes:
        data.append(pad_bytes[pad_index % 2])
        pad_index += 1

    blocks = []
    ecc_blocks = []
    offset = 0

    for count, total_count, data_count in layout:
        ecc_count = total_count - data_count
        for _ in range(count):
            block = data[offset:offset + data_count]
            offset += data_count
            blocks.append(block)
            ecc_blocks.append(rs_remainder(block, ecc_count))

    result = []
    max_data_len = max(map(len, blocks))
    for i in range(max_data_len):
        for block in blocks:
            if i < len(block):
                result.append(block[i])

    max_ecc_len = max(map(len, ecc_blocks))
    for i in range(max_ecc_len):
        for block in ecc_blocks:
            if i < len(block):
                result.append(block[i])

    return result


class QRCode:
    def __init__(self, text):
        self.text = text
        self.payload = text.encode("utf-8")

        self.version = None
        for version in range(1, 11):
            count_bits = 8 if version <= 9 else 16
            required_bits = 4 + count_bits + len(self.payload) * 8
            if required_bits <= data_capacity(version) * 8:
                self.version = version
                break

        if self.version is None:
            raise ValueError(
                "Texte trop long : maximum d'environ 271 octets en UTF-8 "
                "avec cette implémentation (versions 1 à 10, ECC-L)."
            )

        if self.version <= 9 and len(self.payload) >= 256:
            raise ValueError("Charge utile trop longue pour le compteur Byte Mode.")

        self.size = 17 + 4 * self.version
        self.modules = [[None] * self.size for _ in range(self.size)]
        self.function = [[False] * self.size for _ in range(self.size)]
        self._draw_function_patterns()
        self.codewords = make_codewords(self.payload, self.version)
        self._place_data()

        candidates = []
        for mask in range(8):
            candidate = [row[:] for row in self.modules]
            self._apply_mask(candidate, mask)
            self._draw_format_bits(candidate, mask)
            candidates.append((self._penalty_score(candidate), mask, candidate))

        _, self.mask, self.modules = min(candidates, key=lambda item: item[0])

    def _set_function(self, x, y, dark):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.modules[y][x] = bool(dark)
            self.function[y][x] = True

    def _finder(self, cx, cy):
        for dy in range(-1, 8):
            for dx in range(-1, 8):
                x, y = cx + dx, cy + dy
                if 0 <= x < self.size and 0 <= y < self.size:
                    inside = 0 <= dx <= 6 and 0 <= dy <= 6
                    if not inside:
                        dark = False
                    else:
                        distance = max(abs(dx - 3), abs(dy - 3))
                        dark = distance != 2
                    self._set_function(x, y, dark)

    def _alignment(self, cx, cy):
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                distance = max(abs(dx), abs(dy))
                self._set_function(cx + dx, cy + dy, distance != 1)

    def _draw_function_patterns(self):
        last = self.size - 7
        self._finder(0, 0)
        self._finder(last, 0)
        self._finder(0, last)

        centers = ALIGNMENT_CENTERS[self.version]
        for cy in centers:
            for cx in centers:
                # Skip the three alignment patterns that overlap finder patterns.
                if self.function[cy][cx]:
                    continue
                self._alignment(cx, cy)

        for i in range(8, self.size - 8):
            if not self.function[6][i]:
                self._set_function(i, 6, i % 2 == 0)
            if not self.function[i][6]:
                self._set_function(6, i, i % 2 == 0)

        self._draw_format_bits(self.modules, 0)
        # Format-information modules are function modules and must never
        # be overwritten by the payload placement.
        format_coords = (
            [(8, i) for i in range(6)]
            + [(8, 7), (8, 8), (7, 8)]
            + [(14 - i, 8) for i in range(9, 15)]
            + [(self.size - 1 - i, 8) for i in range(8)]
            + [(8, self.size - 15 + i) for i in range(8, 15)]
        )
        for x, y in format_coords:
            self.function[y][x] = True
        self.function[self.size - 8][8] = True

        if self.version >= 7:
            self._draw_version_bits()

    def _draw_format_bits(self, matrix, mask):
        # ECC level L has format value 01.
        data = (0b01 << 3) | mask
        remainder = data
        for _ in range(10):
            remainder = (remainder << 1) ^ (0x537 if (remainder >> 9) & 1 else 0)
        bits = ((data << 10) | remainder) ^ 0x5412

        coords_a = (
            [(8, i) for i in range(6)]
            + [(8, 7), (8, 8), (7, 8)]
            + [(14 - i, 8) for i in range(9, 15)]
        )
        coords_b = (
            [(self.size - 1 - i, 8) for i in range(8)]
            + [(8, self.size - 15 + i) for i in range(8, 15)]
        )

        for i, (x, y) in enumerate(coords_a):
            matrix[y][x] = (bits >> i) & 1
        for i, (x, y) in enumerate(coords_b):
            matrix[y][x] = (bits >> i) & 1

        matrix[self.size - 8][8] = True

    def _draw_version_bits(self):
        remainder = self.version
        for _ in range(12):
            remainder = (remainder << 1) ^ (
                0x1F25 if (remainder >> 11) & 1 else 0
            )
        bits = (self.version << 12) | remainder

        for i in range(18):
            bit = (bits >> i) & 1
            a = self.size - 11 + (i % 3)
            b = i // 3
            self._set_function(a, b, bit)
            self._set_function(b, a, bit)

    def _place_data(self):
        bits = []
        for byte in self.codewords:
            bits.extend((byte >> i) & 1 for i in range(7, -1, -1))

        index = 0
        upward = True
        right = self.size - 1

        while right >= 1:
            if right == 6:
                right = 5

            for vert in range(self.size):
                y = self.size - 1 - vert if upward else vert
                for dx in range(2):
                    x = right - dx
                    if not self.function[y][x]:
                        self.modules[y][x] = bool(bits[index]) if index < len(bits) else False
                        index += 1

            upward = not upward
            right -= 2

    @staticmethod
    def _mask_bit(mask, x, y):
        if mask == 0:
            return (x + y) % 2 == 0
        if mask == 1:
            return y % 2 == 0
        if mask == 2:
            return x % 3 == 0
        if mask == 3:
            return (x + y) % 3 == 0
        if mask == 4:
            return (x // 3 + y // 2) % 2 == 0
        if mask == 5:
            product = x * y
            return (product % 2 + product % 3) == 0
        if mask == 6:
            product = x * y
            return (product % 2 + product % 3) % 2 == 0
        return ((x + y) % 2 + (x * y) % 3) % 2 == 0

    def _apply_mask(self, matrix, mask):
        for y in range(self.size):
            for x in range(self.size):
                if not self.function[y][x] and self._mask_bit(mask, x, y):
                    matrix[y][x] = not matrix[y][x]

    def _penalty_score(self, matrix):
        score = 0
        size = self.size

        # Rule 1: runs of at least five same-colour modules.
        for lines in (matrix, list(map(list, zip(*matrix)))):
            for line in lines:
                run_colour = line[0]
                run_length = 1
                for value in line[1:]:
                    if value == run_colour:
                        run_length += 1
                    else:
                        if run_length >= 5:
                            score += 3 + run_length - 5
                        run_colour = value
                        run_length = 1
                if run_length >= 5:
                    score += 3 + run_length - 5

        # Rule 2: monochrome 2x2 blocks.
        for y in range(size - 1):
            for x in range(size - 1):
                value = matrix[y][x]
                if (matrix[y][x + 1] == value
                        and matrix[y + 1][x] == value
                        and matrix[y + 1][x + 1] == value):
                    score += 3

        # Rule 3: finder-like 1:1:3:1:1 pattern with four light modules.
        def count_finder_patterns(line):
            penalty = 0
            n = len(line)
            for i in range(n - 10):
                window = line[i:i + 11]
                if window == [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]:
                    penalty += 40
                if window == [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]:
                    penalty += 40
            return penalty

        for line in matrix:
            score += count_finder_patterns([int(v) for v in line])
        for line in zip(*matrix):
            score += count_finder_patterns([int(v) for v in line])

        # Rule 4: dark/light balance.
        dark = sum(sum(bool(v) for v in row) for row in matrix)
        total = size * size
        score += (abs(dark * 20 - total * 10) // total) * 10
        return score

    def terminal(self):
        border = 4
        for y in range(-border, self.size + border):
            row = []
            for x in range(-border, self.size + border):
                dark = (
                    0 <= x < self.size
                    and 0 <= y < self.size
                    and self.modules[y][x]
                )
                row.append("██" if dark else "  ")
            print("".join(row))

    def save_png(self, filename, scale=10):
        """Write a standards-friendly grayscale PNG with a 4-module quiet zone."""
        border = 4
        dimension = (self.size + border * 2) * scale
        raw = bytearray()

        for y in range(dimension):
            raw.append(0)  # PNG filter: None
            module_y = y // scale - border
            for x in range(dimension):
                module_x = x // scale - border
                dark = (
                    0 <= module_x < self.size
                    and 0 <= module_y < self.size
                    and self.modules[module_y][module_x]
                )
                raw.append(0 if dark else 255)

        def chunk(kind, data):
            return (
                struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            )

        png = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB",
                                         dimension, dimension, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b"")
        )
        with open(filename, "wb") as file:
            file.write(png)


def normalize_target(target):
    """Turn a bare domain or IP into a clickable URL; preserve explicit schemes."""
    target = target.strip()
    if not target:
        raise ValueError("L'adresse ne peut pas être vide.")

    try:
        address = ipaddress.ip_address(target)
        if address.version == 6:
            return "http://[" + target + "]"
        return "http://" + target
    except ValueError:
        pass

    if "://" not in target:
        target = "https://" + target

    parsed = urlsplit(target)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Seuls les liens http:// et https:// sont acceptés.")
    if not parsed.hostname:
        raise ValueError("URL invalide : nom d'hôte manquant.")
    return target


def main():
    parser = argparse.ArgumentParser(
        description="Générateur de QR Codes conforme, sans dépendances externes."
    )
    parser.add_argument("target", help="Adresse IP ou site web à encoder")
    parser.add_argument(
        "--save",
        nargs="?",
        const="qrcode.png",
        metavar="FICHIER.png",
        help="Enregistrer le QR Code en PNG (défaut : qrcode.png)"
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=10,
        help="Pixels par module pour le PNG (défaut : 10)"
    )
    args = parser.parse_args()

    if args.scale < 1 or args.scale > 100:
        parser.error("--scale doit être compris entre 1 et 100.")

    try:
        target = normalize_target(args.target)
        qr = QRCode(target)

        print(f"\nQR Code : {target}")
        print(f"Version : {qr.version} | ECC : L | Masque : {qr.mask}\n")
        qr.terminal()

        if args.save:
            filename = args.save
            if not filename.lower().endswith(".png"):
                filename += ".png"
            qr.save_png(filename, args.scale)
            print(f"\nImage PNG enregistrée : {filename}")

    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
