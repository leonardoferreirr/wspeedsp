// W Speed: peças industriais em 3D geradas a partir das tabelas da norma.
// Nenhum modelo pronto: rosca helicoidal, sextavados, colar, esfera e mola saem das medidas (mm).
//
// API
//   criarVisor(canvas, { dpr, auto, arrastar, aoPronto }) -> visor
//   visor.mostrar(tipo, dims, { material, instante })   tipo: '906' | '908' | '910' | 'posicionador' | 'mola' | 'bucha' | 'bucha-colar'
//   visor.material('aco' | 'inox' | 'zincado')
//   visor.comprimir(k)  (mola: 0 solta, 1 comprimida)
//   visor.foto(largura, altura) -> dataURL PNG com fundo transparente
//   visor.pausar() / visor.retomar() / visor.destruir()
//   montarPeca(tipo, dims) -> THREE.Group (para testes)

import {
  WebGLRenderer, Scene, PerspectiveCamera, Group, Mesh, BufferGeometry, Float32BufferAttribute,
  MeshPhysicalMaterial, MeshBasicMaterial, PMREMGenerator, ACESFilmicToneMapping, SRGBColorSpace,
  Shape, ShapeGeometry, SphereGeometry, PlaneGeometry, BoxGeometry, TubeGeometry, Curve, Vector3,
  BackSide, DoubleSide, Box3, Sphere, Color,
} from 'three';

const TAU = Math.PI * 2;
const lim = (v, a, b) => Math.min(b, Math.max(a, v));
const suave = (t) => t * t * (3 - 2 * t);

// ------------------------------------------------------------------ roscas
const BSP = { '1/16': 7.723, '1/8': 9.728, '1/4': 13.157, '3/8': 16.662, '1/2': 20.955, '3/4': 26.441, '1': 33.249, '1.1/4': 41.91, '1.1/2': 47.803, '2': 59.614 };
const NPT = { '1/16': 7.94, '1/8': 10.29, '1/4': 13.72, '3/8': 17.15, '1/2': 21.34, '3/4': 26.67, '1': 33.4, '1.1/4': 42.16, '1.1/2': 48.26, '2': 60.33 };
const GROSSA = { 3: 0.5, 4: 0.7, 5: 0.8, 6: 1, 8: 1.25, 10: 1.5, 12: 1.75, 16: 2, 20: 2.5, 24: 3 };

/** '1/2"-14' | 'M12 × 1,5' | 'M8' -> { d, passo, cone, angulo } */
export function lerRosca(rotulo, tipoRosca) {
  const r = String(rotulo).replace(',', '.');
  const m = r.match(/M\s*(\d+(?:\.\d+)?)(?:\s*[×x]\s*(\d+(?:\.\d+)?))?/i);
  const cone = tipoRosca === 'bspt' || tipoRosca === 'nptf' || tipoRosca === 'metrica-conica';
  if (m) {
    const d = parseFloat(m[1]);
    const passo = m[2] ? parseFloat(m[2]) : (GROSSA[d] || d * 0.15);
    return { d, passo, cone, perfil: 0.6134 };
  }
  const p = r.match(/([\d./]+)"\s*-\s*([\d.]+)/);
  const nominal = p ? p[1] : '1/2';
  const tpi = p ? parseFloat(p[2]) : 14;
  const npt = tipoRosca === 'nptf';
  const d = (npt ? NPT : BSP)[nominal] || 20;
  return { d, passo: 25.4 / tpi, cone, perfil: npt ? 0.8 : 0.64 };
}

/** '5/32"' -> mm ; 12 -> 12 */
export function medida(v) {
  if (typeof v === 'number') return v;
  const s = String(v).replace('"', '').replace(',', '.').trim();
  const m = s.match(/^(?:(\d+)\.)?(\d+)\/(\d+)$/);
  if (m) return ((m[1] ? +m[1] : 0) + (+m[2] / +m[3])) * 25.4;
  const n = parseFloat(s);
  return Number.isFinite(n) ? (s.includes('/') ? n * 25.4 : n) : 0;
}

// ------------------------------------------------------------------ geometrias
/**
 * Superfície da rosca helicoidal entre y0 (ponta) e y1. Raio maior pode variar (cônica).
 * corte(x, y, z) -> true para descartar triângulos (fenda do posicionador).
 */
function rosca({ y0, y1, rMaj0, rMaj1, passo, prof, segA = 128, porPasso = 14, chPonta = true, chTopo = false, ch, corte, redondo = false }) {
  const len = y1 - y0;
  const nY = lim(Math.ceil((len / passo) * porPasso), 12, 420);
  ch = ch ?? prof * 1.1;
  const pos = new Float32Array((nY + 1) * segA * 3);
  const sulco = redondo ? new Float32Array((nY + 1) * segA) : null;
  let o = 0, os = 0;
  for (let j = 0; j <= nY; j++) {
    const y = y0 + (len * j) / nY;
    const rMaj = rMaj0 + ((rMaj1 - rMaj0) * (y - y0)) / len;
    const rMin = rMaj - prof;
    for (let i = 0; i < segA; i++) {
      const a = (i / segA) * TAU;
      let f = y / passo - a / TAU;
      f -= Math.floor(f);
      const tri = 1 - Math.abs(2 * f - 1);
      let k = lim((tri - 0.1) / 0.78, 0, 1);
      k = redondo ? 1 - Math.pow(1 - tri, 2.4) : suave(k) * 0.45 + k * 0.55;
      if (sulco) sulco[os++] = 1 - k;
      let r = rMin + prof * k;
      if (chPonta) r = Math.min(r, rMin - ch * 0.35 + (y - y0) * 1.0);
      if (chTopo) r = Math.min(r, rMin - ch * 0.35 + (y1 - y) * 1.0);
      pos[o++] = r * Math.cos(a);
      pos[o++] = y;
      pos[o++] = r * Math.sin(a);
    }
  }
  const idx = [];
  for (let j = 0; j < nY; j++) {
    for (let i = 0; i < segA; i++) {
      const a = j * segA + i, b = j * segA + ((i + 1) % segA), c = (j + 1) * segA + i, d = (j + 1) * segA + ((i + 1) % segA);
      if (corte) {
        const cx = (pos[a * 3] + pos[d * 3]) / 2, cy = (pos[a * 3 + 1] + pos[d * 3 + 1]) / 2, cz = (pos[a * 3 + 2] + pos[d * 3 + 2]) / 2;
        if (corte(cx, cy, cz)) continue;
      }
      idx.push(a, c, b, b, c, d);
    }
  }
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute(pos, 3));
  if (sulco) g.setAttribute('sulco', new Float32BufferAttribute(sulco, 1));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

/** Sólido de revolução com arestas vivas: cada trecho do perfil vira uma faixa com normais próprias.
 *  perfil: [[r, y], ...] percorrido por fora, de baixo para cima. */
function torno(perfil, seg = 128) {
  const pos = [], nor = [], idx = [];
  for (let s = 0; s < perfil.length - 1; s++) {
    const [r0, y0] = perfil[s], [r1, y1] = perfil[s + 1];
    const dr = r1 - r0, dy = y1 - y0, L = Math.hypot(dr, dy) || 1;
    const nr = dy / L, ny = -dr / L;
    const base = pos.length / 3;
    for (let i = 0; i <= seg; i++) {
      const a = (i / seg) * TAU, c = Math.cos(a), sn = Math.sin(a);
      pos.push(r0 * c, y0, r0 * sn, r1 * c, y1, r1 * sn);
      nor.push(nr * c, ny, nr * sn, nr * c, ny, nr * sn);
    }
    for (let i = 0; i < seg; i++) {
      const a = base + i * 2, b = a + 1, c = a + 2, d = a + 3;
      idx.push(a, b, c, c, b, d);
    }
  }
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new Float32BufferAttribute(nor, 3));
  g.setIndex(idx);
  return g;
}

// vértices do sextavado (S entre faces), no plano XZ
function sextavado(S) {
  const R = S / Math.sqrt(3);
  const p = [];
  for (let k = 0; k < 6; k++) {
    const a = (k / 6) * TAU + Math.PI / 6;
    p.push([R * Math.cos(a), R * Math.sin(a)]);
  }
  return p;
}

// triângulos soltos (normais chapadas), orientados para "dir"
function soltos(tris) {
  const pos = [];
  for (const [a, b, c, dir] of tris) {
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2];
    const vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    if (nx * dir[0] + ny * dir[1] + nz * dir[2] < 0) pos.push(...a, ...c, ...b);
    else pos.push(...a, ...b, ...c);
  }
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute(pos, 3));
  g.computeVertexNormals();
  return g;
}

/** Face plana em y, círculo de raio r com furo sextavado S, virada para cima. */
function tampaComSextavado(r, S, y, seg = 96) {
  const sh = new Shape();
  sh.absarc(0, 0, r, 0, TAU, false);
  const furo = new Shape();
  const hx = sextavado(S);
  // Shape está em XY; depois de rotateX(-90°) o ponto (x, y) vai para (x, 0, -y)
  furo.moveTo(hx[0][0], -hx[0][1]);
  for (let k = 5; k >= 1; k--) furo.lineTo(hx[k][0], -hx[k][1]);
  sh.holes.push(furo);
  const g = new ShapeGeometry(sh, seg);
  g.rotateX(-Math.PI / 2);
  g.translate(0, y, 0);
  return g;
}

/** Disco plano em y (para cima ou para baixo). */
function disco(r, y, cima = true, seg = 96) {
  const sh = new Shape();
  sh.absarc(0, 0, r, 0, TAU, false);
  const g = new ShapeGeometry(sh, seg);
  g.rotateX(cima ? -Math.PI / 2 : Math.PI / 2);
  g.translate(0, y, 0);
  return g;
}

/** Furo sextavado: paredes + fundo cônico de broca (118°). */
function cavidade(S, yTopo, T) {
  const hx = sextavado(S);
  const yF = yTopo - T, ponta = (S / 2) * 0.6;
  const tris = [];
  for (let k = 0; k < 6; k++) {
    const [x0, z0] = hx[k], [x1, z1] = hx[(k + 1) % 6];
    const dentro = [-(x0 + x1) / 2, 0, -(z0 + z1) / 2];
    const A = [x0, yTopo, z0], B = [x1, yTopo, z1], C = [x1, yF, z1], D = [x0, yF, z0];
    tris.push([A, B, C, dentro], [A, C, D, dentro]);
    tris.push([D, C, [0, yF - ponta, 0], [0, 1, 0]]);
  }
  return soltos(tris);
}

/** Cabeça sextavada com chanfro de 30° em cima e embaixo (S entre faces, altura M). */
function cabecaSextavada(S, y0, M, nA = 240, nY = 40) {
  const pos = new Float32Array((nY + 1) * nA * 3);
  const rTopo = S * 0.475, rBase = S * 0.492, k = 1 / Math.tan(Math.PI / 6);
  let o = 0;
  for (let j = 0; j <= nY; j++) {
    const t = j / nY;
    const tt = 0.5 - 0.5 * Math.cos(Math.PI * t); // mais linhas perto das bordas
    const y = y0 + M * tt;
    for (let i = 0; i < nA; i++) {
      const a = (i / nA) * TAU;
      let phi = ((a + Math.PI / 6) % (Math.PI / 3)) - Math.PI / 6;
      const rHex = S / 2 / Math.cos(phi);
      const r = Math.min(rHex, rTopo + (y0 + M - y) * k, rBase + (y - y0) * k * 1.6);
      pos[o++] = r * Math.cos(a);
      pos[o++] = y;
      pos[o++] = r * Math.sin(a);
    }
  }
  const idx = [];
  for (let j = 0; j < nY; j++) for (let i = 0; i < nA; i++) {
    const a = j * nA + i, b = j * nA + ((i + 1) % nA), c = (j + 1) * nA + i, d = (j + 1) * nA + ((i + 1) % nA);
    idx.push(a, c, b, b, c, d);
  }
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return { lado: g, topo: disco(rTopo, y0 + M, true), rTopo };
}

// Mantém cada parte como malha própria (indexada, leve). Fundir tudo sem índice multiplicava os
// vértices por 6 e a placa de vídeo travava ~1 s a cada troca de peça.
function juntar(lista) {
  return lista.map((g) => {
    for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal' && k !== 'sulco') g.deleteAttribute(k);
    if (!g.attributes.normal) g.computeVertexNormals();
    return g;
  });
}

// ------------------------------------------------------------------ peças
function bujao906(dm) {
  const rs = lerRosca(dm.rosca, dm.tipoRosca);
  const L = dm.L, S = medida(dm.S), T = Math.min(dm.T, L * 0.8);
  const rTopo = rs.d / 2, rPonta = rTopo - L / 32;
  const prof = rs.passo * rs.perfil * 0.62;
  const ch = Math.min(prof * 1.2, L * 0.08);
  const rT = rTopo - prof - ch * 0.35;
  const corpo = juntar([
    rosca({ y0: 0, y1: L, rMaj0: rPonta, rMaj1: rTopo, passo: rs.passo, prof, chPonta: true, chTopo: true, ch }),
    tampaComSextavado(rT, S, L),
    cavidade(S, L, T),
    disco(rPonta - prof - ch * 0.35, 0, false),
  ]);
  return { corpo };
}

function bujao908(dm) {
  const rs = lerRosca(dm.rosca, dm.tipoRosca);
  const D = dm.D, C = dm.C, L = dm.L, S = medida(dm.S), T = Math.min(dm.T, C + L * 0.7);
  const r = rs.d / 2, prof = rs.passo * rs.perfil * 0.62, ch = prof * 1.2;
  const rMin = r - prof, rPesc = rMin - ch * 0.35, hPesc = Math.max(rs.passo * 0.7, 0.6);
  const yRosca = L - hPesc, yC = L, yTopo = L + C, chC = Math.min(C * 0.22, 0.8), R = D / 2;
  const corpo = juntar([
    rosca({ y0: 0, y1: yRosca, rMaj0: r, rMaj1: r, passo: rs.passo, prof, chPonta: true, chTopo: true, ch }),
    disco(rPesc, 0, false),
    torno([[rPesc, yRosca], [rPesc, yC], [R - chC * 0.6, yC], [R, yC + chC * 0.6], [R, yTopo - chC], [R - chC, yTopo]]),
    tampaComSextavado(R - chC, S, yTopo),
    cavidade(S, yTopo, T),
  ]);
  return { corpo };
}

function bujao910(dm) {
  const rs = lerRosca(dm.rosca, dm.tipoRosca);
  const D = dm.D, M = dm.M, L = dm.L, C = dm.C, S = medida(dm.S);
  const r = rs.d / 2, prof = rs.passo * rs.perfil * 0.62, ch = prof * 1.2;
  const rMin = r - prof, rPesc = rMin - ch * 0.35, hPesc = Math.max(rs.passo * 0.7, 0.6);
  const yRosca = L - hPesc, yC = L, yCab = L + C, R = D / 2, chC = Math.min(C * 0.22, 0.8);
  const cab = cabecaSextavada(S, yCab, M);
  const corpo = juntar([
    rosca({ y0: 0, y1: yRosca, rMaj0: r, rMaj1: r, passo: rs.passo, prof, chPonta: true, chTopo: true, ch }),
    disco(rPesc, 0, false),
    torno([[rPesc, yRosca], [rPesc, yC], [R - chC * 0.6, yC], [R, yC + chC * 0.6], [R, yCab - chC], [R - chC, yCab], [S * 0.45, yCab]]),
    cab.lado,
    cab.topo,
  ]);
  return { corpo };
}

function posicionador(dm) {
  const rs = lerRosca(dm.rosca, 'metrica');
  const L = dm.L, D2 = dm.D2, l1 = dm.l1;
  const r = rs.d / 2, prof = rs.passo * rs.perfil * 0.7, ch = prof * 1.2;
  const rMin = r - prof, rB = D2 / 2;
  const w = Math.max(rs.d * 0.17, 0.5), sp = rs.d * 0.32; // fenda
  const corte = (x, y) => Math.abs(x) < w / 2 && y < sp;
  const rEnd = rMin - ch * 0.35;
  // tampa de trás em duas metades (a fenda atravessa)
  const metade = (lado) => {
    const sh = new Shape();
    const a0 = Math.acos(lim(w / 2 / rEnd, 0, 1));
    const n = 40;
    for (let i = 0; i <= n; i++) {
      const a = -a0 + (2 * a0 * i) / n;
      const x = lado * rEnd * Math.cos(a), z = rEnd * Math.sin(a);
      i === 0 ? sh.moveTo(x, z) : sh.lineTo(x, z);
    }
    const g = new ShapeGeometry(sh);
    g.rotateX(Math.PI / 2);
    return g;
  };
  const zE = Math.sqrt(Math.max(0, (rMin + prof * 0.4) ** 2 - (w / 2) ** 2));
  const paredes = soltos([
    [[w / 2, 0, -zE], [w / 2, sp, -zE], [w / 2, sp, zE], [-1, 0, 0]], [[w / 2, 0, -zE], [w / 2, sp, zE], [w / 2, 0, zE], [-1, 0, 0]],
    [[-w / 2, 0, -zE], [-w / 2, sp, -zE], [-w / 2, sp, zE], [1, 0, 0]], [[-w / 2, 0, -zE], [-w / 2, sp, zE], [-w / 2, 0, zE], [1, 0, 0]],
    [[-w / 2, sp, -zE], [w / 2, sp, -zE], [w / 2, sp, zE], [0, -1, 0]], [[-w / 2, sp, -zE], [w / 2, sp, zE], [-w / 2, sp, zE], [0, -1, 0]],
  ]);
  const rFuro = rB * 0.86;
  const corpo = juntar([
    rosca({ y0: 0, y1: L, rMaj0: r, rMaj1: r, passo: rs.passo, prof, chPonta: true, chTopo: true, ch, corte }),
    metade(1), metade(-1), paredes,
    torno([[rEnd, L], [rFuro + (rEnd - rFuro) * 0.35, L + Math.min(l1 * 0.25, 0.3)], [rFuro, L - rB * 0.05]]),
  ]);
  const esfera = new SphereGeometry(rB, 64, 40);
  esfera.translate(0, L + l1 - rB, 0);
  return { corpo, esfera };
}

/** Rosca interna de um furo passante: normais para o eixo; nas pontas abre até um círculo (entrada do chanfro). */
function roscaInterna({ y0, y1, rMin, passo, prof, segA = 96, porPasso = 12 }) {
  const len = y1 - y0;
  const nY = lim(Math.ceil((len / passo) * porPasso), 12, 320);
  const rFim = rMin + prof * 1.02;
  const pos = new Float32Array((nY + 1) * segA * 3);
  const sulco = new Float32Array((nY + 1) * segA);
  let o = 0, os = 0;
  for (let j = 0; j <= nY; j++) {
    const y = y0 + (len * j) / nY;
    for (let i = 0; i < segA; i++) {
      const a = (i / segA) * TAU;
      let f = y / passo - a / TAU;
      f -= Math.floor(f);
      const tri = 1 - Math.abs(2 * f - 1);
      let k = lim((tri - 0.1) / 0.78, 0, 1);
      k = suave(k) * 0.45 + k * 0.55;
      sulco[os++] = 0.34 + 0.66 * (1 - k);
      let r = rMin + prof * (1 - k);
      r = Math.max(r, rFim - (y - y0), rFim - (y1 - y));
      pos[o++] = r * Math.cos(a);
      pos[o++] = y;
      pos[o++] = r * Math.sin(a);
    }
  }
  const idx = [];
  for (let j = 0; j < nY; j++) for (let i = 0; i < segA; i++) {
    const a = j * segA + i, b = j * segA + ((i + 1) % segA), c = (j + 1) * segA + i, d = (j + 1) * segA + ((i + 1) % segA);
    idx.push(a, b, c, b, d, c);
  }
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute(pos, 3));
  g.setAttribute('sulco', new Float32BufferAttribute(sulco, 1));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

/** Bucha roscada: rosca por fora e por dentro, furo passante. Reta (ponta lisa em cima) ou com colar. */
function bucha(dm) {
  const de = dm.de || 14, pe = dm.pe || 1.75, di = dm.di || 8, pi = dm.pi || 1.25, L = dm.L || 28;
  const rMaj = de / 2, prof = pe * 0.42, chE = prof * 1.1, rMin = rMaj - prof, rFimE = rMin - chE * 0.35;
  const profI = pi * 0.54, rMinI = di / 2 - profI, rFimI = rMinI + profI * 1.02;
  const cBoca = Math.max(pi * 0.45, 0.5), rBoca = rFimI + cBoca * 0.75;

  const partes = [];
  let yRosca, yTopo;
  if (dm.colar) {
    const C = dm.C || L * 0.14, D = dm.D || de * 1.3, hPesc = pe * 1.15;
    yRosca = L - hPesc; yTopo = L + C;
    const R = D / 2, ch = C * 0.13, rPesc = rMaj - prof * 0.12;
    partes.push(torno([
      [rFimE, yRosca], [rPesc, yRosca + prof * 0.9], [rPesc, L], [R - ch * 0.7, L], [R, L + ch * 0.7],
      [R, yTopo - ch], [R - ch, yTopo], [rBoca, yTopo], [rFimI, yTopo - cBoca],
    ]));
  } else {
    const hBanda = pe * 1.7, chB = pe * 0.34, rBanda = rMaj - prof * 0.1;
    yRosca = L - hBanda; yTopo = L;
    partes.push(torno([
      [rFimE, yRosca], [rBanda, yRosca + prof * 0.9], [rBanda, L - chB], [rBanda - chB, L], [rBoca, L], [rFimI, L - cBoca],
    ]));
  }
  partes.push(rosca({ y0: 0, y1: yRosca, rMaj0: rMaj, rMaj1: rMaj, passo: pe, prof, ch: chE, chPonta: true, chTopo: true, redondo: true }));
  partes.push(roscaInterna({ y0: cBoca, y1: yTopo - cBoca, rMin: rMinI, passo: pi, prof: profI }));
  partes.push(torno([[rFimI, cBoca], [rBoca, 0], [rFimE, 0]]));
  return { corpo: juntar(partes) };
}

// Mola de compressão com as pontas fechadas (espiras encostadas)
class Helice extends Curve {
  constructor(R, voltas, fio, passo) {
    super();
    this.R = R; this.v = voltas; this.fio = fio; this.passo = passo;
    // altura acumulada por volta (pontas fechadas = passo do fio)
    const n = 2000, h = new Float32Array(n + 1);
    for (let i = 1; i <= n; i++) {
      const c = (i / n) * voltas;
      const borda = Math.min(c, voltas - c);
      const p = fio + (passo - fio) * suave(lim(borda - 0.6, 0, 1));
      h[i] = h[i - 1] + (p * voltas) / n;
    }
    this.h = h; this.n = n;
  }
  getPoint(t, alvo = new Vector3()) {
    const f = lim(t, 0, 1) * this.n, i = Math.min(this.n - 1, Math.floor(f));
    const y = this.h[i] + (this.h[i + 1] - this.h[i]) * (f - i);
    const a = t * this.v * TAU;
    return alvo.set(this.R * Math.cos(a), y, this.R * Math.sin(a));
  }
}

function mola(dm) {
  const fio = dm.fio || 2, De = dm.De || 18, voltas = dm.voltas || 9, Lo = dm.Lo || 46;
  const R = (De - fio) / 2;
  const passoLivre = (Lo - fio * 2.4) / (voltas - 1.6);
  const passoComp = Math.max(fio * 1.12, passoLivre * 0.5);
  const seg = Math.round(voltas * 72);
  const rad = 14;
  const livre = tampar(new TubeGeometry(new Helice(R, voltas, fio, passoLivre), seg, fio / 2, rad, false), seg, rad);
  const comp = tampar(new TubeGeometry(new Helice(R, voltas, fio, passoComp), seg, fio / 2, rad, false), seg, rad);
  livre.morphAttributes.position = [comp.attributes.position];
  livre.morphAttributes.normal = [comp.attributes.normal];
  return { corpo: livre, mola: true };
}

// fecha as duas pontas do tubo (o arame cortado) com um leque; mesma topologia nas duas posições da mola
function tampar(tubo, seg, rad) {
  const P = tubo.attributes.position.array, N = tubo.attributes.normal.array, I = Array.from(tubo.index.array);
  const pos = Array.from(P), nor = Array.from(N);
  for (const [anel, sinal] of [[0, -1], [seg, 1]]) {
    const ini = anel * (rad + 1);
    let cx = 0, cy = 0, cz = 0;
    for (let i = 0; i < rad; i++) { cx += P[(ini + i) * 3]; cy += P[(ini + i) * 3 + 1]; cz += P[(ini + i) * 3 + 2]; }
    cx /= rad; cy /= rad; cz /= rad;
    // direção do arame na ponta
    const viz = (anel === 0 ? rad + 1 : -(rad + 1));
    let tx = cx - P[(ini + viz) * 3], ty = cy - P[(ini + viz) * 3 + 1], tz = cz - P[(ini + viz) * 3 + 2];
    const tl = Math.hypot(tx, ty, tz) || 1; tx /= tl; ty /= tl; tz /= tl;
    const centro = pos.length / 3;
    pos.push(cx, cy, cz); nor.push(tx, ty, tz);
    const base = pos.length / 3;
    for (let i = 0; i <= rad; i++) {
      pos.push(P[(ini + i) * 3], P[(ini + i) * 3 + 1], P[(ini + i) * 3 + 2]);
      nor.push(tx, ty, tz);
    }
    for (let i = 0; i < rad; i++) {
      if (sinal > 0) I.push(centro, base + i, base + i + 1);
      else I.push(centro, base + i + 1, base + i);
    }
  }
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new Float32BufferAttribute(nor, 3));
  g.setIndex(I);
  return g;
}

export function montarPeca(tipo, dm) {
  const f = { 906: bujao906, 908: bujao908, 910: bujao910, posicionador, mola, bucha, 'bucha-colar': (d) => bucha({ ...d, colar: true }) }[tipo];
  return f(dm);
}

// ------------------------------------------------------------------ estúdio
function ambiente(renderer) {
  const sala = new Scene();
  const fundo = new Mesh(new SphereGeometry(20, 32, 16), new MeshBasicMaterial({ color: 0x5c6066, side: BackSide }));
  sala.add(fundo);
  const painel = (w, h, cor, int, x, y, z) => {
    const m = new Mesh(new PlaneGeometry(w, h), new MeshBasicMaterial({ color: new Color(cor).multiplyScalar(int) }));
    m.position.set(x, y, z);
    m.lookAt(0, 0, 0);
    sala.add(m);
  };
  painel(10, 7, 0xffffff, 5.0, -7, 6, 6);    // softbox principal, alto à esquerda
  painel(12, 6, 0xffffff, 3.2, 0, 8, -7);    // teto atrás: brilho nas faces de cima
  painel(1.6, 16, 0xffffff, 3.4, -8, 0, 1);  // fita vertical à esquerda: risco de luz na rosca
  painel(1.6, 16, 0xffffff, 2.6, 8, 0, -1);  // fita vertical à direita
  painel(4, 12, 0xffffff, 1.6, 6, 1, 7);     // rebatedor frontal à direita
  painel(14, 14, 0xe4e4e4, 1.1, 0, -10, 0);  // chão claro
  painel(8, 3, 0xffffff, 1.2, 0, -3, 9);     // frente baixa
  painel(16, 9, 0xffffff, 0.75, -2, 3, 11);
  painel(14, 7, 0xffffff, 1.5, 1, -7, 7);    // rebatedor baixo à frente: faces verticais inclinadas pelo ângulo de câmera  // frente difusa: faces planas viradas para a câmera não somem no preto
  const pm = new PMREMGenerator(renderer);
  const tex = pm.fromScene(sala, 0.035).texture;
  pm.dispose();
  return tex;
}

// Zincado amarelo (bicromatizado): fosco, oliva-dourado, com manchas rosadas e esverdeadas e um grão fino.
// As manchas saem de um ruído na posição da peça (em mm), mais esticado na volta do que na altura.
function materialZincado() {
  const m = new MeshPhysicalMaterial({ color: 0xffffff, metalness: 1, roughness: 0.37 });
  m.customProgramCacheKey = () => 'zincado-v2';
  m.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float sulco;\nvarying vec3 vPeca;\nvarying float vSulco;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvPeca = position;\nvSulco = sulco;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
varying vec3 vPeca;
varying float vSulco;
float zh(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float zn(vec3 x){ vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(zh(i), zh(i + vec3(1,0,0)), f.x), mix(zh(i + vec3(0,1,0)), zh(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(zh(i + vec3(0,0,1)), zh(i + vec3(1,0,1)), f.x), mix(zh(i + vec3(0,1,1)), zh(i + vec3(1,1,1)), f.x), f.y), f.z); }
float zf(vec3 p){ return 0.55 * zn(p) + 0.3 * zn(p * 2.1 + 3.7) + 0.15 * zn(p * 4.3 + 9.1); }
vec3 zl(vec3 c){ return pow(c, vec3(2.2)); }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
{
  vec3 q = vPeca * vec3(0.16, 0.42, 0.16);
  float a = zf(q + 11.0), b = zf(q * 1.3 + 41.0);
  vec3 oliva = zl(vec3(0.60, 0.54, 0.34)), ouro = zl(vec3(0.74, 0.64, 0.38)), rosa = zl(vec3(0.72, 0.55, 0.42)), verde = zl(vec3(0.54, 0.54, 0.32));
  vec3 cor = mix(oliva, ouro, smoothstep(0.32, 0.62, a));
  cor = mix(cor, rosa, smoothstep(0.54, 0.74, b) * 0.75);
  cor = mix(cor, verde, smoothstep(0.56, 0.76, 1.0 - b) * 0.6);
  cor *= 0.975 + 0.05 * zn(vPeca * 16.0);
  cor *= mix(1.0, 0.24, pow(clamp(vSulco, 0.0, 1.0), 1.4));
  diffuseColor.rgb = cor;
}`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
roughnessFactor = clamp(roughnessFactor + (zn(vPeca * 11.0) - 0.5) * 0.07, 0.05, 1.0);`);
  };
  return m;
}

const MATERIAIS = {
  aco: () => new MeshPhysicalMaterial({ color: 0x34363b, metalness: 1, roughness: 0.32, clearcoat: 0.55, clearcoatRoughness: 0.2 }),
  inox: () => new MeshPhysicalMaterial({ color: 0xc9ccd1, metalness: 1, roughness: 0.22 }),
  mola: () => new MeshPhysicalMaterial({ color: 0x3a3c41, metalness: 1, roughness: 0.28, clearcoat: 0.6, clearcoatRoughness: 0.15, side: DoubleSide }),
  zincado: () => materialZincado(),
  esfera: () => new MeshPhysicalMaterial({ color: 0xeef0f2, metalness: 1, roughness: 0.05 }),
};

export function criarVisor(canvas, op = {}) {
  const renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: !!op.foto, powerPreference: 'high-performance' });
  renderer.setPixelRatio(op.dpr || Math.min(window.devicePixelRatio || 1, 2));
  renderer.toneMapping = ACESFilmicToneMapping;
  renderer.toneMappingExposure = op.exposicao || 1.05;
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.setClearColor(0x000000, 0);

  const cena = new Scene();
  cena.environment = ambiente(renderer);
  const cam = new PerspectiveCamera(26, 1, 0.1, 100);
  cam.position.set(0, 0, 5.2);

  const pivo = new Group();      // giro do usuário
  cena.add(pivo);
  const mats = { corpo: MATERIAIS.aco(), esfera: MATERIAIS.esfera(), mola: MATERIAIS.mola() };
  let mat = 'aco', atual = null, entrando = 0, morph = 0, alvoMorph = 0;
  let yaw = op.yaw ?? -0.5, pitch = op.pitch ?? 0.42, vel = op.auto === false ? 0 : 0.0045, arrastando = false;
  let w = 0, h = 0, raf = 0, vivo = true, pausado = false;

  function medir() {
    const r = canvas.getBoundingClientRect();
    const nw = Math.max(1, Math.round(r.width)), nh = Math.max(1, Math.round(r.height));
    if (nw !== w || nh !== h) {
      w = nw; h = nh;
      renderer.setSize(w, h, false);
      cam.aspect = w / h;
      cam.updateProjectionMatrix();
    }
  }

  function materialDe(m) {
    if (m.userData.papel === 'esfera') return mats.esfera;
    return m.userData.papel === 'mola' && mat !== 'inox' ? mats.mola : mats.corpo;
  }
  function aplicarMaterial() {
    const novo = (MATERIAIS[mat] || MATERIAIS.aco)();
    mats.corpo.dispose();
    mats.corpo = novo;
    if (atual) atual.traverse((m) => { if (m.isMesh) m.material = materialDe(m); });
  }

  // peças já montadas ficam guardadas: voltar a uma peça reaproveita o que já está na placa de vídeo
  const guardadas = new Map();
  function montarGrupo(tipo, dm) {
    const p = montarPeca(tipo, dm);
    const g = new Group();
    for (const geo of Array.isArray(p.corpo) ? p.corpo : [p.corpo]) {
      const m = new Mesh(geo);
      m.userData.papel = p.mola ? 'mola' : 'corpo';
      if (p.mola) m.morphTargetInfluences = [morph];
      g.add(m);
    }
    if (p.esfera) {
      const e = new Mesh(p.esfera);
      e.userData.papel = 'esfera';
      g.add(e);
    }
    // centraliza e normaliza pelo raio da esfera envolvente (todas as medidas ocupam o mesmo quadro)
    const esf = new Box3().setFromObject(g).getBoundingSphere(new Sphere());
    g.children.forEach((m) => m.geometry.translate(-esf.center.x, -esf.center.y, -esf.center.z));
    g.userData.k = (op.escala || 1.12) / esf.radius;
    g.scale.setScalar(g.userData.k);
    return g;
  }

  function mostrar(tipo, dm, o = {}) {
    if (o.material && o.material !== mat) { mat = o.material; aplicarMaterial(); }
    const chave = tipo + JSON.stringify(dm);
    let g = guardadas.get(chave);
    if (g) guardadas.delete(chave);
    else g = montarGrupo(tipo, dm);
    guardadas.set(chave, g);
    while (guardadas.size > 10) {
      const [k0, g0] = guardadas.entries().next().value;
      guardadas.delete(k0);
      if (g0 === atual) { guardadas.set(k0, g0); continue; }
      g0.traverse((m) => { if (m.isMesh) m.geometry.dispose(); });
    }
    g.traverse((m) => { if (m.isMesh) m.material = materialDe(m); });
    if (atual && atual !== g) pivo.remove(atual);
    atual = g;
    if (!g.parent) pivo.add(g);
    entrando = o.instante ? 1 : 0;
    desenhar();
  }

  function desenhar() {
    medir();
    if (atual) {
      const e = suave(lim(entrando, 0, 1));
      atual.scale.setScalar(atual.userData.k * (0.86 + 0.14 * e));
      atual.rotation.y = (1 - e) * -0.9;
    }
    pivo.rotation.set(pitch, yaw, 0, 'XYZ');
    const mesh = atual && atual.children[0];
    if (mesh && mesh.morphTargetInfluences) mesh.morphTargetInfluences[0] = morph;
    renderer.render(cena, cam);
  }

  let ultimo = performance.now();
  function quadro(t) {
    if (!vivo) return;
    raf = requestAnimationFrame(quadro);
    const dt = Math.min(0.05, (t - ultimo) / 1000);
    ultimo = t;
    if (pausado) return;
    if (!arrastando) yaw += vel * dt * 60;
    if (entrando < 1) entrando = Math.min(1, entrando + dt * 2.2);
    morph += (alvoMorph - morph) * Math.min(1, dt * 8);
    desenhar();
  }

  if (op.arrastar !== false) {
    let x0 = 0, y0 = 0, ya = 0, pa = 0;
    canvas.style.touchAction = 'pan-y';
    canvas.addEventListener('pointerdown', (ev) => {
      arrastando = true; x0 = ev.clientX; y0 = ev.clientY; ya = yaw; pa = pitch;
      canvas.setPointerCapture(ev.pointerId);
    });
    canvas.addEventListener('pointermove', (ev) => {
      if (!arrastando) return;
      yaw = ya + (ev.clientX - x0) * 0.012;
      pitch = lim(pa + (ev.clientY - y0) * 0.006, -0.2, 1.1);
    });
    const solta = () => { arrastando = false; };
    canvas.addEventListener('pointerup', solta);
    canvas.addEventListener('pointercancel', solta);
  }

  const ro = new ResizeObserver(() => desenhar());
  ro.observe(canvas);
  if (!op.foto) raf = requestAnimationFrame(quadro);

  return {
    mostrar,
    material(m) { if (m !== mat) { mat = m; aplicarMaterial(); desenhar(); } },
    comprimir(k) { alvoMorph = lim(k, 0, 1); },
    girar(v) { vel = v; },
    angulo(y, p) { yaw = y; if (p != null) pitch = p; desenhar(); },
    foto(fw, fh) {
      renderer.setPixelRatio(1);
      renderer.setSize(fw, fh, false);
      cam.aspect = fw / fh; cam.updateProjectionMatrix();
      w = fw; h = fh;
      entrando = 1;
      if (atual) atual.scale.setScalar(atual.userData.k);
      pivo.rotation.set(pitch, yaw, 0, 'XYZ');
      const mesh = atual && atual.children[0];
      if (mesh && mesh.morphTargetInfluences) mesh.morphTargetInfluences[0] = alvoMorph;
      renderer.render(cena, cam);
      return canvas.toDataURL('image/png');
    },
    pausar() { pausado = true; },
    retomar() { pausado = false; ultimo = performance.now(); },
    destruir() { vivo = false; cancelAnimationFrame(raf); ro.disconnect(); renderer.dispose(); },
  };
}
