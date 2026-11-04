#!/bin/bash
# Lighthouse no celular (throttling devtools, mais próximo do real que o simulate), N vezes, mediana.
# Usa o Chromium do Playwright: nunca o Chrome do Leonardo.  tools/lh.sh [rota] [N]
cd "$(dirname "$0")/.."
LH=$(ls -d ~/.npm/_npx/*/node_modules/.bin/lighthouse | head -1)
export CHROME_PATH=~/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell
ROTA=${1:-/}; N=${2:-3}; NOME=$(echo "$ROTA" | tr '/' '_')
for i in $(seq 1 "$N"); do
  "$LH" "http://127.0.0.1:4220$ROTA" --only-categories=performance,accessibility,best-practices,seo \
    --throttling-method=devtools --form-factor=mobile --screenEmulation.mobile --quiet \
    --chrome-flags="--no-sandbox --disable-gpu" \
    --output=json --output-path=".audit/lh$NOME-$i.json" > /dev/null 2>&1
done
python3 - "$N" "$NOME" <<'PY'
import json, sys, statistics as st
n, nome = int(sys.argv[1]), sys.argv[2]; runs = []
for i in range(1, n+1):
    d = json.load(open(f".audit/lh{nome}-{i}.json")); a = d["audits"]; c = d["categories"]
    runs.append({"perf": round(c["performance"]["score"]*100), "a11y": round(c["accessibility"]["score"]*100),
                 "bp": round(c["best-practices"]["score"]*100), "seo": round(c["seo"]["score"]*100),
                 "FCP": a["first-contentful-paint"]["numericValue"]/1000, "LCP": a["largest-contentful-paint"]["numericValue"]/1000,
                 "TBT": a["total-blocking-time"]["numericValue"], "CLS": a["cumulative-layout-shift"]["numericValue"]})
for i, r in enumerate(runs, 1):
    print(f"  run{i}: perf {r['perf']}  FCP {r['FCP']:.1f}s  LCP {r['LCP']:.1f}s  TBT {r['TBT']:.0f}ms  CLS {r['CLS']:.3f}")
m = lambda k: st.median(r[k] for r in runs)
print(f"MEDIANA {nome}: perf {m('perf'):.0f}  a11y {m('a11y'):.0f}  boas práticas {m('bp'):.0f}  seo {m('seo'):.0f}")
d = json.load(open(f".audit/lh{nome}-1.json"))
falhas = [(k, v["title"]) for k, v in d["audits"].items() if v.get("score") is not None and v["score"] < 0.9 and v.get("scoreDisplayMode") in ("binary", "numeric", "metricSavings")]
for k, t in falhas[:14]: print("   -", k, ":", t)
PY
