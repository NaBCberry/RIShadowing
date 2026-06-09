#!/usr/bin/env python3
"""Create a proper ICO file from a PNG image."""
import struct, io, sys
from PIL import Image


def create_ico(png_path, ico_path, sizes=None):
    if sizes is None:
        sizes = [16, 24, 32, 48, 64, 128, 256]
    
    img = Image.open(png_path).convert("RGBA")
    
    entries = []  # (width, height, data_bytes)
    
    for s in sizes:
        resized = img.resize((s, s), Image.LANCZOS)
        pixels = list(resized.getdata())  # list of (R,G,B,A) tuples
        
        # XOR mask: BGRA data (32bpp)
        xor_data = bytearray()
        for r, g, b, a in pixels:
            xor_data.extend([b, g, r, a])
        
        # AND mask: 1 bit per pixel, 1 = transparent
        and_data = bytearray()
        for i in range(s):
            row_bits = 0
            for j in range(s):
                r, g, b, a = pixels[i * s + j]
                if a < 128:
                    row_bits |= (1 << (7 - (j % 8)))
                if j % 8 == 7 or j == s - 1:
                    and_data.append(row_bits)
                    row_bits = 0
            # Pad AND mask row to 4 bytes
            row_bytes = (s + 7) // 8
            while len(and_data) % 4 != 0:
                and_data.append(0)
        
        # XOR data rows must also be 4-byte aligned (they already are for 32bpp)
        
        # BITMAPINFOHEADER (40 bytes)
        bih = struct.pack('<IiiHHIIiiII',
            40,           # biSize
            s,            # biWidth
            s * 2,        # biHeight (double for ICO: XOR + AND)
            1,            # biPlanes
            32,           # biBitCount
            0,            # biCompression (BI_RGB)
            0,            # biSizeImage (can be 0 for BI_RGB)
            0, 0, 0, 0)   # biXPelsPerMeter, biYPelsPerMeter, biClrUsed, biClrImportant
        
        data = bytes(bih) + bytes(xor_data) + bytes(and_data)
        entries.append((s, data))
    
    # Build ICO file
    count = len(entries)
    header = struct.pack('<HHH', 0, 1, count)
    
    # Calculate offsets
    dir_offset = 6
    dir_size = count * 16
    data_offset = dir_offset + dir_size
    
    # Build directory entries
    directory = bytearray()
    entry_data = bytearray()
    for s, data in entries:
        w = s if s < 256 else 0
        h = s if s < 256 else 0
        entry = struct.pack('<BBBBHHII',
            w, h, 0, 0, 1, 32, len(data), data_offset)
        directory.extend(entry)
        entry_data.extend(data)
        data_offset += len(data)
    
    with open(ico_path, 'wb') as f:
        f.write(header)
        f.write(directory)
        f.write(entry_data)
    
    print(f"Created {ico_path}: {count} sizes, {data_offset} bytes")


if __name__ == '__main__':
    create_ico('RIShadowing.ico', 'RIShadowing.ico')
