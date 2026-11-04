# W Speed: site da linha industrial

Catálogo da W Speed (@wfix.speed) com bujões DIN 906, 908 e 910,
posicionador com mola e esfera, molas de compressão e usinagem sob medida. A pessoa escolhe a medida
na tabela, monta a lista de orçamento e a lista vai pronta para o WhatsApp (11) 98890-4107.

## Como rodar

    python3 build.py                 # gera as páginas (HTML na raiz)
    python3 tools/serve.py 4220      # prévia local (imita o cleanUrls da Vercel)

Outras ferramentas:

| Comando | Faz |
|---|---|
| `cd tools/pecas3d && npm run pacote` | empacota o motor 3D (three.js) em `assets/js/pecas3d.js` |
| `python3 tools/renders.py` | gera as imagens das peças (aço e inox) pelo mesmo motor 3D |
| `python3 tools/logo.py` | recorta o logo do post do Instagram (`_src/post-fabricamos.webp`) |
| `python3 tools/og.py` | imagem de compartilhamento 1200x630 |
| `tools/lh.sh /rota 3` | Lighthouse no celular (Chromium do Playwright), mediana de 3 |
| `node tools/teste-orcamento.mjs` | testa o fluxo tabela, lista, WhatsApp |
| `node tools/cel.mjs _src/shots /rota` | capturas do celular tela a tela |

## Como funciona

- Medidas em `_src/produtos.json`, conforme as normas DIN. As tabelas dos bujões vieram do catálogo
  técnico da FBP e a do posicionador, do OM615 da Ômega Fix (similar ao GN 615). São dados de norma,
  iguais para qualquer fabricante.
- As peças em 3D são geradas a partir dessas medidas: rosca helicoidal, sextavado interno, cabeça
  sextavada com chanfro, colar, esfera e mola. Nenhuma foto de concorrente foi usada.
- O 3D (130 KB comprimido) só carrega na primeira interação. Antes disso aparece o pôster, renderizado
  com o mesmo enquadramento, por isso a troca não dá pulo.
- A lista de orçamento fica no navegador (`localStorage`). Ao enviar, a mensagem passa pelo
  `sessionStorage` até o `/obrigado`, que dispara o evento `conversao_whatsapp` e abre o WhatsApp.
- `INDEXAR = False` até a aprovação do cliente e o domínio. Depois disso, trocar `DOMINIO` e `INDEXAR`.

## Notas (04/11/2026)

Desempenho no celular entre 99 e 100 em todas as páginas, acessibilidade 100 e boas práticas 100.
O SEO aparece em 69 só porque o `noindex` está ligado de propósito.

## Pendências

- [ ] Domínio **wspeedsp.com.br**: do próprio cliente, registrado pela Hostinger e com DNS
      estacionado (`dns-parking.com`). Vence em 02/07/2027. Precisa do acesso à Hostinger para apontar
      para a Vercel.
- [ ] Depois do domínio: `DOMINIO = "https://www.wspeedsp.com.br"`, `INDEXAR = True`, Google Search
      Console com o sitemap e Perfil da Empresa no Google. O cliente dele procura no Google.
- [ ] Fotos das molas e das peças usinadas (ele disse que ia mandar).
- [ ] Confirmar o material do aço (a FBP usa 9SMn28, classe 5.8; a Ômega, SAE 1020). O site diz só
      "aço com oxidação preta".
- [ ] Confirmar se ele fabrica todas as medidas da tabela, inclusive a série NPTF.
- [ ] CNPJ, endereço e horário para o rodapé (e o schema de empresa local).
- [ ] Áudio de 0:11 das 13:50 do dia 03/11 não estava na pasta de briefing.
- [ ] Linha automotiva separada (peças de moto), para mais tarde, como ele sugeriu.
