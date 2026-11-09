#!/usr/bin/env python3
"""Foto de grupo do topo da inicial: todas as peças juntas, a partir dos renders de tools/renders.py.
   python3 tools/grupo.py          gera assets/img/pecas/grupo-todas-*.webp
   python3 tools/grupo.py <png>    grava também uma prévia sobre o fundo do site, para conferir"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

RAIZ = Path(__file__).resolve().parent.parent
RENDERS = RAIZ / "_src/renders"
OUT = RAIZ / "assets/img/pecas"
LADO = 1800

# do fundo para a frente: render, centro x, linha do chão, altura em px, sombra (0 = sem), giro em graus
CENA = [
    ("mola-torcao-zinco", 1205, 640, 560, 0, 0),
    ("mola-tracao-aco", 205, 1010, 900, 0.5, 0),
    ("mola-aco", 545, 830, 690, 1, 0),
    ("posicionador-inox", 895, 985, 610, 1, 0),
    ("908-inox", 1400, 1085, 420, 1, 0),
    ("906-aco", 1345, 1610, 365, 1, 0),
    ("bucha-colar-latao", 930, 1500, 435, 1, 0),
    ("910-aco", 435, 1655, 590, 1, 0),
]


def recortar(nome, altura, giro):
    im = Image.open(RENDERS / f"{nome}.png").convert("RGBA")
    if giro:
        im = im.rotate(giro, resample=Image.BICUBIC, expand=True)
    im = im.crop(im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox())
    return im.resize((round(im.width * altura / im.height), altura), Image.LANCZOS)


def sombra(tela, im, cx, chao, forca):
    if not forca:
        return
    larg = max(im.width * 0.86, 90)
    alt = max(im.height * 0.11, 46)
    camada = Image.new("L", tela.size, 0)
    ImageDraw.Draw(camada).ellipse((cx - larg / 2, chao - alt * 0.62, cx + larg / 2, chao + alt * 0.38), fill=round(92 * forca))
    camada = camada.filter(ImageFilter.GaussianBlur(alt * 0.34))
    preto = Image.new("RGBA", tela.size, (17, 18, 21, 0))
    preto.putalpha(camada)
    tela.alpha_composite(preto)


def montar():
    tela = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    for nome, cx, chao, altura, forca, giro in CENA:
        im = recortar(nome, altura, giro)
        sombra(tela, im, cx, chao, forca)
        tela.alpha_composite(im, (round(cx - im.width / 2), chao - im.height))
    return tela


def main():
    tela = montar()
    for w in (480, 800):
        tela.resize((w, w), Image.LANCZOS).save(OUT / f"grupo-todas-{w}.webp", quality=84, method=6)
    tela.resize((300, 300), Image.LANCZOS).save(OUT / "grupo-todas-recorte-300.webp", quality=84, method=6)
    if len(sys.argv) > 1:
        fundo = Image.new("RGBA", tela.size, (236, 238, 240, 255))
        fundo.alpha_composite(tela)
        fundo.convert("RGB").resize((900, 900), Image.LANCZOS).save(sys.argv[1])


if __name__ == "__main__":
    main()
