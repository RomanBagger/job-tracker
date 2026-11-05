"""Рисует иконку (скруглённый квадрат с графиком) без внешних библиотек и собирает .icns."""
import struct, subprocess, sys, zlib
from pathlib import Path

N = 1024
out = Path(sys.argv[1])
R = 230  # радиус скругления
px = bytearray()
bars = [(250, 560), (450, 400), (650, 250)]  # (x, верх), ширина 140, низ 780
for y in range(N):
    px.append(0)
    for x in range(N):
        cx, cy = min(max(x, R), N - 1 - R), min(max(y, R), N - 1 - R)
        inside = (x - cx) ** 2 + (y - cy) ** 2 <= R * R
        if not inside:
            px += b"\x00\x00\x00\x00"; continue
        t = y / N
        r, g, b = int(14 + 12 * t), int(124 - 20 * t), int(134 - 20 * t)
        if any(bx <= x < bx + 140 and top <= y < 780 for bx, top in bars):
            r, g, b = 255, 255, 255
        px += bytes((r, g, b, 255))

def chunk(t, d):
    c = struct.pack(">I", len(d)) + t + d
    return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", N, N, 8, 6, 0, 0, 0)) \
    + chunk(b"IDAT", zlib.compress(bytes(px), 9)) + chunk(b"IEND", b"")
base = out.with_suffix(".png"); base.write_bytes(png)
iset = out.with_suffix(".iconset"); iset.mkdir(exist_ok=True)
for s in (16, 32, 128, 256, 512):
    for scale in (1, 2):
        name = f"icon_{s}x{s}{'@2x' if scale == 2 else ''}.png"
        subprocess.run(["sips", "-z", str(s * scale), str(s * scale), str(base), "--out", str(iset / name)],
                       check=True, capture_output=True)
subprocess.run(["iconutil", "-c", "icns", str(iset), "-o", str(out)], check=True)
