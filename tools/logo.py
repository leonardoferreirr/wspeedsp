#!/usr/bin/env python3
"""Recorta o logo da W Speed do post do Instagram (_src/post-fabricamos.webp), tira o fundo cinza
com alfa suave (sem serrilhado) e gera: logo (original), logo-negativo (preto vira branco, chama
mantida) e o favicon com o W.  Fonte de cor: o próprio arquivo do cliente, nada redesenhado."""
from pathlib import Path
import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
src = Image.open(RAIZ / "_src/post-fabricamos.webp").convert("RGB")
# W + chama + SPEED, sem o "Peças de Motos" e o telefone
crop = src.crop((430, 38, 1000, 236))
a = np.asarray(crop).astype(np.float32)
fundo = np.array([239.0, 240.0, 242.0])
mn, mx = a.min(axis=2), a.max(axis=2)
sat = (mx - mn) / 255.0
alfa = np.clip(np.maximum((228.0 - mn) / 110.0, (sat - 0.06) * 4.0), 0, 1)
alfa[alfa < 0.04] = 0
# cor do primeiro plano sem o fundo misturado na borda
fg = np.where(alfa[..., None] > 0, (a - (1 - alfa[..., None]) * fundo) / np.maximum(alfa[..., None], 1e-3), 0)
fg = np.clip(fg, 0, 255)
rgba = np.dstack([fg, alfa * 255]).astype(np.uint8)
img = Image.fromarray(rgba, "RGBA")
img = img.crop(img.getbbox())
img.save(RAIZ / "_src/logo-limpo.png")

def salvar(im, nome, alturas):
    for h in alturas:
        w = round(im.width * h / im.height)
        r = im.resize((w, h), Image.LANCZOS)
        r.save(RAIZ / f"assets/img/{nome}-{h}.png", optimize=True)
        r.save(RAIZ / f"assets/img/{nome}-{h}.webp", quality=90, method=6)
    print(nome, im.size, "->", alturas)

salvar(img, "logo", (96, 160))

# negativo: preto/cinza escuro sem cor vira branco, a chama (saturada) fica
arr = np.asarray(img).astype(np.float32)
mn, mx = arr[..., :3].min(axis=2), arr[..., :3].max(axis=2)
neutro = (mx - mn) < 40
inv = arr.copy()
inv[neutro, 0:3] = 255 - arr[neutro, 0:3] * 0.15
salvar(Image.fromarray(inv.astype(np.uint8), "RGBA"), "logo-negativo", (96, 160))

# favicon: o W
W = img.crop((int(img.width * 0.44), 0, int(img.width * 0.84), int(img.height * 0.5)))
W = W.crop(W.getbbox())
lado = max(W.size) + 24
fav = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
fav.paste(W, ((lado - W.width) // 2, (lado - W.height) // 2), W)
for s in (32, 180, 512):
    fav.resize((s, s), Image.LANCZOS).save(RAIZ / f"assets/img/icone-{s}.png", optimize=True)
fav.resize((48, 48), Image.LANCZOS).save(RAIZ / "favicon.ico")
print("favicon ok")
