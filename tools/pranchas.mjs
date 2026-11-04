import { createRequire } from 'module';
const require = createRequire('/Users/Leonardo/dev/agencia-ia-escritorio/package.json');
const pw = require('playwright');
const nav = await pw.chromium.launch();
const pg = await nav.newPage({ viewport: { width: 1440, height: 900 } });
for (const r of ['/bujao-din-908', '/bujao-din-910', '/posicionador-com-mola-e-esfera', '/molas-de-compressao']) {
  await pg.goto('http://127.0.0.1:4220' + r, { waitUntil: 'networkidle' });
  const el = await pg.$('.prancha'); await el.scrollIntoViewIfNeeded(); await pg.waitForTimeout(2600);
  await el.screenshot({ path: `_src/shots/prancha${r.replace(/\//g, '_')}.png` });
}
await nav.close();
