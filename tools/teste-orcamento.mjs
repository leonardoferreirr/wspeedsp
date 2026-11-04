// Fluxo completo: tabela -> lista -> formulário -> /obrigado -> link do WhatsApp com a mensagem.
import { createRequire } from 'module';
const require = createRequire('/Users/Leonardo/dev/agencia-ia-escritorio/package.json');
const pw = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:4220';
const nav = await pw.chromium.launch();
const ctx = await nav.newContext({ viewport: { width: 1280, height: 860 } });
const pg = await ctx.newPage();
const erros = [];
pg.on('pageerror', (e) => erros.push(e.message));
await ctx.route('https://wa.me/**', (r) => r.fulfill({ status: 200, body: 'wa' }));
await pg.goto(BASE + '/bujao-din-906', { waitUntil: 'networkidle' });
// troca para inox, adiciona a linha 3/4" pela tabela e a 1/2" pelo cartão com 20 un.
await pg.click('.material button[data-mat="inox"]');
await pg.click('#t-bspt tbody tr:nth-child(5) td.add button');
await pg.fill('.escolha .qtd input', '20');
await pg.click('.escolha [data-adiciona]');
// aba métrica, seleciona M20 e adiciona
await pg.click('.abas [aria-controls="t-metrica"]');
await pg.click('#t-metrica tbody tr:nth-child(7) td:first-child');
const nomeEsc = await pg.textContent('.escolha__nome');
await pg.click('.escolha [data-adiciona]');
await pg.goto(BASE + '/posicionador-com-mola-e-esfera', { waitUntil: 'networkidle' });
await pg.click('tbody tr:nth-child(11) td.add button');
await pg.goto(BASE + '/molas-de-compressao', { waitUntil: 'networkidle' });
await pg.fill('input[name="fio"]', '2,5'); await pg.fill('input[name="de"]', '20'); await pg.fill('input[name="lo"]', '50');
await pg.click('form[data-sob-medida] button[type="submit"]');
await pg.waitForTimeout(500);
const contagem = await pg.textContent('.bt-orc .n');
const itens = await pg.$$eval('.itens .item', (l) => l.map((x) => x.innerText.replace(/\s+/g, ' ').trim()));
await pg.fill('#form-orc input[name="nome"]', 'Teste Site');
await pg.fill('#form-orc input[name="cidade"]', 'Uberlândia/MG');
const [req] = await Promise.all([
  pg.waitForRequest((r) => r.url().startsWith('https://wa.me/'), { timeout: 8000 }),
  pg.click('.gaveta__base button[type="submit"]'),
]);
const url = new URL(req.url());
console.log('escolha:', nomeEsc.replace(/\s+/g, ' '));
console.log('contagem:', contagem, '| itens:', itens.length);
itens.forEach((i) => console.log('  -', i));
console.log('destino:', url.origin + url.pathname);
console.log('mensagem:\n' + url.searchParams.get('text'));
console.log('erros:', erros);
await nav.close();
