#!/usr/bin/env python3
"""Gera as imagens das peças (aço e inox) pelo mesmo motor 3D do site.
   quadrado/ : enquadramento igual ao do visor 3D (o pôster vira o 3D sem pulo)
   recorte/  : justo na peça, para os cards e a prateleira
   python3 tools/renders.py                    (todas)
   python3 tools/renders.py bucha bucha-colar  (só esses tipos)"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
OUT = RAIZ / "assets/img/pecas"
TMP = RAIZ / "_src/renders"
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)

BASE = {
    "906": {"rosca": "1/2\"-14", "tipoRosca": "bspt", "L": 10, "S": 10, "T": 5, "W": 2},
    "908": {"rosca": "1/2\"-14", "tipoRosca": "bsp", "D": 26, "C": 4, "L": 14, "S": 10, "T": 7.5},
    "910": {"rosca": "1/2\"-14", "tipoRosca": "bsp", "D": 26, "M": 8, "L": 14, "C": 4, "S": 19},
    "posicionador": {"rosca": "M8", "L": 20, "D2": 5, "l1": 1.5},
    "mola": {"fio": 2, "De": 18, "voltas": 9, "Lo": 46},
    # proporções tiradas das fotos do cliente; no site não aparecem como medida de catálogo
    "bucha": {"de": 14, "pe": 1.75, "di": 8.5, "pi": 1.5, "L": 24},
    "bucha-colar": {"de": 14, "pe": 1.75, "di": 9.5, "pi": 1.5, "L": 15, "D": 18, "C": 2.8},
    # molas: proporções tiradas das fotos do cliente; também não são medidas de catálogo
    "mola-reforcada": {"fio": 4, "De": 40, "voltas": 4.5, "Lo": 38},
    "mola-aberta": {"fio": 1.8, "De": 30, "voltas": 5.5, "Lo": 62},
    "mola-barril": {"fio": 1.2, "De": 16, "barril": 8.5, "voltas": 32, "Lo": 80},
    "mola-pequena": {"fio": 0.8, "De": 15, "voltas": 9, "Lo": 24},
    "mola-tracao": {"fio": 1.2, "De": 10, "voltas": 26.5, "hasteA": 40, "hasteB": 17, "gancho": 4.2, "cauda": 5},
    "mola-torcao": {"fio": 2, "De": 40, "voltas": 4, "perna": 56, "dobraAng": 70, "ponta": 14, "volta": 9, "inclina": -24},
}
ANG = {"posicionador": (1.4, 0.36), "mola": (0.2, 0.28), "bucha": (-0.5, 0.72), "bucha-colar": (-0.5, 0.72),
       "mola-reforcada": (0.2, 0.42), "mola-aberta": (0.2, 0.36), "mola-barril": (0.2, 0.2), "mola-pequena": (0.2, 0.36),
       "mola-tracao": (-0.45, 0.14), "mola-torcao": (-0.32, 0.34)}
MATS = {"bucha": ("aco", "latao"), "bucha-colar": ("aco", "latao"),
        "mola-reforcada": ("aco",), "mola-aberta": ("aco",), "mola-barril": ("zinco",), "mola-pequena": ("inox",),
        "mola-tracao": ("aco", "zinco"), "mola-torcao": ("zinco",)}
SO = set(sys.argv[1:])
lista = []
for tipo, dims in BASE.items():
    if SO and tipo not in SO:
        continue
    for mat in MATS.get(tipo, ("aco", "inox")):
        yaw, pitch = ANG.get(tipo, (-0.5, 0.42))
        lista.append({"nome": f"{tipo}-{mat}", "tipo": tipo, "dims": dims, "material": mat, "yaw": yaw, "pitch": pitch, "w": 1100, "h": 1100})
(TMP / "lista.json").write_text(json.dumps(lista))
subprocess.run(["node", str(RAIZ / "tools/render.mjs"), str(TMP), str(TMP / "lista.json")], check=True)

for it in lista:
    im = Image.open(TMP / f"{it['nome']}.png").convert("RGBA")
    for w in (480, 800):
        im.resize((w, w), Image.LANCZOS).save(OUT / f"{it['nome']}-{w}.webp", quality=84, method=6)
    caixa = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    pad = 18
    rec = im.crop((max(0, caixa[0] - pad), max(0, caixa[1] - pad), min(im.width, caixa[2] + pad), min(im.height, caixa[3] + pad)))
    for h in (300, 520):
        rw = round(rec.width * h / rec.height)
        rec.resize((rw, h), Image.LANCZOS).save(OUT / f"{it['nome']}-recorte-{h}.webp", quality=84, method=6)
    print(it["nome"], "recorte", rec.size)
