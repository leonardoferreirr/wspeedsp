/* W Speed: lista de orçamento (localStorage) -> WhatsApp pela ponte /obrigado, tabelas de medidas,
   aço x inox, e o 3D das peças (assets/js/pecas3d.js) só depois da primeira interação. */
(function () {
  'use strict';
  var d = document, raiz = d.documentElement, corpo = d.body;
  var reduz = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, el) { return (el || d).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || d).querySelectorAll(s)); };
  var MAT = { aco: 'aço oxidado', inox: 'inox', zincado: 'aço zincado' };

  /* ---------------- revelar ao rolar */
  var revs = $$('.rev');
  if ('IntersectionObserver' in window) {
    var ioRev = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('vis'); ioRev.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    revs.forEach(function (el) { ioRev.observe(el); });
  } else revs.forEach(function (el) { el.classList.add('vis'); });

  /* ---------------- menu do celular */
  var btMenu = $('.bt-menu');
  if (btMenu) btMenu.addEventListener('click', function () {
    var on = corpo.classList.toggle('menu-aberto');
    btMenu.setAttribute('aria-expanded', on);
  });
  $$('.nav a').forEach(function (a) { a.addEventListener('click', function () { corpo.classList.remove('menu-aberto'); }); });
  $$('.nav .sub>button').forEach(function (b) {
    b.addEventListener('click', function () {
      var on = b.parentNode.classList.toggle('aberto');
      b.setAttribute('aria-expanded', on);
    });
  });

  /* ---------------- lista de orçamento */
  var CHAVE = 'ws_orcamento';
  var itens = [];
  try { itens = JSON.parse(localStorage.getItem(CHAVE)) || []; } catch (e) { itens = []; }
  var gaveta = $('.gaveta'), lista = $('.itens'), vazio = $('.vazio'), formOrc = $('#form-orc');

  function salvar() {
    try { localStorage.setItem(CHAVE, JSON.stringify(itens)); } catch (e) {}
    desenhar();
  }
  function total() { return itens.reduce(function (s, i) { return s + 1; }, 0); }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  var ICO = {
    menos: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M5 12h14"/></svg>',
    mais: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
    tira: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>'
  };

  function desenhar() {
    var n = total();
    $$('.bt-orc .n, .orcf .n').forEach(function (el) { el.textContent = n; });
    corpo.classList.toggle('tem-itens', n > 0);
    if (!lista) return;
    lista.innerHTML = itens.map(function (it, k) {
      return '<li class="item" data-k="' + k + '">' +
        (it.img ? '<img src="' + esc(it.img) + '" alt="" width="56" height="56" loading="lazy">' : '<span></span>') +
        '<div><b>' + esc(it.nome) + '</b><small>' + esc(it.detalhe) + (it.material ? ', ' + esc(MAT[it.material] || it.material) : '') + '</small>' +
        '<div class="qtd"><button type="button" data-q="-1" aria-label="Menos">' + ICO.menos + '</button>' +
        '<input type="number" min="1" inputmode="numeric" value="' + it.qtd + '" aria-label="Quantidade">' +
        '<button type="button" data-q="1" aria-label="Mais">' + ICO.mais + '</button></div></div>' +
        '<button type="button" class="tira" aria-label="Tirar da lista">' + ICO.tira + '</button></li>';
    }).join('');
    if (vazio) vazio.hidden = n > 0;
    if (formOrc) formOrc.hidden = n === 0;
    var base = $('.gaveta__base');
    if (base) base.hidden = n === 0;
  }

  if (lista) {
    lista.addEventListener('click', function (ev) {
      var li = ev.target.closest('.item'); if (!li) return;
      var it = itens[+li.dataset.k];
      var q = ev.target.closest('[data-q]');
      if (q) { it.qtd = Math.max(1, (parseInt(it.qtd, 10) || 1) + +q.dataset.q); salvar(); return; }
      if (ev.target.closest('.tira')) { itens.splice(+li.dataset.k, 1); salvar(); }
    });
    lista.addEventListener('change', function (ev) {
      if (ev.target.tagName !== 'INPUT') return;
      var li = ev.target.closest('.item');
      itens[+li.dataset.k].qtd = Math.max(1, parseInt(ev.target.value, 10) || 1);
      salvar();
    });
  }

  function abrir() { corpo.classList.add('orc-aberto'); corpo.classList.remove('menu-aberto'); if (gaveta) { gaveta.setAttribute('aria-hidden', 'false'); gaveta.inert = false; } var f = $('.gaveta__topo button'); if (f) f.focus({ preventScroll: true }); }
  function fechar() { corpo.classList.remove('orc-aberto'); if (gaveta) { gaveta.setAttribute('aria-hidden', 'true'); gaveta.inert = true; } }
  if (gaveta) gaveta.inert = true;
  $$('[data-abre-orc]').forEach(function (b) { b.addEventListener('click', function (ev) { ev.preventDefault(); abrir(); }); });
  $$('[data-fecha-orc]').forEach(function (b) { b.addEventListener('click', fechar); });
  d.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') { fechar(); corpo.classList.remove('menu-aberto'); } });

  var avisoEl = $('.aviso'), tAviso = 0;
  function aviso(txt) {
    if (!avisoEl) return;
    $('span', avisoEl).textContent = txt;
    avisoEl.classList.add('on');
    clearTimeout(tAviso);
    tAviso = setTimeout(function () { avisoEl.classList.remove('on'); }, 3600);
  }
  if (avisoEl) $('button', avisoEl).addEventListener('click', function () { avisoEl.classList.remove('on'); abrir(); });

  function adicionar(it, qtd) {
    qtd = Math.max(1, parseInt(qtd, 10) || 1);
    var id = it.id + '|' + (it.material || '');
    var ex = itens.filter(function (i) { return i.uid === id; })[0];
    if (ex) ex.qtd = (parseInt(ex.qtd, 10) || 1) + qtd;
    else itens.push({ uid: id, nome: it.nome, detalhe: it.detalhe, material: it.material || '', img: it.img || '', qtd: qtd });
    salvar();
    $$('.bt-orc .n, .orcf .n').forEach(function (el) { el.classList.remove('pulo'); void el.offsetWidth; el.classList.add('pulo'); });
    aviso(it.nome + ' ' + it.detalhe + ' na lista');
  }

  function mensagem(dados) {
    var linhas = ['Olá, W Speed! Quero um orçamento destas peças:', ''];
    itens.forEach(function (it, k) {
      linhas.push((k + 1) + ') ' + it.nome + ', ' + it.detalhe + (it.material ? ', ' + (MAT[it.material] || it.material) : '') + ': ' + it.qtd + ' un.');
    });
    linhas.push('');
    if (dados.nome) linhas.push('Nome: ' + dados.nome);
    if (dados.empresa) linhas.push('Empresa: ' + dados.empresa);
    if (dados.cidade) linhas.push('Cidade/UF: ' + dados.cidade);
    if (dados.obs) linhas.push('Obs.: ' + dados.obs);
    linhas.push('(lista montada pelo site)');
    return linhas.join('\n');
  }
  if (formOrc) formOrc.addEventListener('submit', function (ev) {
    ev.preventDefault();
    if (!itens.length) return;
    var f = new FormData(formOrc), dados = {};
    f.forEach(function (v, k) { dados[k] = String(v).trim(); });
    try { localStorage.setItem('ws_cliente', JSON.stringify({ nome: dados.nome, empresa: dados.empresa, cidade: dados.cidade })); } catch (e) {}
    try { sessionStorage.setItem('ws_msg', mensagem(dados)); } catch (e) {}
    location.href = '/obrigado?c=orcamento';
  });
  if (formOrc) {
    try {
      var cli = JSON.parse(localStorage.getItem('ws_cliente') || '{}');
      ['nome', 'empresa', 'cidade'].forEach(function (k) { if (cli[k] && formOrc.elements[k]) formOrc.elements[k].value = cli[k]; });
    } catch (e) {}
  }
  var limpar = $('[data-limpa]');
  if (limpar) limpar.addEventListener('click', function () { itens = []; salvar(); });
  desenhar();

  /* ---------------- 3D sob demanda */
  var palcos = $$('.palco[data-visor]');
  var mod3d = null, pedido3d = null;
  function aplicar(el) {
    var v = el._visor, e = el._estado; if (!v || !e) return;
    if (e.material) v.material(e.material);
    if (e.chave !== el._mostrado) { v.mostrar(e.tipo, e.dims, { material: e.material, instante: !el._mostrado }); el._mostrado = e.chave; }
  }
  function estado(el, novo) {
    el._estado = Object.assign({}, el._estado || JSON.parse(el.dataset.visor), novo);
    el._estado.chave = el._estado.tipo + JSON.stringify(el._estado.dims);
    var img = $('img', el);
    if (img && novo && (novo.tipo || novo.material)) {
      var src = (el.dataset.poster || '').replace('{tipo}', el._estado.tipo).replace('{mat}', el._estado.material || 'aco');
      if (src && img.getAttribute('src') !== src) { img.src = src; img.removeAttribute('srcset'); }
    }
    aplicar(el);
  }
  function iniciar3D() {
    if (pedido3d || !palcos.length) return pedido3d;
    pedido3d = import(corpo.dataset.pecas3d).then(function (m) {
      mod3d = m;
      var celular = innerWidth < 760;
      var io = 'IntersectionObserver' in window ? new IntersectionObserver(function (es) {
        es.forEach(function (e) { var v = e.target._visor; if (v) e.isIntersecting ? v.retomar() : v.pausar(); });
      }) : null;
      palcos.forEach(function (el) {
        if (!el._estado) estado(el);
        var cfg = el._estado;
        var cv = d.createElement('canvas');
        cv.setAttribute('aria-hidden', 'true');
        el.appendChild(cv);
        try {
          el._visor = m.criarVisor(cv, { yaw: cfg.yaw, pitch: cfg.pitch, auto: !reduz, dpr: Math.min(window.devicePixelRatio || 1, celular ? 1.6 : 2) });
        } catch (e) { cv.remove(); return; }
        aplicar(el);
        requestAnimationFrame(function () { requestAnimationFrame(function () { el.classList.add('vivo'); }); });
        cv.addEventListener('pointerdown', function () { el.classList.add('girou'); el.dispatchEvent(new CustomEvent('girou')); }, { once: true });
        if (io) io.observe(el);
      });
      d.dispatchEvent(new CustomEvent('pecas3d'));
    }).catch(function () {});
    return pedido3d;
  }
  // na inicial roda o slideshow: lá o 3D só carrega quando a pessoa escolhe uma peça
  if (palcos.length && !$('.palco.rodando')) {
    var evs = ['pointerdown', 'touchstart', 'keydown', 'wheel', 'scroll', 'mousemove'];
    var gatilho = function () { evs.forEach(function (e) { removeEventListener(e, gatilho, true); }); iniciar3D(); };
    evs.forEach(function (e) { addEventListener(e, gatilho, { capture: true, passive: true }); });
  }

  /* ---------------- material (aço x inox) */
  $$('.material').forEach(function (grupo) {
    grupo.addEventListener('click', function (ev) {
      var b = ev.target.closest('button[data-mat]'); if (!b) return;
      var alvo = grupo.dataset.alvo ? $(grupo.dataset.alvo) : null;
      $$('button', grupo).forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
      corpo.dataset.material = b.dataset.mat;
      if (alvo) estado(alvo, { material: b.dataset.mat });
      var selMola = $('form[data-sob-medida="mola"] select[name="material"]');
      if (selMola) selMola.value = b.dataset.mat === 'inox' ? 'inox' : 'aço mola';
      var selBucha = $('form[data-sob-medida="bucha"] select[name="material"]');
      if (selBucha) selBucha.value = b.dataset.mat === 'latao' ? 'latão' : 'aço';
      var e = $('.escolha'); if (e) atualizarEscolha();
    });
  });
  function materialAtual() { return corpo.dataset.material || 'aco'; }

  /* ---------------- herói: slideshow das peças; escolher uma para o slideshow e abre o 3D */
  var heroi = $('.heroi .palco');
  var chips = $$('.heroi [data-peca]');
  if (heroi && chips.length) {
    var dados = JSON.parse(heroi.dataset.pecas);
    var legenda = $('.heroi__legenda');
    var grupoMat = $('.heroi .material');
    var areaHeroi = $('.heroi__v');
    var atual = 0;
    var marcar = function (i) {
      atual = i;
      chips.forEach(function (c, k) { c.setAttribute('aria-pressed', k === i); });
      var p = dados[i];
      if (p.sombra) heroi.style.setProperty('--sombra', p.sombra);
      if (grupoMat) grupoMat.classList.toggle('oculto', !!p.material);
      if (legenda) legenda.innerHTML = p.legenda + ' <a href="' + p.url + '">' + (p.verbo || 'Ver medidas') + '</a>';
    };
    var mostrarPeca = function (i) {
      marcar(i);
      var p = dados[i];
      estado(heroi, { tipo: p.tipo, dims: p.dims, material: p.material || materialAtual(), yaw: p.yaw, pitch: p.pitch });
      if (heroi._visor && p.pitch != null) heroi._visor.angulo(p.yaw, p.pitch);
    };
    chips.forEach(function (c, k) { c.addEventListener('click', function () { mostrarPeca(k); iniciar3D(); }); });

    var PASSO = 1400, roda = !reduz, tRoda = 0, naTela = true, sobre = false, noAr = 0, largSlide = 800;
    var fotos = [$('img', heroi)];
    var urlSlide = function (p) { return '/assets/img/pecas/' + p.tipo + '-' + (p.material || 'aco') + '-' + largSlide + '.webp'; };
    var proximo = function () {
      if (!roda) return;
      if (d.hidden || !naTela || sobre) { tRoda = setTimeout(proximo, 300); return; }
      var i = (atual + 1) % dados.length;
      var pre = new Image();
      pre.src = urlSlide(dados[i]);
      // só troca depois de decodificada, para o slide não piscar em conexão lenta
      (pre.decode ? pre.decode() : Promise.resolve()).catch(function () {}).then(function () {
        if (!roda) return;
        var entra = fotos[1 - noAr];
        entra.removeAttribute('srcset');
        entra.src = pre.src;
        entra.classList.add('no-ar');
        fotos[noAr].classList.remove('no-ar');
        noAr = 1 - noAr;
        marcar(i);
        tRoda = setTimeout(proximo, PASSO);
      });
    };
    var pararSlides = function () {
      roda = false;
      clearTimeout(tRoda);
      if (fotos[1]) {
        if (noAr === 1) { fotos[0].removeAttribute('srcset'); fotos[0].src = fotos[1].src; }
        fotos[1].remove();
      }
      fotos[0].classList.remove('no-ar');
      heroi.classList.remove('rodando');
      if (legenda) legenda.setAttribute('aria-live', 'polite');
    };
    var comecarSlides = function () {
      if (!roda) return;
      largSlide = heroi.offsetWidth * (window.devicePixelRatio || 1) > 480 ? 800 : 480;
      var extra = d.createElement('img');
      extra.alt = ''; extra.decoding = 'async';
      heroi.insertBefore(extra, fotos[0].nextSibling);
      fotos.push(extra);
      tRoda = setTimeout(proximo, PASSO);
    };
    if (roda) {
      // captura: para o slideshow antes de o clique chegar no botão da peça
      areaHeroi.addEventListener('click', function (ev) {
        if (!roda) return;
        pararSlides();
        if (ev.target.closest('a')) return;
        mostrarPeca(atual);
        iniciar3D();
      }, true);
      areaHeroi.addEventListener('pointerenter', function (ev) { if (ev.pointerType === 'mouse') sobre = true; });
      areaHeroi.addEventListener('pointerleave', function () { sobre = false; });
      if ('IntersectionObserver' in window) new IntersectionObserver(function (es) { naTela = es[0].isIntersecting; }).observe(heroi);
      if (d.readyState === 'complete') comecarSlides(); else addEventListener('load', comecarSlides, { once: true });
    } else {
      pararSlides();
    }
  }

  /* ---------------- modelos da peça (bucha, mola) */
  var botoesVar = $$('[data-variante]');
  var selModelo = $('form[data-sob-medida] select[name="modelo"]');
  var selMaterial = $('form[data-sob-medida] select[name="material"]');
  function trocarVariante(b) {
    var alvo = $(b.closest('[data-alvo]').dataset.alvo), cfg = JSON.parse(b.dataset.variante);
    botoesVar.forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
    if (cfg.sombra) alvo.style.setProperty('--sombra', cfg.sombra);
    var novo = { tipo: cfg.tipo, dims: cfg.dims };
    if (cfg.material) novo.material = cfg.material;
    estado(alvo, novo);
    if (alvo._visor && cfg.pitch != null) alvo._visor.angulo(cfg.yaw, cfg.pitch);
    iniciar3D();
    if (selModelo) selModelo.value = cfg.modelo;
    if (selMaterial && cfg.matForm) selMaterial.value = cfg.matForm;
  }
  botoesVar.forEach(function (b) { b.addEventListener('click', function () { trocarVariante(b); }); });
  if (selModelo) selModelo.addEventListener('change', function () {
    botoesVar.forEach(function (b) { if (JSON.parse(b.dataset.variante).modelo === selModelo.value) trocarVariante(b); });
  });

  /* na bucha, trocar o material no formulário também troca a peça */
  var selBuchaMat = $('form[data-sob-medida="bucha"] select[name="material"]');
  if (selBuchaMat) selBuchaMat.addEventListener('change', function () {
    var b = $('.material button[data-mat="' + (selBuchaMat.value === 'latão' ? 'latao' : 'aco') + '"]');
    if (b) b.click();
  });

  /* ---------------- aço x inox lado a lado */
  $$('.lado').forEach(function (el) {
    var inp = $('input', el);
    var pos = function () { el.style.setProperty('--x', inp.value + '%'); };
    inp.addEventListener('input', pos);
    pos();
  });

  /* ---------------- no celular, o botão flutuante sai da frente da coluna do + */
  var tabs = $$('.tabela');
  if (tabs.length && 'IntersectionObserver' in window) {
    var vistas = new Set();
    var ioTab = new IntersectionObserver(function (es) {
      es.forEach(function (e) { e.isIntersecting ? vistas.add(e.target) : vistas.delete(e.target); });
      corpo.classList.toggle('na-tabela', vistas.size > 0);
    }, { rootMargin: '-20% 0px -10% 0px' });
    tabs.forEach(function (t) { ioTab.observe(t); });
  }

  /* ---------------- página de produto: tabelas, escolha, adicionar */
  var abas = $$('.abas [role="tab"]');
  abas.forEach(function (a) {
    a.addEventListener('click', function () {
      abas.forEach(function (x) { x.setAttribute('aria-selected', x === a); });
      $$('.tabela').forEach(function (t) { t.hidden = t.id !== a.getAttribute('aria-controls'); });
      var t = $('#' + a.getAttribute('aria-controls'));
      var linha = $('tr[data-padrao]', t) || $('tbody tr', t);
      if (linha) selecionar(linha, true);
    });
  });
  var selecionada = $('tbody tr[aria-selected="true"]');
  var palcoProd = $('.prod .palco');
  function itemDaLinha(tr) {
    var tab = tr.closest('.tabela');
    return {
      id: tab.dataset.produto + '|' + tab.dataset.rosca + '|' + tr.dataset.rotulo,
      nome: tab.dataset.nome,
      detalhe: tr.dataset.detalhe,
      material: materialAtual(),
      img: tab.dataset.img.replace('{mat}', materialAtual())
    };
  }
  function atualizarEscolha() {
    var e = $('.escolha'); if (!e || !selecionada) return;
    $('.escolha__nome', e).innerHTML = esc(selecionada.closest('.tabela').dataset.nome) + ' <small>' + esc(selecionada.dataset.detalhe) + ', ' + MAT[materialAtual()] + '</small>';
    $('.escolha__dims', e).innerHTML = selecionada.dataset.medidas;
  }
  function selecionar(tr, semRolar) {
    if (selecionada) selecionada.setAttribute('aria-selected', 'false');
    selecionada = tr;
    tr.setAttribute('aria-selected', 'true');
    atualizarEscolha();
    if (palcoProd) {
      var dm = JSON.parse(tr.dataset.dims);
      estado(palcoProd, { dims: dm });
      iniciar3D();
      if (!semRolar && innerWidth < 900) {
        var r = palcoProd.getBoundingClientRect();
        if (r.bottom < 0 || r.top > innerHeight) { /* fica onde está: a escolha mostra a medida */ }
      }
    }
  }
  $$('.tabela tbody').forEach(function (tb) {
    tb.addEventListener('click', function (ev) {
      var tr = ev.target.closest('tr'); if (!tr) return;
      var b = ev.target.closest('td.add button');
      if (b) {
        adicionar(itemDaLinha(tr), 1);
        b.classList.add('ok');
        setTimeout(function () { b.classList.remove('ok'); }, 900);
        return;
      }
      selecionar(tr);
    });
    tb.addEventListener('keydown', function (ev) {
      if ((ev.key === 'Enter' || ev.key === ' ') && ev.target.tagName === 'TR') { ev.preventDefault(); selecionar(ev.target); }
    });
  });
  var qtdEsc = $('.escolha .qtd input');
  $$('.escolha .qtd button').forEach(function (b) {
    b.addEventListener('click', function () { qtdEsc.value = Math.max(1, (parseInt(qtdEsc.value, 10) || 1) + +b.dataset.q); });
  });
  var addEsc = $('.escolha [data-adiciona]');
  if (addEsc) addEsc.addEventListener('click', function () { if (selecionada) { adicionar(itemDaLinha(selecionada), qtdEsc.value); qtdEsc.value = 1; } });
  atualizarEscolha();

  /* ---------------- formulários de sob medida (mola, usinagem) */
  $$('form[data-sob-medida]').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var dd = new FormData(f), partes = [], qtd = 1, mat = '';
      $$('[data-rot]', f).forEach(function (campo) {
        var v = String(dd.get(campo.name) || '').trim();
        if (!v) return;
        if (campo.name === 'qtd') { qtd = v; return; }
        if (campo.name === 'material') { mat = v; return; }
        partes.push(campo.dataset.rot + (campo.dataset.un ? ' ' + v + ' ' + campo.dataset.un : ': ' + v));
      });
      adicionar({ id: f.dataset.sobMedida + '|' + partes.join(';'), nome: f.dataset.nome, detalhe: partes.join(', ') || 'sob medida', material: mat, img: f.dataset.img || '' }, qtd);
      f.reset();
      abrir();
    });
  });
})();
