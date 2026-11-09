#!/usr/bin/env python3
"""Monta o site da W Speed (linha industrial): início, uma página por peça (DIN 906, 908, 910 e
posicionador com mola e esfera) com 3D, desenho técnico e tabela de medidas, molas de compressão,
usinagem sob medida e a ponte /obrigado para o WhatsApp.

    python3 build.py

Medidas em _src/produtos.json. As imagens das peças saem do mesmo motor 3D do site
(tools/renders.py) e o 3D ao vivo (assets/js/pecas3d.js) só carrega na primeira interação.
O CSS vai minificado para dentro do <head>; site.js e pecas3d.js levam o hash no endereço.
"""
import hashlib, json, re
from datetime import date
from html import escape as e, unescape
from pathlib import Path

RAIZ = Path(__file__).parent
DOMINIO = "https://www.wfixspeed.com.br"
INDEXAR = True
INDEXNOW_KEY = "d017e735a97a7fcd2143f5992b725323"   # pública por definição: o Bing confirma o site em /<chave>.txt
NOMES_ALT = ["WFix Speed", "W Fix Speed", "wfix.speed"]   # como a marca aparece no domínio e no Instagram
WHATSAPP = "5511988904107"       # do post e do perfil @wfix.speed
TEL_VER = "(11) 98890-4107"
INSTAGRAM = "https://www.instagram.com/wfix.speed"
GTM_ID = ""                      # quando houver tráfego pago: GTM-XXXXXXX (entra em todas as páginas e no /obrigado)
CSS, JS_FONTE, JS, JS3D = RAIZ / "assets/css/site.css", RAIZ / "assets/js/site.js", RAIZ / "assets/js/site.min.js", RAIZ / "assets/js/pecas3d.js"
ESBUILD = RAIZ / "tools/pecas3d/node_modules/.bin/esbuild"
DADOS = json.loads((RAIZ / "_src/produtos.json").read_text())
PRODUTOS = DADOS["produtos"]
POR_SLUG = {p["slug"]: p for p in PRODUTOS}

# ------------------------------------------------------------------ ícones (traço fino, 24x24)
I = {
    "carrinho": '<path d="M3 4h2.2l2.3 11h10.8L21 7.5H6.6"/><circle cx="9.5" cy="19" r="1.4"/><circle cx="17" cy="19" r="1.4"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h10"/>',
    "fechar": '<path d="M6 6l12 12M18 6L6 18"/>',
    "mais": '<path d="M12 5v14M5 12h14"/>',
    "menos": '<path d="M5 12h14"/>',
    "chev": '<path d="M6 9l6 6 6-6"/>',
    "giro": '<path d="M4 12a8 8 0 0 1 14-5.3M20 12a8 8 0 0 1-14 5.3"/><path d="M18 3v4h-4M6 21v-4h4"/>',
    "caixa": '<path d="M3 7l9-4 9 4v10l-9 4-9-4z"/><path d="M3 7l9 4 9-4M12 11v10"/>',
    "baixo": '<path d="M12 5v14M6 13l6 6 6-6"/>',
}
SETA = '<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M2 8h11M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5"/></svg>'
PONTA = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5h8l6 7-6 7H5l6-7z" fill="currentColor"/></svg>'  # a seta do "D" do logo
ZAP = ('<svg class="zap" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.4.8 3.2.6a2.8 2.8 0 0 0 1.8-1.3 2.3 2.3 0 0 0 .2-1.3c-.1-.1-.3-.2-.6-.3z"/></svg>')


def ic(nome, sw=1.5):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{I[nome]}</svg>'


def minificar(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};:,>])\s*", r"\1", css)
    return css.replace(";}", "}").strip()


def hash_de(p):
    return hashlib.sha1(p.read_bytes()).hexdigest()[:10]


def num(v):
    if isinstance(v, str):
        return v
    if float(v).is_integer():
        return str(int(v))
    return f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def zap_link(contexto):
    return f"/obrigado?c={contexto}"


def btn(txt, href, tipo="escuro", icone="seta", extra=""):
    ico = ZAP if icone == "zap" else (SETA if icone == "seta" else (ic(icone) if icone else ""))
    if icone == "zap":
        return f'<a class="btn btn--{tipo}" href="{href}"{extra}>{ico}<span>{txt}</span></a>'
    return f'<a class="btn btn--{tipo}" href="{href}"{extra}><span>{txt}</span>{ico}</a>'


def img_peca(tipo, mat="aco", recorte=False, alt="", lazy=True, sizes="", h=300, cls=""):
    if recorte:
        src = f"/assets/img/pecas/{tipo}-{mat}-recorte-{h}.webp"
        carga = 'loading="lazy" ' if lazy else ""
        return f'<img class="{cls}" src="{src}" alt="{e(alt)}" height="{h}" {carga}decoding="async">'
    base = f"/assets/img/pecas/{tipo}-{mat}"
    carga = 'loading="lazy" ' if lazy else 'fetchpriority="high" '
    tam = sizes or "(max-width:900px) 92vw, 560px"
    return (f'<img class="{cls}" src="{base}-800.webp" srcset="{base}-480.webp 480w, {base}-800.webp 800w" sizes="{tam}" '
            f'width="800" height="800" alt="{e(alt)}" {carga}decoding="async">')


def dims_recorte(tipo, mat="aco", h=300):
    from PIL import Image
    im = Image.open(RAIZ / f"assets/img/pecas/{tipo}-{mat}-recorte-{h}.webp")
    return im.size


# molas: proporções tiradas das fotos do cliente, para desenhar o 3D; não são medidas de catálogo
MOLA_3D = {
    "mola": {"material": "aco", "yaw": 0.2, "pitch": 0.28, "dims": {"fio": 2, "De": 18, "voltas": 9, "Lo": 46}},
    "mola-reforcada": {"material": "aco", "yaw": 0.2, "pitch": 0.42, "dims": {"fio": 4, "De": 40, "voltas": 4.5, "Lo": 38}},
    "mola-aberta": {"material": "aco", "yaw": 0.2, "pitch": 0.36, "dims": {"fio": 1.8, "De": 30, "voltas": 5.5, "Lo": 62}},
    "mola-barril": {"material": "zinco", "yaw": 0.2, "pitch": 0.2, "dims": {"fio": 1.2, "De": 16, "barril": 8.5, "voltas": 32, "Lo": 80}},
    "mola-pequena": {"material": "inox", "yaw": 0.2, "pitch": 0.36, "dims": {"fio": 0.8, "De": 15, "voltas": 9, "Lo": 24}},
    "mola-tracao": {"material": "aco", "yaw": -0.45, "pitch": 0.14, "dims": {"fio": 1.2, "De": 10, "voltas": 26.5, "hasteA": 40, "hasteB": 17, "gancho": 4.2, "cauda": 5}},
    "mola-torcao": {"material": "zinco", "yaw": -0.32, "pitch": 0.34, "dims": {"fio": 2, "De": 40, "voltas": 4, "perna": 56, "dobraAng": 70, "ponta": 14, "volta": 9, "inclina": -24}},
}


def sombras():
    """Altura da sombra no palco: logo abaixo do pé de cada peça no pôster (mesmo enquadramento do 3D)."""
    from PIL import Image
    out = {}
    for t in ("906", "908", "910", "posicionador", "bucha", "bucha-colar", *MOLA_3D):
        mat = "aco" if t.startswith("bucha") else MOLA_3D[t]["material"] if t in MOLA_3D else "aco"
        im = Image.open(RAIZ / f"assets/img/pecas/{t}-{mat}-800.webp").convert("RGBA")
        baixo = im.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox()[3] / im.height
        out[t] = f"{max(2.0, (1 - baixo) * 100 - 4.5):.1f}%"
    return out


SOMBRA = sombras()


# ------------------------------------------------------------------ dados das tabelas
SUFIXO = {"bspt": " BSPT", "nptf": " NPTF", "metrica-conica": " cônica", "bsp": " BSP", "metrica": "", "metrica-grossa": ""}


def chave_col(c):
    return c.split()[0]


def linha_dims(p, tab, row):
    if p["tipo"] == "posicionador":
        return {"rosca": row[0], "L": row[1], "D2": row[2], "l1": row[3]}
    dm = {"rosca": row[0], "tipoRosca": tab["rosca"]}
    for c, v in zip(tab["cab"][1:], row[1:]):
        dm[chave_col(c)] = v
    return dm


def linha_detalhe(p, tab, row):
    if p["tipo"] == "posicionador":
        return f"{row[0]} × {num(row[1])}"
    return f"rosca {row[0]}{SUFIXO[tab['rosca']]}"


def linha_medidas(p, tab, row):
    partes = []
    for c, v in zip(tab["cab"][1:], row[1:]):
        k = chave_col(c)
        un = "" if isinstance(v, str) else (" N" if k == "F" else " mm")
        partes.append(f'<span><b>{e(k)}</b> {e(num(v))}{un}</span>')
    return "".join(partes)


def linha_padrao(p, tab):
    alvo = {"posicionador": "M8"}.get(p["tipo"])
    for i, row in enumerate(tab["linhas"]):
        if p["tipo"] == "posicionador":
            if row[0] == "M8" and row[1] == 20:
                return i
        elif str(row[0]).startswith('1/2"') or str(row[0]).startswith("M16 "):
            return i
    return min(len(tab["linhas"]) - 1, 3)


def dims_padrao(p):
    tab = p["tabelas"][0]
    return linha_dims(p, tab, tab["linhas"][linha_padrao(p, tab)])


# ------------------------------------------------------------------ desenhos técnicos (SVG)
TRACO, COTA, CENTRO = "#24262b", "#d9361a", "#9aa0a8"


def svg_ini(vb, rotulo):
    return (f'<svg viewBox="{vb}" role="img" aria-label="{e(rotulo)}" xmlns="http://www.w3.org/2000/svg">'
            f'<defs><marker id="pt" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            f'<path d="M0 1.5L10 5 0 8.5z" fill="{COTA}"/></marker></defs>')


def cota(x1, y1, x2, y2, letra, tx, ty, ancora="middle"):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{COTA}" stroke-width="1.1" marker-start="url(#pt)" marker-end="url(#pt)"/>'
            f'<text x="{tx}" y="{ty}" text-anchor="{ancora}" fill="{COTA}" font-size="17" font-weight="500" font-family="Poppins,Arial,sans-serif">{letra}</text>')


def ext(*segs):
    return "".join(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="{COTA}" stroke-width=".7" opacity=".7"/>' for a, b, c, d in segs)


def linhas(segs, cor=TRACO, w=1.6, dash=""):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return "".join(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="{cor}" stroke-width="{w}"{da}/>' for a, b, c, d in segs)


def caminho(d, w=1.6, cor=TRACO, dash="", fill="none"):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="{fill}" stroke="{cor}" stroke-width="{w}" stroke-linejoin="round"{da}/>'


def hexagono(cx, cy, a, flats_verticais=True):
    import math
    R = a / math.cos(math.pi / 6)
    pts = []
    for k in range(6):
        ang = math.radians(30 + 60 * k) if flats_verticais else math.radians(60 * k)
        pts.append(f"{cx + R * math.cos(ang):.1f},{cy - R * math.sin(ang):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="none" stroke="{TRACO}" stroke-width="1.6"/>'


def centros(cx, cy, r):
    return linhas([(cx - r, cy, cx + r, cy), (cx, cy - r, cx, cy + r)], CENTRO, .8, "12 3 2 3")


def texto(x, y, t, tam=13, cor="#73787f", ancora="middle"):
    return f'<text x="{x}" y="{y}" text-anchor="{ancora}" fill="{cor}" font-size="{tam}" font-family="Poppins,Arial,sans-serif">{t}</text>'


def desenho_906():
    s = svg_ini("0 0 560 300", "Desenho técnico do bujão DIN 906 com as medidas L, S, T e W")
    cx, cy = 140, 150
    s += centros(cx, cy, 116)
    s += f'<circle cx="{cx}" cy="{cy}" r="92" fill="none" stroke="{TRACO}" stroke-width="1.6"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="83" fill="none" stroke="{TRACO}" stroke-width=".8"/>'
    s += hexagono(cx, cy, 40)
    s += ext((cx - 40, cy + 12, cx - 40, cy + 124), (cx + 40, cy + 12, cx + 40, cy + 124))
    s += cota(cx - 40, cy + 118, cx + 40, cy + 118, "S", cx, cy + 142)
    # vista lateral (cônica)
    x0, x1, yt, yb = 308, 492, 92, 202
    s += caminho(f"M{x0+6} {yt} H{x1-6} L{x1} {yt+6} L{x1-7} {yb-6} L{x1-13} {yb} H{x0+13} L{x0+7} {yb-6} L{x0} {yt+6} Z")
    s += linhas([(x0 + 9, yt + 6, x0 + 15, yb - 6), (x1 - 9, yt + 6, x1 - 15, yb - 6)], TRACO, .8)
    s += caminho(f"M360 {yt} V{yt+50} L400 {yt+74} L440 {yt+50} V{yt}", 1.1, TRACO, "5 3")
    s += linhas([(360, yt + 50, 440, yt + 50)], TRACO, 1.1, "5 3")
    s += linhas([(400, yt - 14, 400, yb + 14)], CENTRO, .8, "12 3 2 3")
    s += ext((x1, yt, 532, yt), (x1 - 13, yb, 532, yb))
    s += cota(524, yt, 524, yb, "L", 540, (yt + yb) / 2 + 6, "start")
    s += ext((x0, yt, 270, yt), (360, yt + 50, 270, yt + 50), (400, yt + 74, 270, yt + 74), (x0 + 13, yb, 270, yb))
    s += cota(280, yt, 280, yt + 50, "T", 262, yt + 31, "end")
    s += cota(280, yt + 74, 280, yb, "W", 262, (yt + 74 + yb) / 2 + 6, "end")
    s += ext((x0 + 13, yb, x0 + 13, 238), (x1 - 13, yb, x1 - 13, 238))
    s += f'<line x1="{x0+13}" y1="232" x2="{x1-13}" y2="232" stroke="{COTA}" stroke-width="1.1" marker-start="url(#pt)" marker-end="url(#pt)"/>'
    s += texto(400, 256, "rosca cônica", 14, COTA)
    return s + "</svg>"


def desenho_908():
    s = svg_ini("0 0 560 300", "Desenho técnico do bujão DIN 908 com as medidas D, C, L, S e T")
    cx, cy = 140, 156
    s += centros(cx, cy, 116)
    s += f'<circle cx="{cx}" cy="{cy}" r="96" fill="none" stroke="{TRACO}" stroke-width="1.6"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="90" fill="none" stroke="{TRACO}" stroke-width=".8"/>'
    s += hexagono(cx, cy, 32)
    s += ext((cx - 96, cy, cx - 96, 30), (cx + 96, cy, cx + 96, 30))
    s += cota(cx - 96, 36, cx + 96, 36, "D", cx, 26)
    s += ext((cx - 32, cy + 12, cx - 32, cy + 126), (cx + 32, cy + 12, cx + 32, cy + 126))
    s += cota(cx - 32, cy + 120, cx + 32, cy + 120, "S", cx, cy + 143)
    # lateral
    yc, yr, yb = 70, 100, 222
    s += caminho(f"M309 {yc} H491 L496 {yc+5} V{yr} H304 V{yc+5} Z")
    s += caminho(f"M344 {yr} V{yr+8} H338 V{yb-6} L344 {yb} H456 L462 {yb-6} V{yr+8} H456 V{yr}")
    s += linhas([(346, yr + 10, 346, yb - 4), (454, yr + 10, 454, yb - 4)], TRACO, .8)
    s += caminho(f"M366 {yc} V{yc+64} L400 {yc+84} L434 {yc+64} V{yc}", 1.1, TRACO, "5 3")
    s += linhas([(366, yc + 64, 434, yc + 64)], TRACO, 1.1, "5 3")
    s += linhas([(400, yc - 14, 400, yb + 14)], CENTRO, .8, "12 3 2 3")
    s += ext((496, yc, 534, yc), (496, yr, 534, yr), (462, yb, 534, yb))
    s += cota(526, yc, 526, yr, "C", 540, (yc + yr) / 2 + 6, "start")
    s += cota(526, yr, 526, yb, "L", 540, (yr + yb) / 2 + 6, "start")
    s += ext((304, yc, 272, yc), (366, yc + 64, 272, yc + 64))
    s += cota(282, yc, 282, yc + 64, "T", 264, yc + 38, "end")
    s += ext((338, yb, 338, 252), (462, yb, 462, 252))
    s += f'<line x1="338" y1="246" x2="462" y2="246" stroke="{COTA}" stroke-width="1.1" marker-start="url(#pt)" marker-end="url(#pt)"/>'
    s += texto(400, 270, "rosca", 14, COTA)
    return s + "</svg>"


def desenho_910():
    s = svg_ini("0 0 560 300", "Desenho técnico do bujão DIN 910 com as medidas D, M, L, C e S")
    cx, cy = 140, 156
    s += centros(cx, cy, 116)
    s += f'<circle cx="{cx}" cy="{cy}" r="96" fill="none" stroke="{TRACO}" stroke-width="1.6"/>'
    s += hexagono(cx, cy, 70)
    s += f'<circle cx="{cx}" cy="{cy}" r="66" fill="none" stroke="{TRACO}" stroke-width=".8"/>'
    s += ext((cx - 96, cy, cx - 96, 30), (cx + 96, cy, cx + 96, 30))
    s += cota(cx - 96, 36, cx + 96, 36, "D", cx, 26)
    s += ext((cx - 70, cy + 20, cx - 70, cy + 126), (cx + 70, cy + 20, cx + 70, cy + 126))
    s += cota(cx - 70, cy + 120, cx + 70, cy + 120, "S", cx, cy + 143)
    # lateral
    yh, yc, yr, yb = 52, 90, 112, 224
    s += caminho(f"M319 {yh+5} Q319 {yh} 326 {yh} H474 Q481 {yh} 481 {yh+5} V{yc} H319 Z")
    s += linhas([(360, yh, 360, yc), (440, yh, 440, yc)], TRACO, 1.3)
    s += caminho(f"M326 {yh} Q340 {yh+9} 360 {yh+2} M360 {yh+2} Q400 {yh+12} 440 {yh+2} M440 {yh+2} Q460 {yh+9} 474 {yh}", .8)
    s += caminho(f"M309 {yc} H491 L496 {yc+5} V{yr} H304 V{yc+5} Z")
    s += caminho(f"M344 {yr} V{yr+8} H338 V{yb-6} L344 {yb} H456 L462 {yb-6} V{yr+8} H456 V{yr}")
    s += linhas([(346, yr + 10, 346, yb - 4), (454, yr + 10, 454, yb - 4)], TRACO, .8)
    s += linhas([(400, yh - 14, 400, yb + 14)], CENTRO, .8, "12 3 2 3")
    s += ext((481, yh, 534, yh), (496, yc, 534, yc), (496, yr, 534, yr), (462, yb, 534, yb))
    s += cota(526, yh, 526, yc, "M", 540, (yh + yc) / 2 + 6, "start")
    s += cota(526, yc, 526, yr, "C", 540, (yc + yr) / 2 + 6, "start")
    s += cota(526, yr, 526, yb, "L", 540, (yr + yb) / 2 + 6, "start")
    s += ext((338, yb, 338, 254), (462, yb, 462, 254))
    s += f'<line x1="338" y1="248" x2="462" y2="248" stroke="{COTA}" stroke-width="1.1" marker-start="url(#pt)" marker-end="url(#pt)"/>'
    s += texto(400, 272, "rosca", 14, COTA)
    return s + "</svg>"


def desenho_posicionador():
    s = svg_ini("0 0 560 270", "Desenho técnico do posicionador com mola e esfera com as medidas d1, L, D2 e l1")
    x0, x1, yt, yb, cy = 132, 448, 95, 175, 135
    s += linhas([(80, cy, 500, cy)], CENTRO, .8, "12 3 2 3")
    s += caminho(f"M{x0+6} {yt} H{x1-6} L{x1} {yt+6} V{yb-6} L{x1-6} {yb} H{x0+6} L{x0} {yb-6} V{yt+6} Z")
    s += linhas([(x0 + 8, yt + 7, x1 - 8, yt + 7), (x0 + 8, yb - 7, x1 - 8, yb - 7)], TRACO, .8)
    s += linhas([(x1 - 30, cy - 7, x1, cy - 7), (x1 - 30, cy + 7, x1, cy + 7), (x1 - 30, cy - 7, x1 - 30, cy + 7)], TRACO, 1.3)
    s += caminho(f"M{x0} {cy-24} H{x0+210} M{x0} {cy+24} H{x0+210} M{x0+210} {cy-24} V{cy+24}", 1.1, TRACO, "5 3")
    mola = "M168 135 " + " ".join(f"L{176 + 16 * i} {cy - 18 if i % 2 == 0 else cy + 18}" for i in range(10)) + f" L{176+16*10} 135"
    s += caminho(mola, 1, "#73787f")
    rb = 25
    bx = x0 - 15 + rb
    s += f'<circle cx="{bx}" cy="{cy}" r="{rb}" fill="#f7f8f9" stroke="{TRACO}" stroke-width="1.6"/>'
    s += ext((x0, yb, x0, 226), (x1, yb, x1, 226))
    s += cota(x0, 218, x1, 218, "L", (x0 + x1) / 2, 244)
    s += ext((x0 - 15, cy, x0 - 15, 52), (x0, yt, x0, 52))
    s += cota(x0 - 15, 60, x0, 60, "", 0, 0)
    s += texto(x0 - 22, 44, "l1", 17, COTA, "end").replace('font-family', 'font-weight="500" font-family')
    s += ext((bx, cy - rb, 60, cy - rb), (bx, cy + rb, 60, cy + rb))
    s += cota(70, cy - rb, 70, cy + rb, "D2", 58, cy + 6, "end")
    s += ext((x1, yt, 530, yt), (x1, yb, 530, yb))
    s += cota(520, yt, 520, yb, "d1", 512, cy + 6, "end")
    return s + "</svg>"


def desenho_mola():
    s = svg_ini("0 0 560 300", "Como medir a mola: arame d, diâmetro externo De e comprimento livre Lo")
    xl, xr, y0, y1, n = 190, 370, 44, 256, 9
    passo = (y1 - y0) / n
    for i in range(n):
        ya = y0 + i * passo
        s += f'<line x1="{xl+6}" y1="{ya+passo:.1f}" x2="{xr-6}" y2="{ya:.1f}" stroke="#9da2aa" stroke-width="9" stroke-linecap="round"/>'
    for i in range(n + 1):
        ya = y0 + i * passo
        if i < n:
            s += f'<line x1="{xl+6}" y1="{ya:.1f}" x2="{xr-6}" y2="{ya+passo:.1f}" stroke="{TRACO}" stroke-width="10" stroke-linecap="round"/>'
    s += ext((xl, y0, xl, 18), (xr, y0, xr, 18))
    s += cota(xl, 24, xr, 24, "De", (xl + xr) / 2, 16)
    s += ext((xr, y0, 420, y0), (xr, y1, 420, y1))
    s += cota(412, y0, 412, y1, "Lo", 426, (y0 + y1) / 2 + 6, "start")
    yy = y0 + passo * 4
    s += ext((xl + 2, yy - 5, 140, yy - 5), (xl + 2, yy + 5, 140, yy + 5))
    s += f'<line x1="150" y1="{yy-26}" x2="150" y2="{yy-5}" stroke="{COTA}" stroke-width="1.1" marker-end="url(#pt)"/>'
    s += f'<line x1="150" y1="{yy+26}" x2="150" y2="{yy+5}" stroke="{COTA}" stroke-width="1.1" marker-end="url(#pt)"/>'
    s += texto(136, yy + 6, "d", 17, COTA, "end").replace('font-family', 'font-weight="500" font-family')
    return s + "</svg>"


def desenho_tracao():
    s = svg_ini("0 0 560 300", "Como medir a mola de tração: arame d, diâmetro externo De, comprimento total L e corpo Lc")
    for x in range(194, 368, 9):
        s += f'<line x1="{x}" y1="112" x2="{x+4}" y2="188" stroke="{TRACO}" stroke-width="7" stroke-linecap="round"/>'
    s += caminho("M192 186 H92 A22 22 0 0 1 92 142 H110", 4.5)
    s += caminho("M368 114 H468 A22 22 0 0 1 468 158 H450", 4.5)
    s += ext((70, 150, 70, 40), (490, 136, 490, 40))
    s += cota(70, 46, 490, 46, "L", 280, 38)
    s += ext((190, 110, 148, 110), (190, 190, 148, 190))
    s += cota(156, 110, 156, 190, "De", 146, 156, "end")
    s += ext((190, 192, 190, 254), (370, 192, 370, 254))
    s += cota(190, 248, 370, 248, "Lc", 280, 272)
    s += ext((272, 192, 272, 226), (280, 192, 280, 226))
    s += f'<line x1="250" y1="218" x2="272" y2="218" stroke="{COTA}" stroke-width="1.1" marker-end="url(#pt)"/>'
    s += f'<line x1="302" y1="218" x2="280" y2="218" stroke="{COTA}" stroke-width="1.1" marker-end="url(#pt)"/>'
    s += texto(308, 224, "d", 17, COTA, "start").replace('font-family', 'font-weight="500" font-family')
    return s + "</svg>"


def desenho_torcao():
    s = svg_ini("0 0 560 300", "Como medir a mola de torção: arame d, diâmetro externo De e comprimento da perna L")
    s += f'<circle cx="280" cy="170" r="76" fill="none" stroke="{TRACO}" stroke-width="9"/>'
    s += f'<circle cx="280" cy="170" r="67" fill="none" stroke="{TRACO}" stroke-width="1"/>'
    s += caminho("M280 90 H96 L76 140 A7.5 7.5 0 0 0 90 146 L102 116", 4.5)
    s += caminho("M280 90 H464 L484 140 A7.5 7.5 0 0 1 470 146 L458 116", 4.5)
    s += ext((280, 86, 280, 40), (464, 86, 464, 40))
    s += cota(280, 46, 464, 46, "L", 372, 38)
    s += ext((204, 180, 204, 276), (356, 180, 356, 276))
    s += cota(204, 268, 356, 268, "De", 280, 292)
    s += f'<line x1="170" y1="58" x2="170" y2="87" stroke="{COTA}" stroke-width="1.1" marker-end="url(#pt)"/>'
    s += f'<line x1="170" y1="122" x2="170" y2="93" stroke="{COTA}" stroke-width="1.1" marker-end="url(#pt)"/>'
    s += texto(158, 74, "d", 17, COTA, "end").replace('font-family', 'font-weight="500" font-family')
    return s + "</svg>"


def desenho_usinagem():
    """Eixo escalonado que se desenha sozinho quando entra na tela."""
    s = svg_ini("0 0 600 300", "Desenho técnico de uma peça usinada sob medida")
    t = lambda d, atraso=0: f'<path class="traco" pathLength="1" d="{d}" fill="none" stroke="{TRACO}" stroke-width="1.6" stroke-linejoin="round" style="--d:{atraso}s"/>'
    cy = 140
    s += f'<path class="traco" pathLength="1" d="M40 {cy} H560" stroke="{CENTRO}" stroke-width=".8" stroke-dasharray="12 3 2 3" fill="none" style="--d:0s"/>'
    s += t(f"M70 {cy-26} H150 V{cy-46} H300 V{cy-36} H330 V{cy-30} H360 V{cy-36} H440 V{cy-20} H520 L528 {cy-12} V{cy+12} L520 {cy+20} H440 V{cy+36} H360 V{cy+30} H330 V{cy+36} H300 V{cy+46} H150 V{cy+26} H70 L62 {cy+18} V{cy-18} Z", .2)
    s += t(f"M150 {cy-46} V{cy+46} M300 {cy-36} V{cy+36} M440 {cy-20} V{cy+20}", .9)
    s += t(f"M70 {cy-20} H150 M70 {cy+20} H150", 1.2)
    s += t(f"M460 {cy-8} H500 M460 {cy+8} H500 M460 {cy-8} A8 8 0 0 0 460 {cy+8} M500 {cy-8} A8 8 0 0 1 500 {cy+8}", 1.4)
    c = '<g class="cota">'
    for xa, xb, lbl in ((70, 150, "20"), (150, 300, "38"), (300, 440, "35"), (440, 528, "22")):
        c += ext((xa, cy + 50, xa, 232), (xb, cy + 50, xb, 232))
        c += f'<line x1="{xa}" y1="226" x2="{xb}" y2="226" stroke="{COTA}" stroke-width="1.1" marker-start="url(#pt)" marker-end="url(#pt)"/>'
        c += texto((xa + xb) / 2, 250, lbl, 14, COTA)
    for x, r, lbl in ((110, 26, "Ø 26"), (225, 46, "Ø 46"), (400, 36, "Ø 36"), (490, 20, "Ø 20h7")):
        c += f'<line x1="{x}" y1="{cy-r}" x2="{x}" y2="{cy+r}" stroke="{COTA}" stroke-width="1.1" marker-start="url(#pt)" marker-end="url(#pt)"/>'
        c += texto(x, cy - r - 10, lbl, 13, COTA)
    c += texto(560, 290, "medidas em mm", 12, "#9aa0a8", "end")
    c += "</g>"
    return s + c + "</svg>"


def desenho_bucha():
    s = svg_ini("0 0 560 300", "Desenho técnico da bucha roscada com as medidas d1, d2, L, D e C")
    cx, cy = 130, 156
    s += centros(cx, cy, 112)
    s += f'<circle cx="{cx}" cy="{cy}" r="96" fill="none" stroke="{TRACO}" stroke-width="1.6"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="60" fill="none" stroke="{TRACO}" stroke-width=".8"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="50" fill="none" stroke="{TRACO}" stroke-width="1.6"/>'
    s += ext((cx - 96, cy, cx - 96, 30), (cx + 96, cy, cx + 96, 30))
    s += cota(cx - 96, 36, cx + 96, 36, "D", cx, 26)
    s += ext((cx - 60, cy + 8, cx - 60, cy + 126), (cx + 60, cy + 8, cx + 60, cy + 126))
    s += cota(cx - 60, cy + 120, cx + 60, cy + 120, "d1", cx, cy + 143)
    # lateral
    x, yt, yc, yb = 386, 56, 86, 236
    s += caminho(f"M{x-92} {yt} H{x+92} L{x+96} {yt+4} V{yc} H{x-96} V{yt+4} Z")
    s += caminho(f"M{x-74} {yc} V{yb-6} L{x-68} {yb} H{x+68} L{x+74} {yb-6} V{yc}")
    s += linhas([(x - 66, yc + 12, x - 66, yb - 4), (x + 66, yc + 12, x + 66, yb - 4)], TRACO, .8)
    s += linhas([(x - 50, yt, x - 50, yb), (x + 50, yt, x + 50, yb)], TRACO, 1.1, "5 3")
    s += linhas([(x - 60, yt + 6, x - 60, yb - 6), (x + 60, yt + 6, x + 60, yb - 6)], TRACO, .7, "5 3")
    s += linhas([(x, yt - 14, x, yb + 14)], CENTRO, .8, "12 3 2 3")
    s += ext((x + 96, yt, x + 142, yt), (x + 96, yc, x + 142, yc), (x + 74, yb, x + 142, yb))
    s += cota(x + 134, yt, x + 134, yc, "C", x + 146, (yt + yc) / 2 + 6, "start")
    s += cota(x + 134, yc, x + 134, yb, "L", x + 146, (yc + yb) / 2 + 6, "start")
    s += ext((x - 74, yb, x - 74, 268), (x + 74, yb, x + 74, 268))
    s += cota(x - 74, 262, x + 74, 262, "d2", x, 286)
    return s + "</svg>"


DESENHO = {"906": desenho_906, "908": desenho_908, "910": desenho_910, "posicionador": desenho_posicionador}


# ------------------------------------------------------------------ facetas do fundo (o cinza dobrado do post)
def facetas(variante=0):
    polys = [
        ("0,0 560,0 210,1000 0,1000", "#e5e7ea"),
        ("560,0 1120,0 780,1000 210,1000", "#eceef0"),
        ("1120,0 1600,0 1600,560 1250,1000 780,1000", "#f2f3f5"),
        ("1600,560 1600,1000 1250,1000", "#e7e9ec"),
        ("1120,0 1350,0 980,1000 780,1000", "#eff0f2"),
    ]
    if variante:
        polys = [(p, c) for p, c in polys]
    corpo = "".join(f'<polygon points="{p}" fill="{c}"/>' for p, c in polys)
    return (f'<div class="facetas" aria-hidden="true"><svg viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice">{corpo}'
            '<defs><linearGradient id="lz" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
            '<rect width="1600" height="1000" fill="url(#lz)"/></svg></div>')


# ------------------------------------------------------------------ estrutura comum
def ld(obj):
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False, separators=(",", ":"))}</script>'


ORG_ID = DOMINIO + "/#empresa"
BRASIL = {"@type": "Country", "name": "Brasil"}
DIAS_UTEIS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
# imagens de cada página, para o sitemap e para os dados estruturados
IMG_ROTA = {"/": ["grupo-todas"], "/bujao-din-906": ["906-aco", "906-inox"], "/bujao-din-908": ["908-aco", "908-inox"], "/bujao-din-910": ["910-aco", "910-inox"],
            "/posicionador-com-mola-e-esfera": ["posicionador-aco", "posicionador-inox"], "/bucha-roscada": ["bucha-colar-aco", "bucha-colar-latao"],
            "/molas-de-compressao": ["mola-aco"], "/molas-de-tracao": ["mola-tracao-aco"], "/molas-de-torcao": ["mola-torcao-zinco"]}


def org_schema():
    return {
        "@context": "https://schema.org", "@type": "Organization", "@id": ORG_ID, "name": "W Speed", "alternateName": NOMES_ALT,
        "url": DOMINIO + "/", "logo": DOMINIO + "/assets/img/logo-160.png", "image": DOMINIO + "/assets/img/og-image.jpg",
        "telephone": "+55 11 98890-4107", "sameAs": [INSTAGRAM], "address": {"@type": "PostalAddress", "addressRegion": "SP", "addressCountry": "BR"}, "areaServed": BRASIL,
        "description": "Fabricante de bujões DIN 906, 908 e 910, posicionadores com mola e esfera, buchas roscadas, molas de compressão, tração e torção e usinagem sob medida.",
        "knowsAbout": ["Bujões DIN 906, 908 e 910", "Posicionadores com mola e esfera", "Buchas roscadas", "Molas de compressão, tração e torção", "Usinagem sob medida", "Peças para máquinas agrícolas e sistemas hidráulicos"],
        "contactPoint": {"@type": "ContactPoint", "telephone": "+55 11 98890-4107", "contactType": "sales", "areaServed": "BR", "availableLanguage": "Portuguese",
                         "hoursAvailable": [{"@type": "OpeningHoursSpecification", "dayOfWeek": DIAS_UTEIS, "opens": a, "closes": f} for a, f in (("08:00", "12:00"), ("13:30", "17:30"))]},
    }


def site_ld():
    """Só na inicial: é o que faz o Google mostrar "W Speed" como nome do site, e não o endereço."""
    return {"@context": "https://schema.org", "@type": "WebSite", "@id": DOMINIO + "/#site", "url": DOMINIO + "/", "name": "W Speed",
            "alternateName": NOMES_ALT, "inLanguage": "pt-BR", "publisher": {"@id": ORG_ID}}


def servico_ld(nome, rota, desc):
    """Service, e não Product: sem preço público, Product só geraria erro de "offers" no Search Console."""
    d = {"@context": "https://schema.org", "@type": "Service", "@id": DOMINIO + rota + "#servico", "name": nome, "serviceType": nome,
         "url": DOMINIO + rota, "description": desc, "provider": {"@id": ORG_ID}, "areaServed": BRASIL}
    if rota in IMG_ROTA:
        d["image"] = f"{DOMINIO}/assets/img/pecas/{IMG_ROTA[rota][0]}-800.webp"
    return d


def faq_ld(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in faq]}


def migalhas_ld(passos):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": DOMINIO + u} for i, (n, u) in enumerate(passos)]}


def gtm_head():
    if not GTM_ID:
        return ""
    return ("<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});"
            "var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;"
            f"j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','{GTM_ID}');</script>")


def gtm_body():
    if not GTM_ID:
        return ""
    return f'<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>'


MOLAS_TIPOS = [("Molas de compressão", "trabalham sendo apertadas", "/molas-de-compressao", "mola"),
               ("Molas de tração", "trabalham sendo esticadas", "/molas-de-tracao", "mola-tracao"),
               ("Molas de torção", "trabalham girando", "/molas-de-torcao", "mola-torcao")]


# na faixa escura da página inicial as molas aparecem claras, para o arame não sumir no fundo
MOLAS_CASA = [("Mola de compressão", "trabalha sendo apertada", "Com a mola solta, as espiras ficam afastadas umas das outras. Ao ser apertada, ela encurta e empurra de volta.", "/molas-de-compressao", "mola", "inox"),
              ("Mola de tração", "trabalha sendo esticada", "Com a mola solta, as espiras ficam encostadas umas nas outras, e cada ponta termina em um gancho.", "/molas-de-tracao", "mola-tracao", "zinco"),
              ("Mola de torção", "trabalha girando", "O corpo é um anel de espiras encostadas, e duas pernas saem dele, retas ou com a ponta dobrada.", "/molas-de-torcao", "mola-torcao", "zinco")]


def topo(rota):
    cur = ' aria-current="page"'
    sub = "".join(
        f'<li><a href="/{p["slug"]}"{cur if rota == "/" + p["slug"] else ""}>'
        f'<img src="/assets/img/pecas/{p["tipo"]}-aco-480.webp" alt="" width="40" height="40" loading="lazy">'
        f'<span>{e(p["nome"])}<small>{e(p["sub"])}</small></span></a></li>'
        for p in PRODUTOS if p["tipo"] != "posicionador")
    atual = lambda r: ' aria-current="page"' if rota == r else ""
    sub_molas = "".join(
        f'<li><a href="{r}"{atual(r)}><img src="/assets/img/pecas/{t}-{MOLA_3D[t]["material"]}-480.webp" alt="" width="40" height="40" loading="lazy">'
        f'<span>{n}<small>{d}</small></span></a></li>' for n, d, r, t in MOLAS_TIPOS)
    return f'''<header class="topo"><div class="wrap">
<a class="marca" href="/" aria-label="W Speed, página inicial"><img src="/assets/img/logo-96.webp" width="139" height="46" alt="W Speed"></a>
<nav class="nav" id="nav" aria-label="Principal">
<div class="sub"><button type="button" aria-expanded="false">Bujões {ic("chev", 1.8)}</button><ul>{sub}</ul></div>
<a href="/posicionador-com-mola-e-esfera"{atual("/posicionador-com-mola-e-esfera")}>Posicionadores</a>
<a href="/bucha-roscada"{atual("/bucha-roscada")}>Buchas</a>
<div class="sub"><button type="button" aria-expanded="false">Molas {ic("chev", 1.8)}</button><ul>{sub_molas}</ul></div>
<a href="/usinagem"{atual("/usinagem")}>Usinagem</a>
<a href="/contato"{atual("/contato")}>Contato</a>
</nav>
<div class="topo__acoes">
<button class="bt-orc" type="button" data-abre-orc>{ic("carrinho", 1.6)}<span class="txt">Orçamento</span><span class="n">0</span></button>
<button class="bt-menu" type="button" aria-label="Menu" aria-controls="nav" aria-expanded="false">{ic("menu", 1.7)}</button>
</div></div></header>'''


def rodape():
    links = "".join(f'<li><a href="/{p["slug"]}">{e(p["nome"])}</a></li>' for p in PRODUTOS)
    return f'''<footer class="rodape"><div class="wrap">
<div class="rodape__grade">
<div><img class="logo" src="/assets/img/logo-negativo-160.webp" width="163" height="54" alt="W Speed" loading="lazy">
<p>Bujões DIN 906, 908 e 910, posicionadores com mola e esfera, buchas roscadas, molas de compressão, tração e torção e usinagem sob medida, com envio para todo o Brasil.</p></div>
<div><p class="rodape__tit">Peças</p><ul>{links}<li><a href="/bucha-roscada">Bucha roscada</a></li><li><a href="/molas-de-compressao">Molas de compressão</a></li><li><a href="/molas-de-tracao">Molas de tração</a></li><li><a href="/molas-de-torcao">Molas de torção</a></li><li><a href="/usinagem">Usinagem sob medida</a></li></ul></div>
<div><p class="rodape__tit">Contato</p><ul><li><a href="{zap_link("rodape")}">WhatsApp {TEL_VER}</a></li><li><a href="{INSTAGRAM}" target="_blank" rel="noopener">Instagram @wfix.speed</a></li><li><a href="#" data-abre-orc>Minha lista de orçamento</a></li><li><a href="/contato">Contato</a></li><li>Seg. a sex., 8h às 12h e 13h30 às 17h30</li></ul></div>
</div>
<div class="rodape__base"><span>© {date.today().year} W Speed</span><span>Medidas conforme as normas DIN. As imagens das peças são geradas a partir dessas medidas.</span></div>
</div></footer>'''


def gaveta():
    return f'''<div class="veu" data-fecha-orc></div>
<aside class="gaveta" role="dialog" aria-modal="true" aria-hidden="true" aria-labelledby="orc-tit">
<div class="gaveta__topo"><h2 id="orc-tit">Seu orçamento</h2><button type="button" data-fecha-orc aria-label="Fechar">{ic("fechar", 1.7)}</button></div>
<div class="gaveta__corpo">
<div class="vazio">{ic("caixa", 1.3)}<p>Sua lista ainda está vazia. Abra uma peça, escolha a medida na tabela e toque no <b>+</b> da linha.</p><div class="ctas"><a class="btn btn--linha" href="/#pecas" data-fecha-orc><span>Ver as peças</span></a></div></div>
<ul class="itens"></ul>
<form id="form-orc" class="form" hidden>
<label class="inteiro">Seu nome<input name="nome" required autocomplete="name"></label>
<label>Empresa<input name="empresa" autocomplete="organization"></label>
<label>Cidade/UF<input name="cidade" placeholder="Ex.: Rio Verde/GO" autocomplete="address-level2"></label>
<label class="inteiro">Observação<textarea name="obs" placeholder="Prazo, aplicação, se precisa de nota fiscal..."></textarea></label>
</form>
</div>
<div class="gaveta__base" hidden><button class="btn btn--escuro" type="submit" form="form-orc">{ZAP}<span>Enviar pelo WhatsApp</span></button><p>A lista vai pronta na conversa. <button type="button" data-limpa>Limpar lista</button></p></div>
</aside>
<div class="flutua"><button class="orcf" type="button" data-abre-orc>{ic("carrinho", 1.6)}<span>Ver orçamento</span><span class="n">0</span></button><a class="zapf" href="{zap_link("flutuante")}" aria-label="Falar no WhatsApp">{ZAP}</a></div>
<div class="aviso" role="status" aria-live="polite"><span></span><button type="button">Ver lista</button></div>'''


def pagina(titulo, desc, corpo, rota="/", preload="", extra_ld="", robots=None, casca=True):
    robots = robots or ("index,follow,max-image-preview:large" if INDEXAR else "noindex,nofollow")
    css = minificar(CSS.read_text())
    lds = ld(org_schema()) + extra_ld
    return f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(titulo)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{DOMINIO}{rota}">
<meta name="theme-color" content="#eceef0">
<meta property="og:type" content="website"><meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="W Speed">
<meta property="og:title" content="{e(titulo)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{DOMINIO}{rota}">
<meta property="og:image" content="{DOMINIO}/assets/img/og-image.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" type="image/png" sizes="32x32" href="/assets/img/icone-32.png"><link rel="apple-touch-icon" href="/assets/img/icone-180.png">
<link rel="preload" href="/assets/fonts/poppins-300.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/poppins-500.woff2" as="font" type="font/woff2" crossorigin>
{preload}
<script>document.documentElement.classList.add('js')</script>
{gtm_head()}
<style>{css}</style>
{lds}
</head>
<body data-pecas3d="/assets/js/pecas3d.js?v={hash_de(JS3D)}">
{gtm_body()}
{topo(rota) if casca else ""}
<main id="conteudo">
{corpo}
</main>
{rodape() if casca else ""}
{gaveta() if casca else ""}
<script src="/assets/js/site.min.js?v={hash_de(JS)}" defer></script>
</body>
</html>
'''


def preload_peca(tipo, mat="aco", sizes="(max-width:900px) 92vw, 560px"):
    base = f"/assets/img/pecas/{tipo}-{mat}"
    return (f'<link rel="preload" as="image" type="image/webp" href="{base}-800.webp" imagesrcset="{base}-480.webp 480w, {base}-800.webp 800w" '
            f'imagesizes="{sizes}" fetchpriority="high">')


def material_toggle(alvo, rot_aco="Aço oxidado", outro=("inox", "Inox")):
    return (f'<div class="material" role="group" aria-label="Material" data-alvo="{alvo}">'
            f'<button type="button" data-mat="aco" aria-pressed="true">{rot_aco}</button>'
            f'<button type="button" data-mat="{outro[0]}" aria-pressed="false">{outro[1]}</button></div>')


def visor_cfg(tipo, dims, material="aco", yaw=None, pitch=None):
    yaw = yaw if yaw is not None else {"posicionador": 1.4, "mola": 0.2}.get(tipo, -0.5)
    pitch = pitch if pitch is not None else {"posicionador": 0.36, "mola": 0.28}.get(tipo, 0.42)
    return e(json.dumps({"tipo": tipo, "dims": dims, "material": material, "yaw": yaw, "pitch": pitch}, ensure_ascii=False), quote=True)


def perguntas_html(faq):
    mais = ic("mais", 1.8)
    return '<div class="perguntas">' + "".join(
        f'<details class="rev"><summary>{e(q)}<i>{mais}</i></summary><p>{e(r)}</p></details>' for q, r in faq) + "</div>"


CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'
HORARIO = "de segunda a sexta-feira, das 8h às 12h e das 13h30 às 17h30"
# textos da IA do cliente (06/11), página por página
TXT_BUJOES = ("Bujões padrão DIN: qualidade para <strong>Indústria</strong> e hidráulica",
              "Fabricamos bujões de aço carbono e aço inoxidável, seguindo as normas DIN. Ideais para fechamento de furos em sistemas hidráulicos, caixas de engrenagens e máquinas industriais.",
              ["Vedação segura contra vazamentos", "Resistentes à pressão e ao desgaste", "Medidas padrão e também sob desenho técnico"],
              "Peça seu orçamento rápido pelo WhatsApp")
TXT_POSICIONADOR = ("Posicionadores com mola-esfera: para <strong>fixação e ajuste seguro</strong>",
                    "Nossos posicionadores com mola-esfera são fabricados com materiais resistentes, para uso em máquinas industriais, equipamentos de montagem e ferramentas.",
                    ["Fixação precisa e fácil de ajustar", "Suporta movimentos repetidos sem desgaste rápido", "Versões padrão ou sob desenho do cliente"],
                    "Solicite seu orçamento pelo WhatsApp")
TXT_MOLAS = ("Molas de compressão, tração e torção: para <strong>todas as aplicações industriais</strong>",
             "Fabricamos molas em aço carbono e aço inoxidável, para máquinas, equipamentos agrícolas, sistemas hidráulicos e montagens em geral.",
             ["Resistência à fadiga e à pressão contínua", "Medidas padrão ou feitas sob desenho técnico", "Controle de qualidade em todas as peças"],
             "Peça já seu orçamento pelo WhatsApp")
TXT_USINAGEM = "Realizamos usinagem de peças conforme desenho ou amostra do cliente, em aço carbono e aço inoxidável. Atendemos indústrias, oficinas mecânicas e equipamentos agrícolas e hidráulicos."
ITENS_USINAGEM = ["Precisão nas medidas", "Controle de qualidade em todas as etapas", "Produção de peças únicas ou em lotes"]


ICONE_DESENHO = '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 14h20l4 4v8l-4 4H8z"/><path d="M32 22h8M12 22h16" stroke-dasharray="3 3"/><path d="M8 37v5M28 37v5M8 39.5h20"/></svg>'


def miniatura(tipo, mat):
    """Foto pequena da peça para a fileira do topo (sai do recorte de 300 px)."""
    from PIL import Image
    destino = RAIZ / f"assets/img/pecas/{tipo}-{mat}-mini.webp"
    origem = RAIZ / f"assets/img/pecas/{tipo}-{mat}-recorte-300.webp"
    if not destino.exists() or destino.stat().st_mtime < origem.stat().st_mtime:
        im = Image.open(origem).convert("RGBA")
        im.resize((round(im.width * 96 / im.height), 96), Image.LANCZOS).save(destino, quality=82, method=6)
    larg, alt = Image.open(destino).size
    return f'src="/assets/img/pecas/{tipo}-{mat}-mini.webp" width="{round(larg * 48 / alt)}" height="48"'


def lista_ok(itens):
    return '<ul class="ok">' + "".join(f"<li>{CHECK}<span>{e(i)}</span></li>" for i in itens) + "</ul>"


def destaque(txt, contexto):
    titulo, texto, itens, cta = txt
    return f'''<section class="sec" style="padding-block:clamp(48px,7vw,88px) 0"><div class="wrap"><div class="destaque rev">
<div><h2 class="tit barra">{titulo}</h2><p class="lead" style="margin-top:22px">{e(texto)}</p></div>
<div>{lista_ok(itens)}<div class="ctas" style="margin-top:26px">{btn(cta, zap_link(contexto), "escuro", "zap")}</div></div>
</div></div></section>'''


# ------------------------------------------------------------------ início
FAQ_HOME = [
    ("O que a W Speed fabrica?",
     "A W Speed fabrica bujões DIN 906, 908 e 910, posicionadores com mola e esfera, buchas roscadas, molas de compressão, tração e torção e peças usinadas conforme desenho ou amostra. Trabalha com aço carbono, aço inoxidável e, nas buchas, latão."),
    ("Para quais setores a W Speed fornece?",
     "Para indústrias, oficinas mecânicas, máquinas agrícolas, tratores, sistemas hidráulicos, redutores, moldes e estampos, em todo o Brasil."),
    ("Vocês fazem peças só em lote grande?",
     "Não! Atendemos desde peças individuais até lotes grandes, conforme a necessidade do cliente."),
    ("Trabalham com aço inoxidável?",
     "Sim, fabricamos peças em aço carbono e também em aço inoxidável."),
    ("Preciso enviar desenho técnico para fazer o orçamento?",
     "Se tiver o desenho é melhor, mas também aceitamos amostra da peça ou medidas exatas."),
    ("Enviam para todo o Brasil?",
     "Sim, fazemos entrega para todas as regiões do país. Informe a sua cidade quando mandar a lista, assim a gente calcula o frete junto com o orçamento."),
    ("Quanto tempo demora para chegar o orçamento?",
     f"Respondemos pelo WhatsApp em horário comercial, {HORARIO}."),
    ("Qual a diferença entre o bujão DIN 906, 908 e 910?",
     "O DIN 906 é cônico e sem colar, fica rente à peça e veda pela própria rosca. O DIN 908 tem colar e sextavado interno, para chave Allen, e o DIN 910 tem cabeça sextavada por fora e colar, para chave de boca. Esses dois têm rosca reta e vedam com um anel embaixo do colar."),
    ("Como descobrir a rosca do bujão que eu preciso?",
     "Meça o diâmetro externo da rosca com um paquímetro e conte quantos fios cabem em uma polegada (25,4 mm). Com essas duas medidas você acha a linha certa na tabela. Se ficar em dúvida, mande uma foto da peça ao lado do paquímetro pelo WhatsApp que a gente ajuda."),
    ("Vocês fazem medidas fora da tabela?",
     "Fazemos. Medidas, roscas e materiais especiais saem sob encomenda: mande a medida ou o desenho junto com a lista de orçamento."),
    ("Como funciona o pedido pelo site?",
     "Você monta a lista com as peças, as medidas e as quantidades e envia pelo WhatsApp. O pedido é fechado na conversa, com preço, prazo e forma de pagamento."),
]
CAMPO = ["Tratores", "Colheitadeiras", "Implementos agrícolas", "Bombas hidráulicas", "Redutores", "Blocos de válvulas",
         "Cárteres e câmbios", "Tanques de óleo", "Moldes de injeção", "Estampos", "Gabaritos e dispositivos", "Máquinas industriais"]


LEGENDA_GRUPO = "Escolha uma peça para girar e ver as medidas."
TAM_GRUPO = "(max-width:620px) 270px, (max-width:900px) 340px, 440px"   # largura real do .palco no topo


def home():
    p910, p908, p906, ppos = POR_SLUG["bujao-din-910"], POR_SLUG["bujao-din-908"], POR_SLUG["bujao-din-906"], POR_SLUG["posicionador-com-mola-e-esfera"]
    pecas_heroi = [
        {"grupo": True, "rot": "Todas as peças", "mini": ("grupo", "todas"), "legenda": LEGENDA_GRUPO},
        {"tipo": "910", "sombra": SOMBRA["910"], "dims": dims_padrao(p910), "yaw": -0.5, "pitch": 0.42, "rot": "DIN 910", "mini": ("910", "aco"), "legenda": "Bujão DIN 910 com cabeça sextavada e colar.", "url": "/bujao-din-910"},
        {"tipo": "908", "sombra": SOMBRA["908"], "dims": dims_padrao(p908), "yaw": -0.5, "pitch": 0.42, "rot": "DIN 908", "mini": ("908", "aco"), "legenda": "Bujão DIN 908 com colar e sextavado interno.", "url": "/bujao-din-908"},
        {"tipo": "906", "sombra": SOMBRA["906"], "dims": dims_padrao(p906), "yaw": -0.5, "pitch": 0.42, "rot": "DIN 906", "mini": ("906", "aco"), "legenda": "Bujão DIN 906 cônico com sextavado interno.", "url": "/bujao-din-906"},
        {"tipo": "posicionador", "sombra": SOMBRA["posicionador"], "dims": dims_padrao(ppos), "yaw": 1.4, "pitch": 0.36, "rot": "Posicionador", "mini": ("posicionador", "aco"), "legenda": "Posicionador com mola e esfera.", "url": "/posicionador-com-mola-e-esfera"},
        {"tipo": "bucha-colar", "sombra": SOMBRA["bucha-colar"], "dims": BUCHA_DIMS["bucha-colar"], "yaw": -0.5, "pitch": 0.72, "material": "latao", "rot": "Bucha roscada", "mini": ("bucha-colar", "latao"), "legenda": "Bucha roscada em aço ou latão.", "url": "/bucha-roscada", "verbo": "Ver a peça"},
        {"tipo": "mola", "sombra": SOMBRA["mola"], "dims": MOLA_3D["mola"]["dims"], "yaw": 0.2, "pitch": 0.28, "material": "aco", "rot": "Mola de compressão", "mini": ("mola", "aco"), "legenda": "Mola de compressão sob medida.", "url": "/molas-de-compressao"},
        {"tipo": "mola-tracao", "sombra": SOMBRA["mola-tracao"], "dims": MOLA_3D["mola-tracao"]["dims"], "yaw": -0.45, "pitch": 0.14, "material": "aco", "rot": "Mola de tração", "mini": ("mola-tracao", "aco"), "legenda": "Mola de tração com gancho.", "url": "/molas-de-tracao"},
        {"tipo": "mola-torcao", "sombra": SOMBRA["mola-torcao"], "dims": MOLA_3D["mola-torcao"]["dims"], "yaw": -0.32, "pitch": 0.34, "material": "zinco", "rot": "Mola de torção", "mini": ("mola-torcao", "zinco"), "legenda": "Mola de torção sob medida.", "url": "/molas-de-torcao"},
    ]
    miniaturas = "".join(
        f'<button type="button" class="miniatura" data-peca aria-pressed="{"true" if i == 0 else "false"}"><img {miniatura(*h["mini"])} alt="" loading="lazy" decoding="async"><span>{h["rot"]}</span></button>'
        for i, h in enumerate(pecas_heroi))
    heroi = f'''<section class="heroi">{facetas()}
<div class="wrap heroi__grade">
<div class="heroi__a">
<h1 class="barra rev"><strong>Peças industriais</strong> e usinagem sob medida</h1>
</div>
<div class="heroi__b">
<p class="lead rev" style="--d:.08s">Fabricamos bujões padrão DIN, posicionadores com mola-esfera, molas de compressão, tração e torção e peças usinadas conforme seu desenho ou amostra. Trabalhamos com aço carbono e aço inoxidável para indústria, máquinas agrícolas e sistemas hidráulicos. Garantimos precisão, resistência e entrega rápida para todo o Brasil.</p>
<div class="ctas rev" style="--d:.16s">{btn("Ver as peças", "#pecas", "escuro", "baixo")}{btn("Falar com o atendente", zap_link("heroi"), "linha", "zap")}</div>
</div>
<div class="heroi__v">
<div class="palco grupo" style="--sombra:{SOMBRA["910"]}" data-visor="{visor_cfg("910", dims_padrao(p910))}" data-poster="/assets/img/pecas/{{tipo}}-{{mat}}-800.webp" data-pecas="{e(json.dumps(pecas_heroi, ensure_ascii=False), quote=True)}">
{img_peca("grupo", "todas", alt="Peças fabricadas pela W Speed: bujões DIN 906, 908 e 910, posicionador com mola e esfera, bucha roscada e molas de compressão, tração e torção", lazy=False, sizes=TAM_GRUPO)}
<span class="palco__dica">{ic("giro", 1.5)} Arraste para girar</span>
</div>
<div class="controles">
<div class="miniaturas" role="group" aria-label="Peças que fabricamos">{miniaturas}<a class="miniatura miniatura--desenho" href="/usinagem">{ICONE_DESENHO}<span>Peça conforme o desenho</span></a></div>
{material_toggle(".heroi .palco")}
<p class="heroi__legenda" aria-live="polite">{LEGENDA_GRUPO}</p></div>
</div>
</div></section>'''

    cards = ""
    for i, p in enumerate([p910, p908, p906, ppos]):
        w, h = dims_recorte(p["tipo"], "aco", 300)
        cards += f'''<article class="peca rev" style="--d:{i * .08:.2f}s">
<div class="peca__img"><img src="/assets/img/pecas/{p["tipo"]}-aco-recorte-300.webp" width="{w}" height="{h}" alt="{e(p["nome"])} {e(p["sub"])}" loading="lazy" decoding="async"><span class="linha-chama"></span></div>
<h3>{e(p["nome"])}</h3><p class="sub">{e(p["sub"])}</p>
<p class="rec">{e(p["reconhecer"])}</p>
<span class="seta seta--chama">Ver medidas {SETA}</span>
<a class="cobre" href="/{p["slug"]}" aria-label="Ver medidas do {e(p["nome"])}"></a>
</article>'''
    wb, hb = dims_recorte("bucha-colar", "latao", 300)
    cards += f'''<article class="peca rev" style="--d:.32s">
<div class="peca__img"><img src="/assets/img/pecas/bucha-colar-latao-recorte-300.webp" width="{wb}" height="{hb}" alt="Bucha roscada com colar, em latão" loading="lazy" decoding="async"><span class="linha-chama"></span></div>
<h3>Bucha roscada</h3><p class="sub">reta ou com colar</p>
<p class="rec">{e(BUCHA_RECONHECER)}</p>
<span class="seta seta--chama">Ver a peça {SETA}</span>
<a class="cobre" href="/bucha-roscada" aria-label="Ver a bucha roscada"></a>
</article>'''
    pecas = f'''<section class="sec" id="pecas"><div class="wrap">
<div class="centro"><h2 class="tit barra centro rev">Qual é a sua peça?</h2>
<p class="lead rev" style="margin-top:22px">Muitas vezes quem compra recebe só o nome ou a peça velha na mão. Compare pelo formato e abra a ficha com o desenho e as medidas.</p></div>
<div class="prateleira">{cards}</div>
</div></section>'''

    comparar = f'''<section class="sec" style="padding-top:0"><div class="wrap comparar">
<div>
<h2 class="tit barra rev">Em aço oxidado ou em <strong>inox</strong></h2>
<p class="lead rev" style="margin-top:22px">Bujões e posicionadores saem nos dois materiais. Arraste a linha sobre a imagem para comparar.</p>
<ul class="rev"><li><i></i><span><b>Aço oxidado.</b> O acabamento preto protege contra a ferrugem do dia a dia e atende a maior parte das máquinas, tratores e sistemas hidráulicos.</span></li>
<li><i class="inox"></i><span><b>Inox.</b> Não enferruja, então é o indicado para ambiente úmido, contato com água, alimentos ou produtos químicos.</span></li></ul>
</div>
<div class="rev">
<div class="lado" style="--x:50%">
<img src="/assets/img/pecas/posicionador-aco-800.webp" srcset="/assets/img/pecas/posicionador-aco-480.webp 480w, /assets/img/pecas/posicionador-aco-800.webp 800w" sizes="(max-width:900px) 92vw, 560px" width="800" height="800" alt="Posicionador com mola e esfera em aço oxidado" loading="lazy" decoding="async">
<img class="inox" src="/assets/img/pecas/posicionador-inox-800.webp" srcset="/assets/img/pecas/posicionador-inox-480.webp 480w, /assets/img/pecas/posicionador-inox-800.webp 800w" sizes="(max-width:900px) 92vw, 560px" width="800" height="800" alt="O mesmo posicionador em inox" loading="lazy" decoding="async">
<span class="lado__fio"></span>
<input type="range" min="4" max="96" value="50" aria-label="Comparar aço oxidado e inox">
</div>
<div class="lado__rot"><span>&larr; <b>Aço oxidado</b></span><span><b>Inox</b> &rarr;</span></div>
</div>
</div></section>'''

    cartoes_molas = ""
    for i, (n, sb, rec, r, t, mt) in enumerate(MOLAS_CASA):
        wm, hm = dims_recorte(t, mt, 300)
        cartoes_molas += f'''<article class="peca rev" style="--d:{i * .08:.2f}s">
<div class="peca__img"><img src="/assets/img/pecas/{t}-{mt}-recorte-300.webp" width="{wm}" height="{hm}" alt="{n}" loading="lazy" decoding="async"><span class="linha-chama"></span></div>
<h3>{n}</h3><p class="sub">{sb}</p>
<p class="rec">{rec}</p>
<span class="seta seta--chama">Ver medidas {SETA}</span>
<a class="cobre" href="{r}" aria-label="Ver medidas da {n.lower()}"></a>
</article>'''
    molas = f'''<section class="sec escuro"><div class="wrap">
<div class="centro"><h2 class="tit barra centro rev">Molas <strong>sob medida</strong></h2>
<p class="lead lead--cheia rev" style="margin-top:22px">Também fabricamos molas de compressão, de tração e de torção. Você passa as medidas ou manda uma amostra, e a gente produz na quantidade que a sua produção precisa.</p></div>
<div class="prateleira prateleira--3">{cartoes_molas}</div>
</div></section>'''

    usinagem = f'''<section class="sec"><div class="wrap usinagem">
<div class="prancha rev">{desenho_usinagem()}</div>
<div>
<h2 class="tit barra rev">Fabricamos a sua peça <strong>conforme o desenho</strong></h2>
<p class="lead rev" style="margin-top:22px">{e(TXT_USINAGEM)}</p>
<div class="rev" style="margin-top:22px">{lista_ok(ITENS_USINAGEM)}</div>
<div class="ctas rev" style="margin-top:32px">{btn("Mandar o desenho", zap_link("usinagem"), "escuro", "zap")}{btn("Como funciona", "/usinagem", "linha")}</div>
</div>
</div></section>'''

    exemplo = ("Olá, W Speed! Quero um orçamento destas peças:\n\n"
               "1) Bujão DIN 910, rosca 1/2\"-14 BSP, aço oxidado: 40 un.\n"
               "2) Bujão DIN 906, rosca 3/8\"-19 BSPT, aço oxidado: 25 un.\n"
               "3) Posicionador com mola e esfera, M8 × 20, inox: 100 un.\n\n"
               "Nome: Carlos\nCidade/UF: Rio Verde/GO")
    fluxo = f'''<section class="sec" style="padding-top:0"><div class="wrap fluxo">
<div class="rev"><div class="conversa" aria-label="Exemplo da lista chegando no WhatsApp">
<div class="conversa__topo"><img src="/assets/img/icone-180.png" alt="" width="36" height="36" loading="lazy"><div><b>W Speed</b><small>Peças industriais</small></div></div>
<div class="conversa__corpo"><div class="balao">{e(exemplo)}<small>09:41</small></div></div>
</div></div>
<div>
<h2 class="tit barra rev">O orçamento chega <strong>pronto</strong> no WhatsApp</h2>
<ol class="passos rev">
<li><div><b>Escolha a peça e a medida</b><span>Na tabela, toque na rosca certa e escolha aço ou inox.</span></div></li>
<li><div><b>Monte a sua lista</b><span>Junte quantas medidas quiser e ajuste as quantidades.</span></div></li>
<li><div><b>Envie pelo WhatsApp</b><span>A lista vai organizada na conversa e a gente responde com preço e prazo.</span></div></li>
</ol>
<div class="ctas rev" style="margin-top:32px">{btn("Montar minha lista", "#pecas", "escuro")}</div>
</div>
</div></section>'''

    itens_faixa = "".join(f"<span>{PONTA}{e(c)}</span>" for c in CAMPO)
    meio = len(CAMPO) // 2
    f1 = "".join(f"<span>{PONTA}{e(c)}</span>" for c in CAMPO[:meio] + CAMPO[meio:])
    f2 = "".join(f"<span>{PONTA}{e(c)}</span>" for c in CAMPO[meio:] + CAMPO[:meio])
    campo = f'''<section class="sec" style="padding-top:0"><div class="wrap centro">
<h2 class="tit barra centro rev">Peças que trabalham no campo e na Indústria</h2>
<p class="lead rev" style="margin-top:22px">Bujões e posicionadores seguem a norma, então servem em máquina nacional ou importada. Atendemos empresas de todo o Brasil.</p>
</div>
<div class="faixas rev" aria-label="Onde as peças são usadas"><div class="faixa">{f1}{f1}</div><div class="faixa faixa--volta">{f2}{f2}</div></div>
</section>'''

    perguntas = f'''<section class="sec" style="padding-top:0"><div class="wrap">
<h2 class="tit barra centro rev" style="text-align:center">Perguntas frequentes</h2>
{perguntas_html(FAQ_HOME)}
</div></section>'''

    final = f'''<section><div class="wrap"><div class="final rev">
<div><h2 class="tit">Tem a peça na mão e não sabe a medida?</h2>
<p class="lead">Mande uma foto pelo WhatsApp, de preferência com uma régua ou um paquímetro ao lado, e a gente ajuda a identificar.</p></div>
<div class="ctas">{btn("Falar no WhatsApp", zap_link("final"), "claro", "zap")}</div>
</div></div></section>'''

    brasil = f'''<section class="brasil"><div class="wrap brasil__g">
<div><h2 class="brasil__tit rev">Atendemos <strong>todo o Brasil</strong></h2>
<p class="rev">Além de ter qualidade, nossas peças têm preço excelente. Esteja onde estiver, mande a sua lista ou o desenho da peça que a gente envia para a sua cidade.</p></div>
<div class="brasil__lado rev">{lista_ok(["Entrega para todas as regiões do país", "Peças com qualidade", "Preço excelente"])}<div class="ctas">{btn("Pedir orçamento", zap_link("brasil"), "claro", "zap")}</div></div>
</div></section>'''

    corpo = heroi + pecas + comparar + molas + brasil + usinagem + fluxo + campo + perguntas + final
    return pagina("Bujões DIN, molas e usinagem sob medida | W Speed",
                  "Fabricante de bujões DIN 906, 908 e 910, posicionadores com esfera, molas e usinagem sob medida, em aço e inox. Orçamento pelo WhatsApp, envio a todo o Brasil.",
                  corpo, "/", preload_peca("grupo", "todas", TAM_GRUPO), ld(site_ld()) + ld(faq_ld(FAQ_HOME)))


# ------------------------------------------------------------------ página de cada peça
def cab_html(c):
    k = chave_col(c)
    if c.startswith("Rosca"):
        sub = "fios por pol." if "fios" in c else ("× passo" if "passo" in c else "")
        return f'<th scope="col">Rosca{f"<span>{sub}</span>" if sub else ""}</th>'
    un = "pol." if "pol" in c else ("N" if k == "F" else "mm")
    return f'<th scope="col">{e(k)}<span>{un}</span></th>'


def tabela_html(p, tab, visivel, padrao_global):
    corpo = ""
    ip = linha_padrao(p, tab)
    for i, row in enumerate(tab["linhas"]):
        dims = linha_dims(p, tab, row)
        det = linha_detalhe(p, tab, row)
        rot = det if p["tipo"] == "posicionador" else str(row[0])
        sel = "true" if (visivel and i == ip) else "false"
        celulas = "".join(f"<td>{e(num(v))}</td>" for v in row[1:])
        primeira = f"{row[0]} × {num(row[1])}" if p["tipo"] == "posicionador" else row[0]
        if p["tipo"] == "posicionador":
            celulas = "".join(f"<td>{e(num(v))}</td>" for v in row[1:])
        corpo += (f'<tr tabindex="0" aria-selected="{sel}"{" data-padrao" if i == ip else ""} data-rotulo="{e(rot)}" data-detalhe="{e(det)}" '
                  f'data-dims="{e(json.dumps(dims, ensure_ascii=False), quote=True)}" data-medidas="{e(linha_medidas(p, tab, row), quote=True)}">'
                  f'<td>{e(row[0])}</td>{celulas}'
                  f'<td class="add"><button type="button" aria-label="Adicionar {e(det)} ao orçamento">{ic("mais", 1.8)}</button></td></tr>')
    cab = "".join(cab_html(c) for c in tab["cab"])
    nota = ("Medidas em milímetros (S em polegadas). Medidas especiais sob encomenda." if "pol" in "".join(tab["cab"])
            else ("Medidas em milímetros, força final da mola em newtons. Medidas especiais sob encomenda." if p["tipo"] == "posicionador"
                  else "Medidas em milímetros, conforme a norma DIN. Medidas especiais sob encomenda."))
    return (f'<div class="tabela" id="t-{tab["id"]}" role="tabpanel" aria-label="{e(tab["titulo"])}"{"" if visivel else " hidden"} '
            f'data-produto="{p["slug"]}" data-rosca="{tab["rosca"]}" data-nome="{e(p["nome"])}" data-img="/assets/img/pecas/{p["tipo"]}-{{mat}}-recorte-300.webp">'
            f'<h3>{e(tab["titulo"])}</h3><div class="tabela__rola"><table><thead><tr>{cab}<th scope="col"><span class="sr">Adicionar</span></th></tr></thead>'
            f'<tbody>{corpo}</tbody></table></div><p class="tabela__nota">{nota}</p></div>')


def produto(p):
    tab0 = p["tabelas"][0]
    i0 = linha_padrao(p, tab0)
    row0 = tab0["linhas"][i0]
    dims0 = linha_dims(p, tab0, row0)
    abas = ""
    if len(p["tabelas"]) > 1:
        abas = '<div class="abas" role="tablist" aria-label="Tipo de rosca">' + "".join(
            f'<button type="button" role="tab" aria-selected="{"true" if k == 0 else "false"}" aria-controls="t-{t["id"]}">{e(t["rotulo"])}</button>'
            for k, t in enumerate(p["tabelas"])) + "</div>"
    tabelas = "".join(tabela_html(p, t, k == 0, i0) for k, t in enumerate(p["tabelas"]))
    legenda = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in p["letras"])
    material_txt = ("Corpo em aço com oxidação preta ou em inox, esfera de aço temperado." if p["tipo"] == "posicionador"
                    else "Em aço com oxidação preta ou em inox.")
    outras = "".join(
        f'<a class="outra" href="/{o["slug"]}"><img src="/assets/img/pecas/{o["tipo"]}-aco-480.webp" alt="" width="96" height="96" loading="lazy">'
        f'<span><b>{e(o["nome"])}</b><small>{e(o["sub"])}</small></span></a>'
        for o in PRODUTOS if o["slug"] != p["slug"])
    nome_h1 = p["nome"].replace(p["codigo"], f'<strong>{e(p["codigo"])}</strong>') if p["codigo"] in p["nome"] else f'<strong>{e(p["nome"])}</strong>'
    if p["tipo"] == "posicionador":
        nome_h1 = "Posicionador com <strong>mola e esfera</strong>"
    corpo = f'''<section class="cab-prod">{facetas()}
<div class="wrap prod">
<div>
<div class="palco" style="--sombra:{SOMBRA[p["tipo"]]}" data-visor="{visor_cfg(p["tipo"], dims0)}" data-poster="/assets/img/pecas/{{tipo}}-{{mat}}-800.webp">
{img_peca(p["tipo"], "aco", alt=f'{p["nome"]} {p["sub"]} em aço oxidado', lazy=False)}
<span class="palco__dica">{ic("giro", 1.5)} Arraste para girar</span>
</div>
<div class="controles">{material_toggle(".prod .palco")}</div>
</div>
<div>
<nav class="migalhas" aria-label="Você está em"><a href="/">Início</a><span aria-hidden="true">/</span><a href="/#pecas">Peças</a><span aria-hidden="true">/</span><span>{e(p["nome"])}</span></nav>
<h1 class="barra">{nome_h1} <span class="sub" style="display:block">{e(p["sub"])}</span></h1>
<p class="lead">{e(p["texto"])}</p>
<p class="reconhecer"><b>Como reconhecer:</b> {e(p["reconhecer"])}</p>
<div class="escolha" aria-live="polite">
<div class="escolha__topo"><p class="escolha__nome">{e(p["nome"])} <small>{e(linha_detalhe(p, tab0, row0))}, aço oxidado</small></p></div>
<p class="escolha__dims">{linha_medidas(p, tab0, row0)}</p>
<div class="escolha__acao"><div class="qtd"><button type="button" data-q="-1" aria-label="Menos">{ic("menos", 1.8)}</button><input type="number" min="1" value="1" inputmode="numeric" aria-label="Quantidade"><button type="button" data-q="1" aria-label="Mais">{ic("mais", 1.8)}</button></div>
<button class="btn btn--escuro" type="button" data-adiciona>{ic("carrinho", 1.6)}<span>Adicionar ao orçamento</span></button></div>
<p class="escolha__ir">Outra medida? <a href="#medidas">Escolha na tabela</a> e a peça muda aí ao lado.</p>
</div>
</div>
</div></section>
{destaque(TXT_POSICIONADOR if p["tipo"] == "posicionador" else TXT_BUJOES, "desc-" + p["tipo"])}
<section class="sec" id="medidas" style="padding-top:clamp(40px,6vw,80px)"><div class="wrap">
<h2 class="tit barra rev">Desenho técnico e <strong>tabela de medidas</strong></h2>
<div class="tecnico">
<div class="prancha">{DESENHO[p["tipo"]]()}</div>
<div><dl class="legenda">{legenda}</dl><p class="mat">{material_txt}</p></div>
</div>
{abas}
{tabelas}
<div class="especial"><div><b>Precisa de outra medida, rosca ou material?</b><span>Fabricamos sob encomenda. Mande a medida ou o desenho que a gente faz o orçamento.</span></div>{btn("Pedir medida especial", zap_link("especial-" + p["tipo"]), "escuro", "zap")}</div>
</div></section>
<section class="sec" style="padding-top:0"><div class="wrap">
<h2 class="tit barra centro rev" style="text-align:center">Dúvidas sobre o {e(p["nome"])}</h2>
{perguntas_html(p["faq"])}
<h2 class="tit rev" style="margin-top:clamp(64px,8vw,104px);font-size:clamp(1.4rem,2.4vw,1.9rem)">Outras peças</h2>
<div class="outras">{outras}</div>
</div></section>'''
    rota = "/" + p["slug"]
    nome_serv = f'Fabricação de {p["nome"][0].lower()}{p["nome"][1:]} {p["sub"]}'
    extra = ld(servico_ld(nome_serv, rota, p["texto"])) + ld(faq_ld(p["faq"])) + ld(migalhas_ld([("Início", "/"), (p["nome"], rota)]))
    return pagina(f'{p["titulo_seo"]} | W Speed', p["desc_seo"], corpo, rota, preload_peca(p["tipo"]), extra)


# ------------------------------------------------------------------ molas
def tipos_mola(rota):
    itens = ""
    for n, r in (("Compressão", "/molas-de-compressao"), ("Tração", "/molas-de-tracao"), ("Torção", "/molas-de-torcao")):
        marca = ' aria-current="page"' if r == rota else ""
        itens += f'<a class="chip" href="{r}"{marca}>{n}</a>'
    return f'<nav class="tipos-mola" aria-label="Tipos de mola">{itens}</nav>'


def palco_mola(t, alt):
    m = MOLA_3D[t]
    return f'''<div class="palco" style="--sombra:{SOMBRA[t]}" data-visor="{visor_cfg(t, m["dims"], m["material"], m["yaw"], m["pitch"])}" data-poster="/assets/img/pecas/{{tipo}}-{{mat}}-800.webp">
{img_peca(t, m["material"], alt=alt, lazy=False)}
<span class="palco__dica">{ic("giro", 1.5)} Arraste para girar</span>
</div>'''


MOLAS_COMPRESSAO = [("Cilíndrica", "mola", "cilíndrica", "aço mola"), ("Reforçada", "mola-reforcada", "reforçada", "aço mola"),
                    ("Passo aberto", "mola-aberta", "passo aberto", "aço mola"), ("Barril", "mola-barril", "barril", "aço zincado"),
                    ("Pequena", "mola-pequena", "pequena", "inox")]


def molas():
    faq = [
        ("O que é uma mola de compressão?",
         "É a mola que trabalha sendo apertada. Com a mola solta, as espiras ficam afastadas umas das outras. Ao ser apertada, ela encurta e empurra de volta."),
        ("Como medir uma mola de compressão?",
         "Com um paquímetro, meça a espessura do arame, o diâmetro por fora das espiras e o comprimento da mola solta. Conte também quantas voltas ela tem. Com isso a gente já consegue orçar."),
        ("Vocês fazem a mola pela amostra?",
         "Fazemos. Se você tem a mola velha, mande uma foto com o paquímetro ou combine o envio da amostra pelo WhatsApp."),
        ("Qual material escolher?",
         "O aço mola atende a maioria das aplicações. O inox é para quando a mola trabalha molhada, em contato com alimentos ou produtos químicos."),
    ]
    variante = lambda rot, t, modelo, mat_form, ativo: (
        f'<button type="button" class="chip" aria-pressed="{"true" if ativo else "false"}" data-variante="'
        + e(json.dumps({"tipo": t, "dims": MOLA_3D[t]["dims"], "material": MOLA_3D[t]["material"], "yaw": MOLA_3D[t]["yaw"], "pitch": MOLA_3D[t]["pitch"],
                        "sombra": SOMBRA[t], "modelo": modelo, "matForm": mat_form}, ensure_ascii=False), quote=True) + f'">{rot}</button>')
    chips = "".join(variante(r, t, m, f, i == 0) for i, (r, t, m, f) in enumerate(MOLAS_COMPRESSAO))
    modelos = "".join(f'<option value="{m}">{r}</option>' for r, _, m, _ in MOLAS_COMPRESSAO)
    corpo = f'''<section class="cab-prod">{facetas()}
<div class="wrap prod">
<div>
{palco_mola("mola", "Mola de compressão cilíndrica com as pontas fechadas")}
<div class="controles"><div class="seletor" role="group" aria-label="Modelo da mola" data-alvo=".prod .palco">{chips}</div></div>
</div>
<div>
<nav class="migalhas" aria-label="Você está em"><a href="/">Início</a><span aria-hidden="true">/</span><span>Molas de compressão</span></nav>
{tipos_mola("/molas-de-compressao")}
<h1 class="barra">Molas de <strong>compressão</strong> sob medida</h1>
<p class="lead">Fabricamos molas de compressão pela amostra ou pelas medidas que você passar, em aço mola, aço zincado ou inox, na quantidade que a sua produção precisa.</p>
<form class="form escolha" data-sob-medida="mola" data-nome="Mola de compressão" data-img="/assets/img/pecas/mola-aco-recorte-300.webp">
<label>Arame (mm)<input name="fio" inputmode="decimal" placeholder="Ex.: 2" data-rot="arame" data-un="mm"></label>
<label>Diâmetro externo (mm)<input name="de" inputmode="decimal" placeholder="Ex.: 18" data-rot="Ø externo" data-un="mm"></label>
<label>Comprimento livre (mm)<input name="lo" inputmode="decimal" placeholder="Ex.: 46" data-rot="comprimento livre" data-un="mm"></label>
<label>Número de espiras<input name="espiras" inputmode="numeric" placeholder="Se souber" data-rot="com" data-un="espiras"></label>
<label>Modelo<select name="modelo" data-rot="modelo">{modelos}</select></label>
<label>Material<select name="material" data-rot="material"><option value="aço mola">Aço mola</option><option value="aço zincado">Aço zincado</option><option value="inox">Inox</option></select></label>
<label>Quantidade<input name="qtd" inputmode="numeric" value="100" data-rot="qtd"></label>
<label class="inteiro">Observação<input name="obs" placeholder="Aplicação, carga, se tem amostra..." data-rot="obs."></label>
<button class="btn btn--escuro" type="submit">{ic("carrinho", 1.6)}<span>Adicionar ao orçamento</span></button>
</form>
</div>
</div></section>
{destaque(TXT_MOLAS, "desc-mola")}
<section class="sec" style="padding-top:clamp(40px,6vw,80px)"><div class="wrap">
<div class="tecnico">
<div class="prancha rev">{desenho_mola()}</div>
<div>
<h2 class="tit barra rev">Como medir a sua mola</h2>
<dl class="legenda rev" style="margin-top:26px"><div><dt>d</dt><dd>espessura do arame</dd></div><div><dt>De</dt><dd>diâmetro externo, por fora das espiras</dd></div><div><dt>Lo</dt><dd>comprimento livre, com a mola solta</dd></div></dl><p class="mat rev">Conte também as voltas. Se a mola tiver as pontas fechadas ou retificadas, avise na observação. Na mola em barril, informe o maior e o menor diâmetro.</p>
</div>
</div>
{perguntas_html(faq)}
</div></section>'''
    extra = ld(servico_ld("Fabricação de molas de compressão sob medida", "/molas-de-compressao", "Molas de compressão fabricadas pela amostra ou pelas medidas do cliente, em aço mola, aço zincado ou inox.")) + ld(faq_ld(faq)) + ld(migalhas_ld([("Início", "/"), ("Molas de compressão", "/molas-de-compressao")]))
    return pagina("Molas de compressão sob medida em aço e inox | W Speed",
                  "Fabricamos molas de compressão sob medida em aço e inox, pela amostra ou pelas medidas. Informe arame, diâmetro e comprimento e peça orçamento pelo WhatsApp.",
                  corpo, "/molas-de-compressao", preload_peca("mola"), extra)


def mola_tracao():
    rota = "/molas-de-tracao"
    faq = [
        ("O que é uma mola de tração?",
         "É a mola que trabalha sendo esticada e puxa as duas peças de volta para o lugar. Com a mola solta, as espiras ficam encostadas umas nas outras, e cada ponta termina em um gancho."),
        ("Como medir uma mola de tração?",
         "Com um paquímetro, meça a espessura do arame, o diâmetro por fora das espiras e o comprimento total da mola solta, de um gancho ao outro. Se puder, meça também só o corpo, sem as hastes."),
        ("Vocês fazem a mola pela amostra?",
         "Fazemos. Se você tem a mola velha, mande uma foto com o paquímetro ou combine o envio da amostra pelo WhatsApp."),
        ("Posso pedir outro gancho ou outra haste?",
         "Pode. Descreva o que precisa na observação ou mande uma foto do gancho e do comprimento da haste que a sua peça usa, e a gente confirma no orçamento."),
    ]
    corpo = f'''<section class="cab-prod">{facetas()}
<div class="wrap prod">
<div>{palco_mola("mola-tracao", "Mola de tração com espiras encostadas e um gancho em cada ponta")}</div>
<div>
<nav class="migalhas" aria-label="Você está em"><a href="/">Início</a><span aria-hidden="true">/</span><span>Molas de tração</span></nav>
{tipos_mola(rota)}
<h1 class="barra">Molas de <strong>tração</strong> sob medida</h1>
<p class="lead">A mola de tração trabalha sendo esticada: ela puxa as duas peças de volta para o lugar. Fabricamos pela amostra ou pelas medidas que você passar, na quantidade que a sua produção precisa.</p>
<p class="reconhecer"><b>Como reconhecer:</b> com a mola solta, as espiras ficam encostadas umas nas outras, e cada ponta termina em um gancho.</p>
<form class="form escolha" data-sob-medida="mola-tracao" data-nome="Mola de tração" data-img="/assets/img/pecas/mola-tracao-aco-recorte-300.webp">
<label>Arame (mm)<input name="fio" inputmode="decimal" placeholder="Ex.: 1,2" data-rot="arame" data-un="mm"></label>
<label>Diâmetro externo (mm)<input name="de" inputmode="decimal" placeholder="Ex.: 10" data-rot="Ø externo" data-un="mm"></label>
<label>Comprimento total (mm)<input name="l" inputmode="decimal" placeholder="De gancho a gancho" data-rot="comprimento total" data-un="mm"></label>
<label>Comprimento do corpo (mm)<input name="lc" inputmode="decimal" placeholder="Se souber" data-rot="corpo" data-un="mm"></label>
<label>Material<select name="material" data-rot="material"><option value="aço mola">Aço mola</option><option value="aço zincado">Aço zincado</option><option value="inox">Inox</option><option value="outro material (ver obs.)">Outro</option></select></label>
<label>Quantidade<input name="qtd" inputmode="numeric" value="100" data-rot="qtd"></label>
<label class="inteiro">Observação<input name="obs" placeholder="Aplicação, tipo de gancho, se tem amostra..." data-rot="obs."></label>
<button class="btn btn--escuro" type="submit">{ic("carrinho", 1.6)}<span>Adicionar ao orçamento</span></button>
</form>
</div>
</div></section>
{destaque(TXT_MOLAS, "desc-mola-tracao")}
<section class="sec" style="padding-top:clamp(40px,6vw,80px)"><div class="wrap">
<div class="tecnico">
<div class="prancha rev">{desenho_tracao()}</div>
<div>
<h2 class="tit barra rev">Como medir a sua mola</h2>
<dl class="legenda rev" style="margin-top:26px"><div><dt>d</dt><dd>espessura do arame</dd></div><div><dt>De</dt><dd>diâmetro externo, por fora das espiras</dd></div><div><dt>L</dt><dd>comprimento total, de gancho a gancho, com a mola solta</dd></div><div><dt>Lc</dt><dd>comprimento do corpo, só a parte enrolada</dd></div></dl>
</div>
</div>
{perguntas_html(faq)}
</div></section>'''
    extra = ld(servico_ld("Fabricação de molas de tração sob medida", rota, "Molas de tração com gancho, fabricadas pela amostra ou pelas medidas do cliente.")) + ld(faq_ld(faq)) + ld(migalhas_ld([("Início", "/"), ("Molas de tração", rota)]))
    return pagina("Molas de tração sob medida com gancho | W Speed",
                  "Fabricamos molas de tração sob medida, pela amostra ou pelas medidas de arame, diâmetro e comprimento. Orçamento pelo WhatsApp e envio a todo o Brasil.",
                  corpo, rota, preload_peca("mola-tracao"), extra)


def mola_torcao():
    rota = "/molas-de-torcao"
    faq = [
        ("O que é uma mola de torção?",
         "É a mola que trabalha girando: as pernas abrem e fecham em volta do corpo e fazem a peça voltar à posição. O corpo é um anel de espiras encostadas, e as pernas saem dele retas ou com a ponta dobrada."),
        ("Como medir uma mola de torção?",
         "Com um paquímetro, meça a espessura do arame, o diâmetro por fora do corpo e o comprimento de cada perna. Conte as voltas do corpo e veja o ângulo entre as pernas com a mola solta."),
        ("O que é o sentido de enrolamento?",
         "É para que lado as espiras giram, e ele muda o lado em que a mola trabalha. Se não souber, escolha Não sei e mande uma foto da mola pelo WhatsApp que a gente identifica."),
        ("Vocês fazem a mola pela amostra?",
         "Fazemos. Se você tem a mola velha, mande uma foto com o paquímetro ou combine o envio da amostra pelo WhatsApp."),
    ]
    corpo = f'''<section class="cab-prod">{facetas()}
<div class="wrap prod">
<div>{palco_mola("mola-torcao", "Mola de torção zincada com corpo em anel e duas pernas com a ponta dobrada")}</div>
<div>
<nav class="migalhas" aria-label="Você está em"><a href="/">Início</a><span aria-hidden="true">/</span><span>Molas de torção</span></nav>
{tipos_mola(rota)}
<h1 class="barra">Molas de <strong>torção</strong> sob medida</h1>
<p class="lead">A mola de torção trabalha girando: as pernas abrem e fecham em volta do corpo e fazem a peça voltar à posição. Fabricamos pela amostra ou pelas medidas que você passar, na quantidade que a sua produção precisa.</p>
<p class="reconhecer"><b>Como reconhecer:</b> o corpo é um anel de espiras encostadas, e duas pernas saem dele, retas ou com a ponta dobrada.</p>
<form class="form escolha" data-sob-medida="mola-torcao" data-nome="Mola de torção" data-img="/assets/img/pecas/mola-torcao-zinco-recorte-300.webp">
<label>Arame (mm)<input name="fio" inputmode="decimal" placeholder="Ex.: 2" data-rot="arame" data-un="mm"></label>
<label>Diâmetro externo (mm)<input name="de" inputmode="decimal" placeholder="Ex.: 40" data-rot="Ø externo" data-un="mm"></label>
<label>Número de voltas<input name="voltas" inputmode="decimal" placeholder="Ex.: 4" data-rot="com" data-un="voltas"></label>
<label>Comprimento das pernas (mm)<input name="l" inputmode="decimal" placeholder="Ex.: 56" data-rot="pernas" data-un="mm"></label>
<label>Ângulo entre as pernas<input name="ang" placeholder="Com a mola solta" data-rot="ângulo"></label>
<label>Sentido de enrolamento<select name="sentido" data-rot="enrolamento"><option value="não sei">Não sei</option><option value="à direita">À direita</option><option value="à esquerda">À esquerda</option></select></label>
<label>Material<select name="material" data-rot="material"><option value="aço zincado">Aço zincado</option><option value="aço mola">Aço mola</option><option value="inox">Inox</option><option value="outro material (ver obs.)">Outro</option></select></label>
<label>Quantidade<input name="qtd" inputmode="numeric" value="100" data-rot="qtd"></label>
<label class="inteiro">Observação<input name="obs" placeholder="Aplicação, forma da ponta, se tem amostra..." data-rot="obs."></label>
<button class="btn btn--escuro" type="submit">{ic("carrinho", 1.6)}<span>Adicionar ao orçamento</span></button>
</form>
</div>
</div></section>
{destaque(TXT_MOLAS, "desc-mola-torcao")}
<section class="sec" style="padding-top:clamp(40px,6vw,80px)"><div class="wrap">
<div class="tecnico">
<div class="prancha rev">{desenho_torcao()}</div>
<div>
<h2 class="tit barra rev">Como medir a sua mola</h2>
<dl class="legenda rev" style="margin-top:26px"><div><dt>d</dt><dd>espessura do arame</dd></div><div><dt>De</dt><dd>diâmetro externo do corpo</dd></div><div><dt>L</dt><dd>comprimento de cada perna, do corpo até a ponta</dd></div></dl><p class="mat rev">Informe também o número de voltas, o ângulo entre as pernas com a mola solta e a forma da ponta.</p>
</div>
</div>
{perguntas_html(faq)}
</div></section>'''
    extra = ld(servico_ld("Fabricação de molas de torção sob medida", rota, "Molas de torção fabricadas pela amostra ou pelas medidas do cliente.")) + ld(faq_ld(faq)) + ld(migalhas_ld([("Início", "/"), ("Molas de torção", rota)]))
    return pagina("Molas de torção sob medida em aço e inox | W Speed",
                  "Fabricamos molas de torção sob medida, pela amostra ou pelas medidas de arame, diâmetro, voltas e pernas. Orçamento pelo WhatsApp e envio a todo o Brasil.",
                  corpo, rota, preload_peca("mola-torcao", "zinco"), extra)


# ------------------------------------------------------------------ bucha roscada
BUCHA_RECONHECER = "É um cilindro vazado de ponta a ponta, com rosca por fora e por dentro. Pode ser reta ou ter um colar em uma das pontas."
# proporções tiradas das fotos do cliente: servem para desenhar o 3D, não são medidas de catálogo
BUCHA_DIMS = {"bucha": {"de": 14, "pe": 1.75, "di": 8.5, "pi": 1.5, "L": 24},
              "bucha-colar": {"de": 14, "pe": 1.75, "di": 9.5, "pi": 1.5, "L": 15, "D": 18, "C": 2.8}}


def bucha():
    faq = [
        ("Para que serve a bucha roscada?",
         "Ela dá uma rosca nova ao furo. Serve para recuperar rosca espanada, para reforçar rosca em alumínio e outros materiais moles e para adaptar uma medida de parafuso a outra."),
        ("Em quais materiais a W Speed fabrica a bucha roscada?",
         "Em aço e em latão, reta ou com colar, na medida que você informar. O envio é para todo o Brasil."),
        ("Qual a diferença entre a bucha reta e a com colar?",
         "A reta entra por inteiro no furo. A com colar encosta na face da peça, o que limita a profundidade e dá um apoio a mais."),
        ("Como pedir a medida certa?",
         "Informe a rosca interna, a rosca externa e o comprimento. Se não souber, mande uma foto da peça ao lado de um paquímetro pelo WhatsApp que a gente ajuda."),
    ]
    variante = lambda rot, tipo, modelo, ativo: (
        f'<button type="button" class="chip" aria-pressed="{"true" if ativo else "false"}" '
        f'data-variante="{e(json.dumps({"tipo": tipo, "dims": BUCHA_DIMS[tipo], "sombra": SOMBRA[tipo], "modelo": modelo}, ensure_ascii=False), quote=True)}">{rot}</button>')
    corpo = f'''<section class="cab-prod">{facetas()}
<div class="wrap prod">
<div>
<div class="palco" style="--sombra:{SOMBRA["bucha-colar"]}" data-visor="{visor_cfg("bucha-colar", BUCHA_DIMS["bucha-colar"], "aco", -0.5, 0.72)}" data-poster="/assets/img/pecas/{{tipo}}-{{mat}}-800.webp">
{img_peca("bucha-colar", "aco", alt="Bucha roscada com colar, em aço", lazy=False)}
<span class="palco__dica">{ic("giro", 1.5)} Arraste para girar</span>
</div>
<div class="controles"><div class="seletor" role="group" aria-label="Modelo da bucha" data-alvo=".prod .palco">{variante("Com colar", "bucha-colar", "com colar", True)}{variante("Reta", "bucha", "reta", False)}</div>{material_toggle(".prod .palco", "Aço", ("latao", "Latão"))}</div>
</div>
<div>
<nav class="migalhas" aria-label="Você está em"><a href="/">Início</a><span aria-hidden="true">/</span><a href="/#pecas">Peças</a><span aria-hidden="true">/</span><span>Bucha roscada</span></nav>
<h1 class="barra">Bucha <strong>roscada</strong> <span class="sub" style="display:block">rosca interna e externa, reta ou com colar</span></h1>
<p class="lead">A bucha roscada tem rosca por fora e por dentro: ela entra no furo da peça e entrega uma rosca nova no lugar. É o caminho para recuperar rosca espanada, reforçar rosca em alumínio e adaptar uma medida de parafuso a outra. Fabricamos em aço e em latão.</p>
<p class="reconhecer"><b>Como reconhecer:</b> {e(BUCHA_RECONHECER)}</p>
<form class="form escolha" data-sob-medida="bucha" data-nome="Bucha roscada" data-img="/assets/img/pecas/bucha-colar-aco-recorte-300.webp">
<label>Rosca interna<input name="ri" placeholder="Ex.: M8 × 1,25" data-rot="rosca interna"></label>
<label>Rosca externa<input name="re" placeholder="Ex.: M14 × 1,5" data-rot="rosca externa"></label>
<label>Comprimento (mm)<input name="l" inputmode="decimal" placeholder="Ex.: 20" data-rot="comprimento" data-un="mm"></label>
<label>Modelo<select name="modelo" data-rot="modelo"><option value="com colar">Com colar</option><option value="reta">Reta</option></select></label>
<label>Material<select name="material" data-rot="material"><option value="aço">Aço</option><option value="latão">Latão</option></select></label>
<label>Quantidade<input name="qtd" inputmode="numeric" value="100" data-rot="qtd"></label>
<label class="inteiro">Observação<input name="obs" placeholder="Aplicação, se tem amostra..." data-rot="obs."></label>
<button class="btn btn--escuro" type="submit">{ic("carrinho", 1.6)}<span>Adicionar ao orçamento</span></button>
</form>
</div>
</div></section>
<section class="sec" id="medidas" style="padding-top:clamp(40px,6vw,80px)"><div class="wrap">
<h2 class="tit barra rev">O que informar no <strong>pedido</strong></h2>
<div class="tecnico">
<div class="prancha">{desenho_bucha()}</div>
<div><dl class="legenda"><div><dt>d1</dt><dd>rosca interna, a do parafuso que vai entrar</dd></div><div><dt>d2</dt><dd>rosca externa, a que fica no furo da peça</dd></div><div><dt>L</dt><dd>comprimento da rosca externa</dd></div><div><dt>D, C</dt><dd>diâmetro e altura do colar, no modelo com colar</dd></div></dl></div>
</div>
{perguntas_html(faq)}
</div></section>'''
    extra = ld(servico_ld("Fabricação de bucha roscada reta e com colar", "/bucha-roscada", "Bucha com rosca interna e externa, em aço e latão, para recuperar rosca espanada, reforçar rosca em alumínio e adaptar medidas de parafuso.")) + ld(faq_ld(faq)) + ld(migalhas_ld([("Início", "/"), ("Bucha roscada", "/bucha-roscada")]))
    return pagina("Bucha roscada em aço e latão, reta ou com colar | W Speed",
                  "Bucha roscada reta ou com colar, em aço e latão, para recuperar rosca espanada e reforçar rosca em alumínio. Orçamento pelo WhatsApp e envio a todo o Brasil.",
                  corpo, "/bucha-roscada", preload_peca("bucha-colar", "aco"), extra)


# ------------------------------------------------------------------ usinagem
def usinagem():
    faq = [
        ("O que a W Speed usina?",
         "Peças conforme desenho ou amostra do cliente, em aço carbono e aço inoxidável, para indústrias, oficinas mecânicas e equipamentos agrícolas e hidráulicos."),
        ("Preciso ter o desenho técnico para pedir o orçamento?",
         "Se tiver o desenho é melhor, mas também aceitamos amostra da peça ou medidas exatas."),
        ("Em que formato mando o desenho?",
         "PDF, DWG ou uma foto com as medidas, direto na conversa do WhatsApp. Se for pela amostra, a gente combina o envio."),
        ("Vocês fazem peça única?",
         "Sim. Atendemos desde peças individuais até lotes grandes, conforme a necessidade do cliente."),
        ("A W Speed entrega em outras cidades?",
         "Sim, para todas as regiões do Brasil. Informe a sua cidade quando mandar a lista, assim a gente calcula o frete junto com o orçamento."),
    ]
    corpo = f'''<section class="cab-prod">{facetas()}
<div class="wrap prod">
<div class="prancha rev">{desenho_usinagem()}</div>
<div>
<nav class="migalhas" aria-label="Você está em"><a href="/">Início</a><span aria-hidden="true">/</span><span>Usinagem sob medida</span></nav>
<h1 class="barra"><strong>Usinagem</strong> sob medida <span class="sub" style="display:block">peças especiais para sua Indústria</span></h1>
<p class="lead">{e(TXT_USINAGEM)}</p>
<div style="margin-top:22px">{lista_ok(ITENS_USINAGEM)}</div>
<div class="ctas" style="margin-top:30px">{btn("Envie seu desenho ou amostra", zap_link("usinagem"), "escuro", "zap")}{btn("Descrever a peça", "#descrever", "linha", "baixo")}</div>
</div>
</div></section>
<section class="sec" id="descrever" style="padding-top:clamp(40px,6vw,80px)"><div class="wrap fluxo">
<div>
<h2 class="tit barra rev">Como pedir</h2>
<ol class="passos rev">
<li><div><b>Descreva a peça</b><span>Diga o que é, o material e a quantidade no formulário ao lado.</span></div></li>
<li><div><b>Envie a lista pelo WhatsApp</b><span>Ela pode ir junto com bujões, posicionadores e molas.</span></div></li>
<li><div><b>Mande o desenho na conversa</b><span>PDF, DWG ou uma foto com as medidas. Se for pela amostra, a gente combina o envio.</span></div></li>
</ol>
</div>
<form class="form escolha rev" data-sob-medida="usinagem" data-nome="Peça usinada sob medida">
<label class="inteiro">O que é a peça<textarea name="desc" required placeholder="Ex.: bucha de bronze Ø 30 x 40 mm, pino com rosca M10..." data-rot="peça"></textarea></label>
<label>Material<select name="material" data-rot="material"><option value="aço carbono">Aço carbono</option><option value="inox">Inox</option><option value="outro material (ver obs.)">Outro</option></select></label>
<label>Quantidade<input name="qtd" inputmode="numeric" value="10" data-rot="qtd"></label>
<label class="inteiro">Observação<input name="obs" placeholder="Prazo, tratamento, tolerâncias..." data-rot="obs."></label>
<button class="btn btn--escuro" type="submit">{ic("carrinho", 1.6)}<span>Adicionar ao orçamento</span></button>
</form>
</div></section>
<section class="sec" style="padding-top:0"><div class="wrap">
<h2 class="tit barra centro rev" style="text-align:center">Dúvidas sobre usinagem</h2>
{perguntas_html(faq)}
</div></section>'''
    extra = ld(servico_ld("Usinagem de peças sob medida", "/usinagem", TXT_USINAGEM)) + ld(faq_ld(faq)) + ld(migalhas_ld([("Início", "/"), ("Usinagem sob medida", "/usinagem")]))
    return pagina("Usinagem sob medida pelo desenho ou amostra | W Speed",
                  "Peças usinadas sob medida a partir do seu desenho técnico ou de uma amostra, em aço carbono ou inox. Peça única ou lote. Orçamento pelo WhatsApp.",
                  corpo, "/usinagem", "", extra)


# ------------------------------------------------------------------ contato
def contato():
    corpo = f'''<section class="cab-prod">{facetas()}
<div class="wrap prod contato">
<div>
<nav class="migalhas" aria-label="Você está em"><a href="/">Início</a><span aria-hidden="true">/</span><span>Contato</span></nav>
<h1 class="barra">Entre em <strong>contato</strong> <span class="sub" style="display:block">para pedidos, orçamentos ou dúvidas</span></h1>
<p class="lead">Envie seu desenho, amostra ou medidas da peça que precisa que nós respondemos rapidinho!</p>
<div class="ctas" style="margin-top:30px">{btn("Solicitar orçamento agora", zap_link("contato"), "escuro", "zap")}</div>
</div>
<dl class="dados rev">
<div><dt>WhatsApp</dt><dd><a href="{zap_link("contato-numero")}">{TEL_VER}</a></dd></div>
<div><dt>Horário de atendimento</dt><dd>Segunda a sexta-feira, das 8h às 12h e das 13h30 às 17h30</dd></div>
<div><dt>Onde atendemos</dt><dd>Todo o Brasil</dd></div>
<div><dt>Instagram</dt><dd><a href="{INSTAGRAM}" target="_blank" rel="noopener">@wfix.speed</a></dd></div>
</dl>
</div></section>'''
    extra = ld(migalhas_ld([("Início", "/"), ("Contato", "/contato")]))
    return pagina("Contato: orçamento de peças industriais | W Speed",
                  f"Peça orçamento de peças industriais e usinagem sob medida pelo WhatsApp {TEL_VER}, de segunda a sexta em horário comercial. Atendemos todo o Brasil.",
                  corpo, "/contato", "", extra)


# ------------------------------------------------------------------ ponte para o WhatsApp
def obrigado():
    corpo = f'''<section class="ponte"><div>
<img src="/assets/img/logo-96.webp" width="139" height="46" alt="W Speed">
<h1>Estamos abrindo o seu WhatsApp</h1>
<p id="ponte-txt">Se não abrir sozinho, toque no botão abaixo.</p>
<div class="gira" aria-hidden="true"></div>
<div class="ctas" style="justify-content:center"><a class="btn btn--escuro" id="vai" href="https://wa.me/{WHATSAPP}">{ZAP}<span>Abrir o WhatsApp</span></a><a class="btn btn--linha" href="/"><span>Voltar ao site</span></a></div>
</div></section>
<script>
(function(){{
  var W='{WHATSAPP}', q=new URLSearchParams(location.search), c=q.get('c')||'site';
  var msgs={{usinagem:'Olá, W Speed! Vim pelo site e quero orçamento de uma peça usinada sob medida. Vou mandar o desenho aqui.'}};
  var msg=msgs[c]||(c.indexOf('especial')===0?'Olá, W Speed! Vim pelo site e preciso de uma medida especial.':'Olá, W Speed! Vim pelo site e quero um orçamento.');
  try{{ msg=sessionStorage.getItem('ws_msg')||msg; sessionStorage.removeItem('ws_msg'); }}catch(e){{}}
  var dest='https://wa.me/'+W+'?text='+encodeURIComponent(msg); document.getElementById('vai').href=dest;
  var t0=Date.now(), pronto=false, partiu=false;
  function vai(){{ if(partiu) return; partiu=true; location.replace(dest); }}
  function talvez(){{ if(pronto && Date.now()-t0>=900) vai(); }}
  window.dataLayer=window.dataLayer||[];
  window.dataLayer.push({{event:'conversao_whatsapp',contexto:c,eventCallback:function(){{pronto=true;talvez();}},eventTimeout:2000}});
  {"" if GTM_ID else "pronto=true;"}
  setTimeout(talvez,900); setTimeout(vai,2600);
}})();
</script>'''
    return pagina("Abrindo o WhatsApp | W Speed", "Abrindo a conversa com a W Speed no WhatsApp.", corpo, "/obrigado", robots="noindex,nofollow", casca=False)


def nao_achou():
    corpo = f'''<section class="ponte"><div>
<img src="/assets/img/logo-96.webp" width="139" height="46" alt="W Speed">
<h1>Esta página não existe</h1><p>Talvez o endereço tenha mudado. As peças estão todas na página inicial.</p>
<div class="ctas" style="justify-content:center;margin-top:28px">{btn("Ver as peças", "/#pecas")}</div></div></section>'''
    return pagina("Página não encontrada | W Speed", "Página não encontrada.", corpo, "/404", robots="noindex,nofollow", casca=False)


# ------------------------------------------------------------------ arquivos para as IAs
def guia_ia(paginas, rotas):
    """llms.txt (índice) e llms-full.txt (tabelas e perguntas), montados do que já está nas páginas."""
    def dados(r):
        h = paginas["index.html" if r == "/" else r[1:] + ".html"]
        titulo = unescape(re.search(r"<title>(.*?)</title>", h)[1]).removesuffix(" | W Speed")
        desc = unescape(re.search(r'<meta name="description" content="(.*?)"', h)[1])
        blocos = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h)]
        return titulo, desc, [(q["name"], q["acceptedAnswer"]["text"]) for b in blocos if b["@type"] == "FAQPage" for q in b["mainEntity"]]

    resumo = ("# W Speed\n\n> A W Speed (Instagram @wfix.speed) é uma fabricante brasileira de peças industriais: bujões DIN 906, 908 e 910, "
              "posicionadores com mola e esfera, buchas roscadas, molas de compressão, tração e torção e usinagem sob medida. "
              "Atende todo o Brasil, com orçamento pelo WhatsApp.\n")
    fatos = ["Materiais: aço carbono e aço inoxidável. Bujões e posicionadores em aço com oxidação preta ou inox; buchas em aço ou latão.",
             "Medidas dos bujões conforme as normas DIN, iguais em qualquer fabricante; medidas, roscas e materiais especiais sob encomenda.",
             "Clientes: indústrias, oficinas mecânicas, máquinas agrícolas, tratores, sistemas hidráulicos e redutores.",
             "Quantidades: de peças individuais a lotes grandes.",
             "Como pedir: montar a lista no site e enviar pelo WhatsApp, ou mandar desenho (PDF, DWG), foto com medidas ou amostra. Preço e prazo são informados no orçamento; o site não publica preços.",
             f"Atendimento: {HORARIO}."]
    contato = f"\n## Contato\n\n- WhatsApp: {TEL_VER}\n- Instagram: {INSTAGRAM}\n- Site: {DOMINIO}/\n"
    indice = [resumo, *[f"- {f}" for f in fatos], "\n## Páginas\n"]
    indice += [f"- [{dados(r)[0]}]({DOMINIO}{r}): {dados(r)[1]}" for r in rotas[1:]]
    indice += [f"\n## Detalhes\n\n- [Tabelas de medidas e perguntas frequentes]({DOMINIO}/llms-full.txt)", contato]
    (RAIZ / "llms.txt").write_text("\n".join(indice))

    completo = [resumo, *[f"- {f}" for f in fatos], "\nMedidas em milímetros, salvo quando a coluna indica outra unidade."]
    for r in rotas:
        titulo, desc, faq = dados(r)
        completo.append(f"\n## {titulo}\n\n{DOMINIO}{r}\n\n{desc}")
        p = POR_SLUG.get(r[1:])
        if p:
            completo.append("\n" + p["texto"] + "\n\nColunas: " + "; ".join(f"{k} = {v}" for k, v in p["letras"]) + ".")
            for t in p["tabelas"]:
                linhas = "\n".join("| " + " | ".join(num(v) for v in lin) + " |" for lin in t["linhas"])
                completo.append(f"\n### {t['titulo']}\n\n| " + " | ".join(t["cab"]) + " |\n|" + "---|" * len(t["cab"]) + "\n" + linhas)
        if faq:
            completo.append("\n### Perguntas frequentes\n\n" + "\n\n".join(f"**{q}**\n{a}" for q, a in faq))
    completo.append(contato)
    (RAIZ / "llms-full.txt").write_text("\n".join(completo))


# ------------------------------------------------------------------ montar
def main():
    import subprocess
    subprocess.run([str(ESBUILD), str(JS_FONTE), "--minify", "--target=es2017", "--legal-comments=none", f"--outfile={JS}"], check=True, capture_output=True)
    paginas = {"index.html": home(), "bucha-roscada.html": bucha(), "molas-de-compressao.html": molas(), "molas-de-tracao.html": mola_tracao(), "molas-de-torcao.html": mola_torcao(), "usinagem.html": usinagem(), "contato.html": contato(),
               "obrigado.html": obrigado(), "404.html": nao_achou()}
    for p in PRODUTOS:
        paginas[p["slug"] + ".html"] = produto(p)
    for nome, html in paginas.items():
        (RAIZ / nome).write_text(html)
    rotas = ["/"] + ["/" + p["slug"] for p in PRODUTOS] + ["/bucha-roscada", "/molas-de-compressao", "/molas-de-tracao", "/molas-de-torcao", "/usinagem", "/contato"]
    hoje = date.today().isoformat()
    def item_sitemap(r):
        imgs = "".join(f"<image:image><image:loc>{DOMINIO}/assets/img/pecas/{i}-800.webp</image:loc></image:image>" for i in IMG_ROTA.get(r, ()))
        return f"<url><loc>{DOMINIO}{r}</loc><lastmod>{hoje}</lastmod>{imgs}</url>"
    (RAIZ / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
                                      + "".join(map(item_sitemap, rotas)) + "</urlset>\n")
    # o /obrigado não entra no Disallow: precisa ser lido para o Google ver o noindex
    (RAIZ / "robots.txt").write_text("User-agent: *\n" + ("Allow: /\n" if INDEXAR else "Disallow:\n") + f"\nSitemap: {DOMINIO}/sitemap.xml\n")
    guia_ia(paginas, rotas)
    (RAIZ / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY)
    print(f"  {len(paginas)} páginas  site.js v={hash_de(JS)}  pecas3d v={hash_de(JS3D)}  indexar={INDEXAR}")


if __name__ == "__main__":
    main()
