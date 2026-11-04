// Capturas de página inteira (desktop e celular) com o 3D carregado e as revelações disparadas.
// node tools/shots.mjs <saida> [rota ...]
import { createRequire } from 'module';
const require = createRequire('/Users/Leonardo/dev/agencia-ia-escritorio/package.json');
const pw = require('playwright');
const saida = process.argv[2] || '_src/shots';
const rotas = process.argv.slice(3).length ? process.argv.slice(3) : ['/'];
const BASE = process.env.BASE || 'http://127.0.0.1:4220';
const fs = await import('fs');
fs.mkdirSync(saida, { recursive: true });
const nav = await pw.chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
for (const [nome, vp, movel] of [['desk', { width: 1440, height: 900 }, false], ['cel', { width: 390, height: 844 }, true]]) {
  if (process.env.SO && process.env.SO !== nome) continue;
  const ctx = await nav.newContext({ viewport: vp, deviceScaleFactor: 1, isMobile: movel, hasTouch: movel });
  const pg = await ctx.newPage();
  pg.on('pageerror', (e) => console.log('pageerror', e.message));
  pg.on('console', (m) => { if (m.type() === 'error') console.log('console', m.text()); });
  for (const r of rotas) {
    await pg.goto(BASE + r, { waitUntil: 'networkidle' });
    await pg.mouse.move(vp.width / 2, vp.height / 2);
    await pg.mouse.wheel(0, 10);
    await pg.waitForTimeout(1500);
    const h = await pg.evaluate(() => document.documentElement.scrollHeight);
    for (let y = 0; y < h; y += vp.height * 0.6) { await pg.evaluate((yy) => window.scrollTo(0, yy), y); await pg.waitForTimeout(160); }
    await pg.evaluate(() => window.scrollTo(0, 0));
    await pg.waitForTimeout(2600);
    const arq = `${saida}/${nome}${r.replace(/\//g, '_') || '_'}.png`;
    await pg.screenshot({ path: arq, fullPage: true });
    console.log(arq, h);
  }
  await ctx.close();
}
await nav.close();
