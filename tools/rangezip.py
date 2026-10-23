#!/usr/bin/env python3
"""Lista o extrae entradas de un .zip remoto con HTTP Range, sin bajarlo entero.

Se usa para sacar sólo los archivos de Android del paquete de plantillas de
Godot (1,28 GB), que no entra en el disco de la PC del laboratorio:

  python3 tools/rangezip.py URL                       # lista
  python3 tools/rangezip.py URL DESTINO nombre1 ...   # extrae (por sufijo)
"""
import os
import struct
import sys
import urllib.request
import zlib


def get(url, start, end):
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(req) as r:
        return r.read()


def entries(url):
    head = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"))
    size = int(head.headers["Content-Length"])
    tail = get(url, size - 65536 - 22, size - 1)
    i = tail.rfind(b"PK\x05\x06")
    _, _, _, _, n, cd_size, cd_off, _ = struct.unpack("<IHHHHIIH", tail[i:i + 22])
    if cd_off == 0xFFFFFFFF or n == 0xFFFF:          # ZIP64
        j = tail.rfind(b"PK\x06\x07")
        z64off = struct.unpack("<Q", tail[j + 8:j + 16])[0]
        rec = get(url, z64off, z64off + 55)
        n, cd_size, cd_off = struct.unpack("<QQQ", rec[32:56])
    cd = get(url, cd_off, cd_off + cd_size - 1)
    out, p = [], 0
    while p < len(cd):
        (_, _, _, _, method, _, _, _, csize, usize, flen, xlen, clen, _, _, _, loff) = struct.unpack("<IHHHHHHIIIHHHHHII", cd[p:p + 46])
        name = cd[p + 46:p + 46 + flen].decode()
        extra = cd[p + 46 + flen:p + 46 + flen + xlen]
        if 0xFFFFFFFF in (csize, usize, loff):
            q = 0
            while q < len(extra):
                hid, hl = struct.unpack("<HH", extra[q:q + 4])
                if hid == 1:
                    vals = list(struct.unpack("<" + "Q" * (hl // 8), extra[q + 4:q + 4 + hl]))
                    if usize == 0xFFFFFFFF:
                        usize = vals.pop(0)
                    if csize == 0xFFFFFFFF:
                        csize = vals.pop(0)
                    if loff == 0xFFFFFFFF:
                        loff = vals.pop(0)
                q += 4 + hl
        out.append((name, method, csize, usize, loff))
        p += 46 + flen + xlen + clen
    return out


def main():
    url = sys.argv[1]
    items = entries(url)
    if len(sys.argv) < 4:
        for e in items:
            print(e[0], e[3])
        return
    dest, wanted = sys.argv[2], sys.argv[3:]
    os.makedirs(dest, exist_ok=True)
    for name, method, csize, usize, loff in items:
        if not any(name.endswith(w) for w in wanted):
            continue
        lh = get(url, loff, loff + 29)
        flen, xlen = struct.unpack("<HH", lh[26:30])
        start = loff + 30 + flen + xlen
        path = os.path.join(dest, os.path.basename(name))
        # Por bloques de 16 MB para no cargar todo en memoria.
        dec = zlib.decompressobj(-15) if method == 8 else None
        with open(path, "wb") as f:
            pos = 0
            while pos < csize:
                chunk = get(url, start + pos, start + min(csize, pos + (16 << 20)) - 1)
                pos += len(chunk)
                f.write(dec.decompress(chunk) if dec else chunk)
            if dec:
                f.write(dec.flush())
        print("extraído", name, os.path.getsize(path), "de", usize)


if __name__ == "__main__":
    main()
