#!/usr/bin/env python3
"""Avisa o Bing e os outros buscadores do IndexNow que o site mudou. Rodar depois de publicar: python3 tools/indexnow.py"""
import json, re, urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
fonte = (RAIZ / "build.py").read_text()
dominio = re.search(r'DOMINIO = "(.+?)"', fonte)[1]
chave = re.search(r'INDEXNOW_KEY = "(.+?)"', fonte)[1]
urls = re.findall(r"<loc>(.*?)</loc>", (RAIZ / "sitemap.xml").read_text())
corpo = {"host": dominio.split("//")[1], "key": chave, "keyLocation": f"{dominio}/{chave}.txt", "urlList": urls}
req = urllib.request.Request("https://api.indexnow.org/indexnow", json.dumps(corpo).encode(), {"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as r:
    print(r.status, f"{len(urls)} endereços enviados")
