#!/usr/bin/env python3
"""Imagem de compartilhamento 1200x630 (link no WhatsApp/Instagram): logo, título e as quatro peças."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RAIZ = Path(__file__).resolve().parent.parent
W, H = 1200, 630
im = Image.new("RGB", (W, H), "#eceef0")
d = ImageDraw.Draw(im)
for pts, cor in [([(0, 0), (420, 0), (160, H), (0, H)], "#e5e7ea"), ([(840, 0), (W, 0), (W, 360), (930, H), (590, H)], "#f2f3f5")]:
    d.polygon(pts, fill=cor)
logo = Image.open(RAIZ / "assets/img/logo-160.png").convert("RGBA")
logo = logo.resize((round(logo.width * 84 / logo.height), 84), Image.LANCZOS)
im.paste(logo, (64, 56), logo)
fonte = lambda peso, tam: ImageFont.truetype(str(Path.home() / f"Library/Fonts/Poppins-{peso}.ttf"), tam)
y = 196
d.text((64, y), "Fabricamos", font=fonte("SemiBold", 52), fill="#141518"); y += 64
for linha in ["bujões DIN 906, 908 e 910", "e posicionadores com", "mola e esfera"]:
    d.text((64, y), linha, font=fonte("Light", 46), fill="#141518"); y += 58
grad = Image.new("RGB", (64, 5))
for x in range(64):
    t = x / 63
    grad.putpixel((x, 0), (round(255 + (229 - 255) * t), round(138 + (38 - 138) * t), round(31 + (27 - 31) * t)))
grad = grad.resize((64, 5))
for yy in range(5):
    for x in range(64):
        grad.putpixel((x, yy), grad.getpixel((x, 0)))
im.paste(grad, (64, y + 16))
d.text((64, y + 44), "Aço oxidado e inox, com envio para todo o Brasil", font=fonte("Regular", 22), fill="#4b4f57")
# peças em fila, apoiadas na mesma linha e alinhadas à direita
base, gap, pecas = 500, 10, []
for tipo, h in (("910", 150), ("908", 122), ("906", 106), ("posicionador", 205)):
    p = Image.open(RAIZ / f"assets/img/pecas/{tipo}-aco-recorte-520.webp").convert("RGBA")
    pecas.append(p.resize((round(p.width * h / p.height), h), Image.LANCZOS))
x = 1150 - sum(p.width for p in pecas) - gap * (len(pecas) - 1)
for p in pecas:
    sombra = Image.new("RGBA", (p.width, 40), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).ellipse((p.width * .12, 10, p.width * .88, 30), fill=(17, 18, 21, 90))
    sombra = sombra.filter(ImageFilter.GaussianBlur(6))
    im.paste(sombra, (x, base - 24), sombra)
    im.paste(p, (x, base - p.height), p)
    x += p.width + gap
im.save(RAIZ / "assets/img/og-image.jpg", quality=88, optimize=True, progressive=True)
print("og-image.jpg", im.size)
