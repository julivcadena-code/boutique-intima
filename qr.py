# Genera qr-tienda.png (con el logo al centro) y qr-tienda.svg con la dirección de la tienda.
# Uso:  python herramientas/qr.py                       -> usa la dirección de datos/sitio.txt
#       python herramientas/qr.py https://mi-dominio.com -> usa la dirección que escribas
# Se ejecuta solo cada vez que la tienda se actualiza (ver sincronizar.py).
import os, re, sys
from PIL import Image, ImageDraw
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---- tablas del estándar QR (nivel de corrección H = el más resistente, permite poner el logo encima) ----
ECC_CW = {  # bytes de corrección por bloque, versiones 1..20
 'H': [0, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28]}
BLOCKS = {  # cantidad de bloques, versiones 1..20
 'H': [0, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25]}
L = 'H'

def raw_modules(v):
    r = (16 * v + 128) * v + 64
    if v >= 2:
        n = v // 7 + 2
        r -= (25 * n - 10) * n - 55
        if v >= 7: r -= 36
    return r

def data_cw(v): return raw_modules(v) // 8 - ECC_CW[L][v] * BLOCKS[L][v]

def gmul(x, y):
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z

def rs_div(deg):
    r = [0] * (deg - 1) + [1]; root = 1
    for _ in range(deg):
        for j in range(deg):
            r[j] = gmul(r[j], root)
            if j + 1 < deg: r[j] ^= r[j + 1]
        root = gmul(root, 2)
    return r

def rs_rem(data, div):
    r = [0] * len(div)
    for b in data:
        f = b ^ r.pop(0); r.append(0)
        for i, c in enumerate(div): r[i] ^= gmul(c, f)
    return r

def encode(text):
    data = text.encode('utf-8')
    for v in range(1, 21):
        cc = 8 if v < 10 else 16
        if 4 + cc + 8 * len(data) <= data_cw(v) * 8: break
    else:
        raise SystemExit('La dirección es demasiado larga para el QR')
    bits = '0100' + format(len(data), '0%db' % cc) + ''.join(format(b, '08b') for b in data)
    bits += '0' * min(4, data_cw(v) * 8 - len(bits)); bits += '0' * (-len(bits) % 8)
    cw = [int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(cw) < data_cw(v): cw.append(pad); pad ^= 0xEC ^ 0x11
    nb, ecl, raw = BLOCKS[L][v], ECC_CW[L][v], raw_modules(v) // 8
    nshort, shortlen = nb - raw % nb, raw // nb
    div, k, blocks = rs_div(ecl), 0, []
    for i in range(nb):
        d = cw[k:k + shortlen - ecl + (0 if i < nshort else 1)]; k += len(d)
        e = rs_rem(d, div)
        if i < nshort: d = d + [0]
        blocks.append(d + e)
    out = []
    for i in range(len(blocks[0])):
        for j, b in enumerate(blocks):
            if i != shortlen - ecl or j >= nshort: out.append(b[i])
    return v, out

def build(v, cws):
    n = v * 4 + 17
    M = [[False] * n for _ in range(n)]; F = [[False] * n for _ in range(n)]
    def fn(x, y, d):
        if 0 <= x < n and 0 <= y < n: M[y][x] = bool(d); F[y][x] = True
    for i in range(n): fn(6, i, i % 2 == 0); fn(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5): fn(cx + dx, cy + dy, max(abs(dx), abs(dy)) not in (2, 4))
    if v > 1:
        na = v // 7 + 2; step = 26 if v == 32 else (v * 4 + na * 2 + 1) // (na * 2 - 2) * 2
        pos = list(reversed([n - 7 - i * step for i in range(na - 1)] + [6]))
        for i, py in enumerate(pos):
            for j, px in enumerate(pos):
                if (i == 0 and j == 0) or (i == 0 and j == na - 1) or (i == na - 1 and j == 0): continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3): fn(px + dx, py + dy, max(abs(dx), abs(dy)) != 1)
    def fmt(mask):
        d = (2 << 3) | mask  # nivel H = 2
        r = d
        for _ in range(10): r = (r << 1) ^ ((r >> 9) * 0x537)
        b = ((d << 10) | r) ^ 0x5412; g = lambda i: (b >> i) & 1
        for i in range(6): fn(8, i, g(i))
        fn(8, 7, g(6)); fn(8, 8, g(7)); fn(7, 8, g(8))
        for i in range(9, 15): fn(14 - i, 8, g(i))
        for i in range(8): fn(n - 1 - i, 8, g(i))
        for i in range(8, 15): fn(8, n - 15 + i, g(i))
        fn(8, n - 8, True)
    fmt(0)
    if v >= 7:
        r = v
        for _ in range(12): r = (r << 1) ^ ((r >> 11) * 0x1F25)
        b = (v << 12) | r
        for i in range(18):
            a, c = n - 11 + i % 3, i // 3; fn(a, c, (b >> i) & 1); fn(c, a, (b >> i) & 1)
    i = 0
    for right in range(n - 1, 0, -2):
        if right == 6: right = 5
        for vert in range(n):
            for j in range(2):
                x = right - j; up = ((right + 1) & 2) == 0; y = n - 1 - vert if up else vert
                if not F[y][x] and i < len(cws) * 8:
                    M[y][x] = ((cws[i >> 3] >> (7 - (i & 7))) & 1) == 1; i += 1
    cond = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0,
            lambda x, y: (x + y) % 3 == 0, lambda x, y: (x // 3 + y // 2) % 2 == 0,
            lambda x, y: x * y % 2 + x * y % 3 == 0, lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
            lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0]
    def apply(m):
        for y in range(n):
            for x in range(n):
                if not F[y][x] and cond[m](x, y): M[y][x] = not M[y][x]
    def penalty():
        rows = [''.join('1' if c else '0' for c in r) for r in M]
        cols = [''.join('1' if M[y][x] else '0' for y in range(n)) for x in range(n)]
        s = 0
        for ln in rows + cols:
            for m in re.finditer(r'0{5,}|1{5,}', ln): s += len(m.group()) - 2
            s += 40 * (len(re.findall(r'(?=10111010000)', ln)) + len(re.findall(r'(?=00001011101)', ln)))
        for y in range(n - 1):
            for x in range(n - 1):
                if M[y][x] == M[y][x + 1] == M[y + 1][x] == M[y + 1][x + 1]: s += 3
        dark = sum(map(sum, M)); s += (abs(dark * 20 - n * n * 10) + n * n - 1) // (n * n) * 10 - 10
        return s
    best, bm = None, 0
    for m in range(8):
        apply(m); fmt(m); p = penalty(); apply(m)
        if best is None or p < best: best, bm = p, m
    apply(bm); fmt(bm)
    return M

def main():
    url = (sys.argv[1] if len(sys.argv) > 1 else (open('datos/sitio.txt').read().strip() if os.path.exists('datos/sitio.txt') else '')).strip()
    if not url or 'TU-USUARIO' in url:
        print('QR omitido: todavía no hay una dirección real de la tienda.'); return
    rest = url.split('//')[-1]; last = rest.split('/')[-1] if '/' in rest else ''
    if not url.endswith('/') and not re.search(r'[?#]|\.\w+$', last): url += '/'  # evita una redirección al abrir
    v, cws = encode(url); M = build(v, cws); n = len(M)
    color = '#4a0d26'  # vino oscuro (muy buen contraste para que lo lea cualquier celular)
    # --- SVG vectorial para imprimir en cualquier tamaño ---
    q = 4; d = ''.join(f'M{x + q},{y + q}h1v1h-1z' for y in range(n) for x in range(n) if M[y][x])
    open('qr-tienda.svg', 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n + 2 * q} {n + 2 * q}" shape-rendering="crispEdges"><rect width="100%" height="100%" fill="#fff"/><path d="{d}" fill="{color}"/></svg>')
    # --- PNG con el logo en el centro ---
    sc = max(8, 1200 // (n + 2 * q)); W = (n + 2 * q) * sc
    im = Image.new('RGB', (W, W), 'white'); dr = ImageDraw.Draw(im)
    for y in range(n):
        for x in range(n):
            if M[y][x]: dr.rectangle([(x + q) * sc, (y + q) * sc, (x + q + 1) * sc - 1, (y + q + 1) * sc - 1], fill=color)
    if os.path.exists('logo-hd.png'):
        lg = Image.open('logo-hd.png').convert('RGBA'); d0 = int(n * sc * 0.23)  # el logo ocupa ~23% del ancho: el QR sigue siendo legible
        pad = int(d0 * 0.10); disc = d0 + 2 * pad; c = W // 2
        dr.ellipse([c - disc // 2, c - disc // 2, c + disc // 2, c + disc // 2], fill='white')
        lg.thumbnail((d0, d0), Image.LANCZOS); im.paste(lg, (c - lg.width // 2, c - lg.height // 2), lg)
    im.save('qr-tienda.png', optimize=True); print('QR listo para', url, '(versión', v, ')')

main()
