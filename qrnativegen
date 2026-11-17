
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QR Code Generator
100% Python standard library.
No external dependencies.

Usage:
    python qrcode.py https://example.com
    python qrcode.py 192.168.1.1
    python qrcode.py https://example.com --save
"""

import argparse
import struct
import zlib
import binascii


# QR Code versions 1 à 4, ECC-L
# (data codewords, error correction codewords)
QR_SPECS = {
    1: (19, 7),
    2: (34, 10),
    3: (55, 15),
    4: (80, 20),
}


def gf_multiply(x, y):
    """Multiplication dans GF(256)."""
    result = 0

    while y:
        if y & 1:
            result ^= x

        x <<= 1

        if x & 0x100:
            x ^= 0x11D

        y >>= 1

    return result


def rs_generator(degree):
    """Construit le polynôme générateur Reed-Solomon."""
    poly = [1]

    for i in range(degree):
        new = [0] * (len(poly) + 1)

        for j, coef in enumerate(poly):
            new[j] ^= coef
            new[j + 1] ^= gf_multiply(coef, 1 << 0)

        root = 1
        for _ in range(i):
            root = gf_multiply(root, 2)

        new = [0] * len(new)

        for j, coef in enumerate(poly):
            new[j] ^= coef
            new[j + 1] ^= coef
            new[j + 1] ^= gf_multiply(coef, root)

        poly = new

    return poly


def reed_solomon(data, degree):
    """Calcule les octets de correction d'erreur."""
    generator = [1]

    for i in range(degree):
        root = 1
        for _ in range(i):
            root = gf_multiply(root, 2)

        new = [0] * (len(generator) + 1)

        for j, coef in enumerate(generator):
            new[j] ^= coef
            new[j + 1] ^= gf_multiply(coef, root)

        generator = new

    result = list(data) + [0] * degree

    for i in range(len(data)):
        factor = result[i]

        for j in range(len(generator)):
            result[i + j] ^= gf_multiply(
                generator[j], factor
            )

    return result[-degree:]


class BitBuffer:
    def __init__(self):
        self.bits = []

    def append(self, value, length):
        for i in range(length - 1, -1, -1):
            self.bits.append((value >> i) & 1)

    def bytes(self):
        result = bytearray()

        for i in range(0, len(self.bits), 8):
            value = 0

            for bit in self.bits[i:i + 8]:
                value = (value << 1) | bit

            result.append(value)

        return result


class QRCode:

    def __init__(self, data):
        self.data = data.encode("utf-8")

        self.version = next(
            (
                v for v, (capacity, _) in QR_SPECS.items()
                if len(self.data) <= capacity - 2
            ),
            None
        )

        if self.version is None:
            raise ValueError(
                "Texte trop long (maximum 78 octets)."
            )

        self.size = 17 + 4 * self.version
        self.matrix = [
            [None] * self.size for _ in range(self.size)
        ]

        self._build()

    def _encode(self):
        capacity, ecc = QR_SPECS[self.version]

        bits = BitBuffer()

        # Mode byte
        bits.append(0b0100, 4)

        # Taille des données
        bits.append(len(self.data), 8)

        for byte in self.data:
            bits.append(byte, 8)

        max_bits = capacity * 8

        bits.append(0, min(4, max_bits - len(bits.bits)))

        while len(bits.bits) % 8:
            bits.append(0, 1)

        result = list(bits.bytes())

        while len(result) < capacity:
            result.append(0xEC if len(result) % 2 == 0 else 0x11)

        return result + reed_solomon(result, ecc)

    def _set(self, x, y, value):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.matrix[y][x] = bool(value)

    def _finder(self, x, y):
        for dy in range(-1, 8):
            for dx in range(-1, 8):
                xx, yy = x + dx, y + dy

                if not (0 <= xx < self.size and 0 <= yy < self.size):
                    continue

                distance = max(abs(dx - 3), abs(dy - 3))
                self._set(xx, yy, distance != 2 and distance <= 3)

    def _build(self):
        size = self.size

        self._finder(0, 0)
        self._finder(size - 7, 0)
        self._finder(0, size - 7)

        for i in range(8, size - 8):
            self._set(i, 6, i % 2 == 0)
            self._set(6, i, i % 2 == 0)

        self._set(8, 4 * self.version + 9, True)

        codewords = self._encode()
        bits = []

        for byte in codewords:
            bits.extend(
                (byte >> i) & 1 for i in range(7, -1, -1)
            )

        index = 0
        upward = True
        right = size - 1

        while right >= 1:
            if right == 6:
                right -= 1

            for vertical in range(size):
                y = size - 1 - vertical if upward else vertical

                for dx in range(2):
                    x = right - dx

                    if self.matrix[y][x] is None:
                        bit = bits[index] if index < len(bits) else 0
                        index += 1

                        # Masque 0
                        mask = (x + y) % 2 == 0
                        self._set(x, y, bit ^ mask)

            upward = not upward
            right -= 2

        self._format_info()

    def _format_info(self):
        # Format ECC-L, masque 0
        data = 0b01 << 3

        remainder = data

        for _ in range(10):
            remainder = (remainder << 1) ^ (
                0x537 if remainder & 0x400 else 0
            )

        bits = ((data << 10) | remainder) ^ 0x5412

        positions = [
            (8, 0), (8, 1), (8, 2), (8, 3), (8, 4),
            (8, 5), (8, 7), (8, 8), (7, 8),
            (5, 8), (4, 8), (3, 8), (2, 8),
            (1, 8), (0, 8)
        ]

        for i, (x, y) in enumerate(positions):
            self._set(x, y, (bits >> i) & 1)

        positions2 = [
            (self.size - 1, 8),
            (self.size - 2, 8),
            (self.size - 3, 8),
            (self.size - 4, 8),
            (self.size - 5, 8),
            (self.size - 6, 8),
            (self.size - 7, 8),
            (8, self.size - 8),
            (8, self.size - 7),
            (8, self.size - 6),
            (8, self.size - 5),
            (8, self.size - 4),
            (8, self.size - 3),
            (8, self.size - 2),
            (8, self.size - 1),
        ]

        for i, (x, y) in enumerate(positions2):
            self._set(x, y, (bits >> i) & 1)

    def display(self):
        border = 2

        for y in range(-border, self.size + border):
            line = ""

            for x in range(-border, self.size + border):
                dark = (
                    0 <= x < self.size
                    and 0 <= y < self.size
                    and self.matrix[y][x]
                )

                line += "██" if dark else "  "

            print(line)

    def save_png(self, filename, scale=10):
        """Enregistre le QR Code au format PNG sans bibliothèque externe."""

        border = 4
        width = (self.size + border * 2) * scale
        height = width

        raw = bytearray()

        for y in range(height):
            raw.append(0)

            for x in range(width):
                mx = x // scale - border
                my = y // scale - border

                dark = (
                    0 <= mx < self.size
                    and 0 <= my < self.size
                    and self.matrix[my][mx]
                )

                raw.append(0 if dark else 255)

        def chunk(kind, data):
            return (
                struct.pack(">I", len(data))
                + kind + data
                + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
            )

        png = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(
                ">IIBBBBB", width, height, 8, 0, 0, 0, 0
            ))
            + chunk(b"IDAT", zlib.compress(bytes(raw)))
            + chunk(b"IEND", b"")
        )

        with open(filename, "wb") as file:
            file.write(png)


def main():
    parser = argparse.ArgumentParser(
        description="Générateur QR Code sans dépendances."
    )

    parser.add_argument("target", help="IP ou URL à encoder")
    parser.add_argument(
        "--save",
        nargs="?",
        const="qrcode.png",
        help="Enregistrer en PNG (défaut : qrcode.png)"
    )

    args = parser.parse_args()

    try:
        qr = QRCode(args.target)

        print(f"\nQR Code : {args.target}\n")
        qr.display()

        if args.save:
            qr.save_png(args.save)
            print(f"\nImage enregistrée : {args.save}")

    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
