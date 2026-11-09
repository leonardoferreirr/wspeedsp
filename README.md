# W Speed: site da linha industrial

Catálogo da W Speed (@wfix.speed) com bujões DIN 906, 908 e 910,
posicionador com mola e esfera, bucha roscada, molas de compressão, tração e torção e usinagem sob medida. A pessoa escolhe a medida
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
| `python3 tools/grupo.py` | foto com todas as peças, que abre o topo da inicial (usa os renders de `tools/renders.py`) |
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
- No ar em **www.wfixspeed.com.br**. O domínio sem www e o wspeedsp.vercel.app redirecionam para ele (`redirects` no `vercel.json`).
- `build.py` gera também `sitemap.xml`, `robots.txt`, `llms.txt` e `llms-full.txt`. Depois de publicar mudança de texto: `python3 tools/indexnow.py` avisa o Bing.

## Notas (04/11/2026)

Desempenho no celular entre 99 e 100 em todas as páginas, acessibilidade 100 e boas práticas 100.
O SEO aparece em 69 só porque o `noindex` está ligado de propósito.

## Ajustes de 06/11 (áudios e textos da IA dele, a Dola)

Topo com todas as peças à vista (miniaturas trocam o 3D), faixa "Atendemos todo o Brasil" no meio da inicial, textos por página (`TXT_*` no build.py), perguntas frequentes novas, página `/contato` e bucha em aço e latão.

## Pendências

- [ ] Perfil da Empresa no Google: depende do endereço e da verificação feita pelo Wanderley.
- [ ] Fotos das peças usinadas (ele disse que ia mandar).
- [ ] Molas: o texto que ele mandou diz aço carbono e inox nas três, então o inox entrou em tração e torção (09/11). Falta confirmar se o aço zincado continua. O 3D segue as fotos que ele mandou; as proporções não são medidas de catálogo.
- [ ] Bucha roscada: materiais são aço e latão (áudio de 06/11). Falta a tabela de medidas dele; até lá a página pede as medidas no formulário.
- [ ] Confirmar o material do aço (a FBP usa 9SMn28, classe 5.8; a Ômega, SAE 1020). O site diz só
      "aço com oxidação preta".
- [ ] Confirmar se ele fabrica todas as medidas da tabela, inclusive a série NPTF.
- [ ] CNPJ e endereço para o rodapé (e o schema de empresa local). O horário já entrou em /contato e no rodapé.
- [ ] A pergunta "Quanto tempo demora para chegar o orçamento?" veio cortada no print dele: a resposta usa o horário de atendimento até ele mandar o texto inteiro.
- [ ] Áudio de 0:11 das 13:50 do dia 03/11 não estava na pasta de briefing.
- [ ] Linha automotiva separada (peças de moto), para mais tarde, como ele sugeriu.
