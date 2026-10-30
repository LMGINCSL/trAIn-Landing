const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5ydXpqdHFld2pha2Z3c2hmYWd6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg5MjAyMzcsImV4cCI6MjA5NDQ5NjIzN30.GC0IRyXF1QppjbvQJNoYhe_FbWIAa6mjOZQkplrEbfM';
const isEn = document.documentElement.lang === 'en';

(function() {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isMobile = window.matchMedia('(max-width: 767px)').matches;
  gsap.registerPlugin(ScrollTrigger);
  // En móvil, ignorar el resize de la barra de direcciones evita que ScrollTrigger
  // recalcule y provoque saltos/contenido en blanco al hacer scroll.
  ScrollTrigger.config({ ignoreMobileResize: true });

  // Modal
  const modal = document.getElementById('beta-modal');
  function openModal(prefilledEmail) {
    if (prefilledEmail) {
      const i = modal.querySelector('input[name="email"]');
      if (i) i.value = prefilledEmail;
    }
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  function closeModal() {
    modal.classList.remove('active');
    const mm = document.getElementById('mobile-menu');
    if (!mm || !mm.classList.contains('open')) document.body.style.overflow = '';
  }
  document.getElementById('modal-close').addEventListener('click', closeModal);
  modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
  document.querySelectorAll('.open-modal').forEach(btn => btn.addEventListener('click', e => { e.preventDefault(); openModal(); }));

  // Hero form & beta-form-2 → open modal with prefill (so user gets the same success state)
  ['hero-form', 'beta-form-2'].forEach(id => {
    const f = document.getElementById(id);
    if (!f) return;
    f.addEventListener('submit', e => {
      e.preventDefault();
      const email = f.querySelector('input[name="email"]').value;
      openModal(email);
      setTimeout(() => document.getElementById('modal-form').requestSubmit(), 250);
    });
  });

  // Smooth scroll
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const href = a.getAttribute('href');
      if (href.length > 1) {
        const t = document.querySelector(href);
        if (t) { e.preventDefault(); window.scrollTo({ top: t.getBoundingClientRect().top + window.scrollY - 64, behavior: reduceMotion ? 'auto' : 'smooth' }); }
      }
    });
  });

  // Nav — el estilo (degradado) lo define el CSS; aquí solo lo referenciamos
  const nav = document.getElementById('nav');

  // Navbar: arranca compacto (clase nav-compact en el HTML) y se despliega
  // al primer scroll, quedándose expandido para siempre.
  let navExpanded = false;
  function expandNav() {
    if (navExpanded || !nav) return;
    navExpanded = true;
    nav.classList.remove('nav-compact');
  }
  if (nav) {
    if (reduceMotion || window.scrollY > 20) {
      // Sin animación o ya scrolleado al cargar: expandir sin transición.
      nav.classList.add('no-nav-anim');
      expandNav();
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { nav.classList.remove('no-nav-anim'); });
      });
    }
    window.addEventListener('scroll', function () {
      if (window.scrollY > 20) expandNav();
    }, { passive: true });
  }

  // Animaciones: calmadas y una sola vez. Funden y suben unos pocos píxeles;
  // sin rebotes ni escalas. El texto del hero no se anima: es el LCP.
  var heroPhone = document.querySelector('.hero__device .phone');
  if (!reduceMotion) {
    if (heroPhone) gsap.fromTo(heroPhone, { opacity: 0, y: 90 }, { opacity: 1, y: 0, duration: 1.2, delay: 0.15, ease: 'power3.out' });

    var RY = isMobile ? 18 : 28;
    var startPos = isMobile ? 'top 92%' : 'top 85%';
    gsap.utils.toArray('[data-reveal]').forEach(function(el) {
      gsap.from(el, { y: RY, opacity: 0, duration: 0.8, ease: 'power2.out',
        scrollTrigger: { trigger: el, start: startPos, once: true } });
    });
    // Grupos: los hijos entran escalonados (set inicial evita el parpadeo)
    gsap.utils.toArray('[data-reveal-stagger]').forEach(function(group) {
      var kids = gsap.utils.toArray(group.children);
      if (!kids.length) return;
      gsap.set(kids, { opacity: 0, y: RY });
      ScrollTrigger.create({ trigger: group, start: startPos, once: true,
        onEnter: function() { gsap.to(kids, { opacity: 1, y: 0, duration: 0.8, stagger: 0.09, ease: 'power2.out' }); } });
    });
  } else if (heroPhone) {
    heroPhone.style.opacity = 1;
  }

  // ===== Scrollytelling reels: el móvil queda fijo y el reel + el texto cambian al hacer scroll =====
  (function() {
    var stage = document.querySelector('.reels');
    if (!stage) return;
    var reels = gsap.utils.toArray('.reels__reel');
    var strip = stage.querySelector('.reels__strip');
    var steps = gsap.utils.toArray('.reels__step');
    if (!steps.length) return;

    // Si un reel aún no existe (archivo no subido), se oculta y se ve el placeholder.
    reels.forEach(function(v) {
      function hide() { v.style.display = 'none'; }
      v.addEventListener('error', hide);
      var s = v.querySelector('source');
      if (s) s.addEventListener('error', hide);
    });

    // MÓVIL/TABLET ≤860px: galería horizontal (CSS) con flechas. Sin filmstrip ni ScrollTrigger.
    // Cada reel (tarjeta) se reproduce solo cuando entra en pantalla, para ahorrar datos.
    if (window.matchMedia('(max-width: 860px)').matches) {
      var grid = stage.querySelector('.reels__grid');
      var prev = stage.querySelector('[data-reels-dir="-1"]');
      var next = stage.querySelector('[data-reels-dir="1"]');
      if (grid && prev && next) {
        var stepW = function() { return (reels[0] ? reels[0].getBoundingClientRect().width : grid.clientWidth * 0.8) + 16; };
        var syncArrows = function() {
          prev.disabled = grid.scrollLeft < 4;
          next.disabled = grid.scrollLeft + grid.clientWidth > grid.scrollWidth - 4;
        };
        prev.addEventListener('click', function() { grid.scrollBy({ left: -stepW(), behavior: reduceMotion ? 'auto' : 'smooth' }); });
        next.addEventListener('click', function() { grid.scrollBy({ left: stepW(), behavior: reduceMotion ? 'auto' : 'smooth' }); });
        grid.addEventListener('scroll', syncArrows, { passive: true });
        window.addEventListener('resize', syncArrows);
        syncArrows();
      }
      if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function(entries) {
          entries.forEach(function(e) {
            if (e.isIntersecting) { var p = e.target.play(); if (p && p.catch) p.catch(function() {}); }
            else { try { e.target.pause(); } catch (err) {} }
          });
        }, { threshold: 0.4 });
        reels.forEach(function(v) { io.observe(v); });
      } else {
        reels.forEach(function(v) { var p = v.play(); if (p && p.catch) p.catch(function() {}); });
      }
      steps.forEach(function(s) { s.classList.add('on'); });
      return;
    }

    stage.classList.add('js-active');
    var current = -1;
    // Filmstrip por pasos (sin hueco): la tira sube un alto completo por vídeo.
    function setStrip(i) {
      if (strip) strip.style.transform = 'translateY(' + (-i * 100) + '%)';
    }
    function activate(i) {
      if (i === current) return;
      current = i;
      setStrip(i);
      reels.forEach(function(v, idx) {
        if (idx === i) { v.classList.add('on'); var p = v.play(); if (p && p.catch) p.catch(function() {}); }
        else { v.classList.remove('on'); try { v.pause(); } catch (e) {} }
      });
      steps.forEach(function(s, idx) { s.classList.toggle('on', idx === i); });
    }
    // Cuando el texto del paso llega al centro, salta DIRECTO a su vídeo (snap), con su texto centrado.
    steps.forEach(function(step, i) {
      ScrollTrigger.create({ trigger: step, start: 'center center', end: 'bottom center',
        onToggle: function(self) { if (self.isActive) activate(i); } });
    });

    // No reproducimos el reel 0 al cargar (está bajo el fold): arranca cuando su paso entra
    // en el centro del viewport. Solo fijamos la posición inicial de la tira.
    setStrip(0);
  })();

  // FAQ
  document.querySelectorAll('.faq-q').forEach(q => q.addEventListener('click', () => {
    const isOpen = q.closest('.faq-item').classList.toggle('open');
    q.setAttribute('aria-expanded', isOpen);
  }));

  // FAQ — filtros por categoría (acorta la lista mostrando solo lo relevante)
  (function() {
    var chips = document.querySelectorAll('.faq-chip');
    if (!chips.length) return;
    var items = document.querySelectorAll('#faq .faq-item');
    chips.forEach(function(chip) {
      chip.addEventListener('click', function() {
        var cat = chip.getAttribute('data-filter');
        chips.forEach(function(c) { c.classList.toggle('active', c === chip); });
        items.forEach(function(item) {
          var show = cat === 'all' || item.getAttribute('data-cat') === cat;
          item.classList.toggle('hidden', !show);
          if (!show) {
            item.classList.remove('open');
            var b = item.querySelector('.faq-q');
            if (b) b.setAttribute('aria-expanded', 'false');
          }
        });
      });
    });
  })();

  // Capture referral code from URL (atribuir referidos) y spot (ver mi posición)
  const _urlParams = new URLSearchParams(window.location.search);
  const _refCode = _urlParams.get('ref') || null;
  const _spotCode = _urlParams.get('spot') || null;

  // Modal form submit
  const mForm = document.getElementById('modal-form');
  const mFormState = document.getElementById('modal-form-state');
  const mSuccess = document.getElementById('modal-success');
  const mBtn = document.getElementById('modal-submit');
  let mError = document.getElementById('modal-error');
  if (!mError) {
    mError = document.createElement('p');
    mError.id = 'modal-error';
    mError.setAttribute('role', 'alert');
    mError.style.cssText = 'font-size:14px;text-align:center;margin:4px 0 0;display:none;';
    mForm.appendChild(mError);
  }

  function showModalError(msg) { mError.textContent = msg; mError.style.display = 'block'; }
  function hideModalError() { mError.style.display = 'none'; }

  function animateNumber(target) {
    if (reduceMotion) { document.getElementById('ms-num').textContent = target; return; }
    const numEl = document.getElementById('ms-num');
    const numWrap = document.getElementById('ms-num-wrap');
    let cur = target + 38;
    numEl.textContent = cur;
    numWrap.classList.remove('pop');
    const step = () => {
      if (cur <= target) {
        numEl.textContent = target;
        requestAnimationFrame(() => { numWrap.classList.add('pop'); });
        return;
      }
      cur -= 1;
      numEl.textContent = cur;
      const rem = cur - target;
      setTimeout(step, rem > 12 ? 28 : rem > 6 ? 55 : 95);
    };
    setTimeout(step, 400);
  }

  let _msStats = null;
  function animateBar(position) {
    const fill = document.getElementById('ms-fill');
    // Ocupación REAL de la wave (nº total de inscritos), NO la posición del usuario.
    const total = (_msStats && _msStats.total) || position;
    const locked = (_msStats && _msStats.locked) || 0;
    const wave = position <= 100 ? 1 : position <= 250 ? 2 : 3;
    const cap = wave === 1 ? 100 : 150;
    const base = wave === 1 ? 0 : wave === 2 ? 100 : 250;
    const waveLabel = isEn ? `WAVE ${wave} SPOTS` : `PLAZAS WAVE ${wave}`;
    const taken = Math.min(Math.max(total - base, 0), cap);
    const free = Math.max(cap - taken, 0);
    const pct = Math.round(taken / cap * 100);
    const lockedTxt = (wave === 1 && locked > 0) ? (isEn ? ` · ${locked} secured 🔒` : ` · ${locked} aseguradas 🔒`) : '';
    document.getElementById('ms-wl-text').textContent = waveLabel;
    document.getElementById('ms-pos-frac').textContent = isEn ? `${free} available` : `${free} libres`;
    document.getElementById('ms-scarcity-taken').textContent = (isEn ? `${taken} taken` : `${taken} ocupada${taken !== 1 ? 's' : ''}`) + lockedTxt;
    document.getElementById('ms-scarcity-free').textContent = isEn ? `${free} available →` : `${free} disponible${free !== 1 ? 's' : ''} →`;
    if (reduceMotion) { fill.style.transition = 'none'; fill.style.transform = 'scaleX(' + (pct / 100) + ')'; return; }
    setTimeout(() => { fill.style.transform = 'scaleX(' + (pct / 100) + ')'; }, 500);
  }

  function showModalSuccess(referralCode, position, projection, stats) {
    position = position || 1;
    _msStats = stats || {};
    const link = referralCode ? `https://2trainapp.com?ref=${referralCode}` : 'https://2trainapp.com';

    // Determine wave
    const wave = position <= 100 ? 1 : position <= 250 ? 2 : 3;
    const waveData = {
      1: { badge1: 'Wave 1 ⚡', badge2: isEn ? 'Exclusive perks' : 'Ventajas exclusivas', badge3: 'Founding Member' },
      2: { badge1: 'Wave 2', badge2: isEn ? 'Second batch' : 'Segunda tanda', badge3: isEn ? 'Early access' : 'Acceso anticipado' },
      3: { badge1: 'Wave 3', badge2: isEn ? 'Before the public' : 'Antes que el público', badge3: isEn ? 'First come first served' : 'Por orden de llegada' },
    }[wave];
    document.getElementById('ms-badge-1').textContent = waveData.badge1;
    document.getElementById('ms-badge-2').textContent = waveData.badge2;
    document.getElementById('ms-badge-3').textContent = waveData.badge3;

    // Waves card: la tarjeta de escasez la rellena animateBar() con la ocupación real.
    ['ms-w1', 'ms-w2', 'ms-w3'].forEach((id, i) => {
      const el = document.getElementById(id);
      const isActive = i + 1 === wave;
      el.classList.toggle('active', isActive);
      if (isActive) el.querySelector('.ms-ss').textContent = isEn ? "You're here" : 'Tú estás aquí';
    });

    // Share heading: te faltan X referidos para asegurar tu plaza / plaza asegurada 🔒
    const referrals = (stats && stats.referrals) || 0;
    const lockedPos = stats && stats.locked_position;
    const shareH = document.getElementById('ms-share-h');
    if (lockedPos) {
      shareH.innerHTML = isEn ? `<span class="ms-b">🔒</span> Spot locked at #${lockedPos}` : `<span class="ms-b">🔒</span> Plaza asegurada en el #${lockedPos}`;
    } else {
      const need = Math.max(3 - referrals, 0);
      shareH.innerHTML = need > 0
        ? (isEn ? `<span class="ms-b">⚡</span> ${need} more referral${need !== 1 ? 's' : ''} to lock your spot` : `<span class="ms-b">⚡</span> Te falta${need !== 1 ? 'n' : ''} ${need} referido${need !== 1 ? 's' : ''} para asegurar tu plaza`)
        : (isEn ? `<span class="ms-b">⚡</span> Share to move up the list` : `<span class="ms-b">⚡</span> Comparte para subir en la lista`);
    }

    // Referral & share links
    if (referralCode) {
      document.getElementById('ms-ref').textContent = `2trainapp.com?ref=${referralCode}`;
      const copyBtn = document.getElementById('ms-copy');
      copyBtn.onclick = () => {
        navigator.clipboard.writeText(link).then(() => {
          copyBtn.textContent = isEn ? '✓ Copied' : '✓ Copiado';
          setTimeout(() => { copyBtn.textContent = isEn ? 'Copy link' : 'Copiar link'; }, 1600);
        });
      };
    }
    const waMsg = isEn
      ? encodeURIComponent(`I just reserved my spot on 2trAIn ⚡ An AI personal trainer that explains every decision. Only 100 spots with exclusive perks. Join with my link 👉 ${link}`)
      : encodeURIComponent(`Acabo de reservar mi plaza en 2trAIn ⚡ Un entrenador personal con IA que te explica cada decisión. Solo 100 plazas con ventajas exclusivas. Entra con mi link 👉 ${link}`);
    document.getElementById('ms-wa').href = `https://wa.me/?text=${waMsg}`;
    const twText = isEn
      ? encodeURIComponent(`I just reserved my spot on 2trAIn ⚡\n\nAI that explains EVERY decision in your training.\nOnly 100 spots with exclusive perks →`)
      : encodeURIComponent(`Acabo de reservar mi plaza en 2trAIn ⚡\n\nIA que te explica CADA decisión de tu entrenamiento.\nSolo 100 plazas con ventajas exclusivas →`);
    document.getElementById('ms-x').href = `https://twitter.com/intent/tweet?text=${twText}&url=${encodeURIComponent(link)}`;

    // Show success
    mFormState.classList.add('hidden');
    mSuccess.classList.remove('hidden');

    // Animations
    animateNumber(position);
    animateBar(position);

    // Click number to replay
    const numWrap = document.getElementById('ms-num-wrap');
    numWrap.style.cursor = 'pointer';
    numWrap.onclick = () => {
      const fill = document.getElementById('ms-fill');
      fill.style.transition = 'none';
      fill.style.transform = 'scaleX(0)';
      void fill.offsetWidth;
      fill.style.transition = '';
      animateNumber(position);
      animateBar(position);
    };
  }

  mForm.addEventListener('submit', async e => {
    e.preventDefault();
    hideModalError();
    const email = mForm.querySelector('input[name="email"]').value.trim();
    mBtn.querySelector('.btn-label').textContent = isEn ? 'Sending…' : 'Enviando…';
    mBtn.disabled = true; mBtn.style.opacity = '0.6';

    try {
      const res = await fetch('https://nruzjtqewjakfwshfagz.supabase.co/functions/v1/join-waitlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        },
        body: JSON.stringify({ email, referred_by: _refCode, lang: isEn ? 'en' : 'es', hp: (mForm.querySelector('input[name="company"]') || {}).value || '' }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error desconocido');
      showModalSuccess(data.referral_code, data.position, data.projection, data);
    } catch (err) {
      console.error('Waitlist error:', err);
      showModalError(isEn ? 'Something went wrong. Try again or contact us.' : 'Algo salió mal. Inténtalo de nuevo o escríbenos.');
      mBtn.querySelector('.btn-label').textContent = isEn ? 'Reserve a spot' : 'Reservar plaza';
      mBtn.disabled = false; mBtn.style.opacity = '';
    }
  });

  // CTA email "Ver mi posición" → ?spot=CODE abre el modal con la plaza real
  if (_spotCode) {
    openModal();
    mFormState.classList.add('hidden');
    mSuccess.classList.remove('hidden');
    const statusEl = document.querySelector('#modal-success .ms-status');
    if (statusEl) statusEl.textContent = isEn ? 'Loading…' : 'Cargando…';
    (async () => {
      try {
        const res = await fetch('https://nruzjtqewjakfwshfagz.supabase.co/functions/v1/join-waitlist', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          },
          body: JSON.stringify({ referral_code: _spotCode, lang: isEn ? 'en' : 'es' }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error');
        showModalSuccess(data.referral_code, data.position, data.projection, data);
        // Limpia ?spot= de la URL sin recargar (evita reabrir al compartir la barra)
        try {
          const u = new URL(window.location.href);
          u.searchParams.delete('spot');
          window.history.replaceState({}, '', u.pathname + (u.search || '') + u.hash);
        } catch (_) {}
      } catch (err) {
        console.error('Spot lookup error:', err);
        mSuccess.classList.add('hidden');
        mFormState.classList.remove('hidden');
        showModalError(isEn
          ? 'We could not find that spot. Join the waitlist below.'
          : 'No encontramos esa plaza. Apúntate abajo.');
      }
    })();
  }

  modal.addEventListener('transitionend', () => {
    if (!modal.classList.contains('active')) {
      setTimeout(() => {
        mFormState.classList.remove('hidden');
        mSuccess.classList.add('hidden');
        mForm.reset();
        hideModalError();
        mBtn.querySelector('.btn-label').textContent = isEn ? 'Reserve a spot' : 'Reservar plaza';
        mBtn.disabled = false; mBtn.style.opacity = '';
        // Reset bar for next open
        const fill = document.getElementById('ms-fill');
        if (fill) { fill.style.transition = 'none'; fill.style.transform = 'scaleX(0)'; }
      }, 50);
    }
  });
})();

// Cuenta atrás retirada (2026-09-02). Apuntaba al 2026-09-01 y, una vez
// vencida, dejaba en el bloque de conversión la frase "La beta abre el 1 de
// septiembre · faltan / Beta disponible" en ES y EN. La escasez de esta
// página pasa a ser de plazas —la escalera de waves de #beta-offer—, que no
// caduca sola. No reintroducir un contador sin un dueño de la fecha.

// Mobile menu
(function() {
  const toggle = document.getElementById('nav-toggle');
  const menu   = document.getElementById('mobile-menu');
  const nav    = document.getElementById('nav');
  if (!toggle || !menu) return;

  function openMenu() {
    menu.classList.add('open');
    menu.setAttribute('aria-hidden', 'false');
    nav.classList.remove('nav-compact'); // si aún está compacto, despliega la barra
    nav.classList.add('nav-open');
    toggle.setAttribute('aria-label', isEn ? 'Close menu' : 'Cerrar menú');
    toggle.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    const first = menu.querySelector('a, button');
    if (first) first.focus();
  }

  function closeMenu() {
    menu.classList.remove('open');
    menu.setAttribute('aria-hidden', 'true');
    nav.classList.remove('nav-open');
    toggle.setAttribute('aria-label', isEn ? 'Open menu' : 'Abrir menú');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    toggle.focus();
  }

  toggle.addEventListener('click', function() {
    menu.classList.contains('open') ? closeMenu() : openMenu();
  });

  // Close on any link click inside the menu
  menu.querySelectorAll('a').forEach(function(a) {
    a.addEventListener('click', closeMenu);
  });

  // Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && menu.classList.contains('open')) closeMenu();
  });
})();

// ===== Objetivos: preview del plan según meta elegida =====
(function() {
  var section = document.querySelector('#objetivos');
  if (!section) return;
  var opts = section.querySelectorAll('.goal-opt');
  var textEl = section.querySelector('#goals-preview-text');
  if (!opts.length || !textEl) return;

  var en = document.documentElement.lang === 'en';
  var copy = en ? {
    fuerza: 'Push, pull and leg blocks with weekly load progression. Every change in volume or intensity, <strong>explained with your data</strong>.',
    cardio: 'Zone 2 base, controlled intensity days and recovery built in. Conditioning that <strong>fits your week</strong>, not random HIIT.',
    prueba: 'Toward your race day: specific strength, cardio and event stations — periodized to the date, with <strong>taper when it matters</strong>.',
    mantener: 'Sustainable frequency to stay in shape or ease back in. Enough stimulus to progress, <strong>without burning out</strong>.'
  } : {
    fuerza: 'Bloques de empuje, tirón y pierna con progresión de carga. Cada cambio de volumen o intensidad, <strong>explicado con tus datos</strong>.',
    cardio: 'Base Zone 2, días de intensidad controlada y recuperación integrada. Condición que <strong>encaja en tu semana</strong>, no HIIT al azar.',
    prueba: 'Hacia tu fecha: fuerza útil, cardio y estaciones o disciplinas — periodizado al evento, con <strong>taper cuando toca</strong>.',
    mantener: 'Frecuencia sostenible para mantener forma o volver con calma. Estímulo suficiente para progresar, <strong>sin quemarte</strong>.'
  };

  opts.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var key = btn.getAttribute('data-goal');
      if (!key || !copy[key]) return;
      opts.forEach(function(b) { b.setAttribute('aria-pressed', String(b === btn)); });
      textEl.innerHTML = copy[key];
    });
  });
})();

// ===== Demo "Míralo pensar": pensar → colapsar → generar (soporta varios escenarios) =====
(function() {
  var section = document.querySelector('#demo');
  if (!section || typeof gsap === 'undefined') return;

  var tabs = section.querySelectorAll('.demo-tab');
  var scenarios = Array.prototype.slice.call(section.querySelectorAll('.demo-scenario'));
  var demoEN = document.documentElement.lang === 'en';
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var activeTl = null;
  var hasStarted = false;

  // El carrusel es de scroll manual con snap (no marquee): al generar la
  // sesión solo se vuelve al primer ejercicio. Antes se duplicaba la pista
  // para un bucle que ya no existe y salían las 6 tarjetas dos veces.
  function restartMarquee(chat) {
    var carousel = chat && chat.querySelector('.demo-carousel');
    if (carousel) carousel.scrollLeft = 0;
  }

  var phrasesByScenario = {
    pain: demoEN ? [
      'Reading your history…',
      'Detecting shoulder discomfort…',
      'Ruling out risky exercises…',
      'Finding safe angles…',
      'Adding a preventive warm-up…'
    ] : [
      'Leyendo tu historial…',
      'Detectando molestia en el hombro…',
      'Descartando ejercicios de riesgo…',
      'Buscando ángulos seguros…',
      'Añadiendo calentamiento preventivo…'
    ],
    race: demoEN ? [
      'Reading your goal and date…',
      'Checking strength vs cardio base…',
      'Building hybrid weekly blocks…',
      'Periodizing toward race day…',
      'Keeping one strength day…'
    ] : [
      'Leyendo objetivo y fecha…',
      'Cruzando base de fuerza y cardio…',
      'Montando bloques híbridos…',
      'Periodizando hacia la prueba…',
      'Reservando un día de fuerza…'
    ]
  };

  function showOnly(key) {
    scenarios.forEach(function(sc) {
      var on = sc.getAttribute('data-scenario') === key;
      sc.classList.toggle('on', on);
      sc.setAttribute('aria-hidden', String(!on));
    });
    tabs.forEach(function(t, i) {
      var on = t.getAttribute('data-scenario') === key;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      // La píldora blanca del selector segmentado se desliza a la pestaña activa
      if (on && t.parentNode) t.parentNode.style.setProperty('--i', i);
    });
    return section.querySelector('.demo-scenario.on');
  }

  function bindToggle(chat) {
    var toggle = chat.querySelector('.demo-reason__toggle');
    if (!toggle || toggle.dataset.bound === '1') return;
    toggle.dataset.bound = '1';
    toggle.addEventListener('click', function() {
      var box = chat.querySelector('.demo-reason');
      var body = chat.querySelector('.demo-reason__body');
      if (!box || !body || !box.classList.contains('is-interactive')) return;
      var willCollapse = !box.classList.contains('is-collapsed');
      box.classList.toggle('is-collapsed');
      toggle.setAttribute('aria-expanded', String(!willCollapse));
      if (willCollapse) {
        chat.classList.remove('is-open');
        gsap.to(body, { height: 0, opacity: 0, duration: 0.35, ease: 'power2.inOut' });
      } else {
        chat.classList.add('is-open');
        gsap.fromTo(body, { height: 0, opacity: 0 }, { height: 'auto', opacity: 1, duration: 0.35, ease: 'power2.out' });
      }
    });
  }

  function playChat(chat) {
    if (!chat) return;
    if (activeTl) {
      activeTl.kill();
      activeTl = null;
    }

    var statusEl = chat.querySelector('.demo-chat__status-text');
    var user = chat.querySelector('.demo-bubble--user');
    var reasonBox = chat.querySelector('.demo-reason');
    var reasonBody = chat.querySelector('.demo-reason__body');
    var reasonLines = gsap.utils.toArray(chat.querySelectorAll('.demo-reason__line'));
    var toggle = chat.querySelector('.demo-reason__toggle');
    var label = chat.querySelector('.demo-reason__label');
    var aiBubble = chat.querySelector('.demo-bubble--ai');
    var genWrap = chat.querySelector('.demo-gen');
    var genHead = chat.querySelector('.demo-gen__head');
    var carousel = chat.querySelector('.demo-carousel');
    var goBtn = chat.querySelector('.demo-go');
    var scenario = chat.getAttribute('data-scenario') || 'pain';
    var phrases = phrasesByScenario[scenario] || phrasesByScenario.pain;

    chat.classList.add('demo-chat--seq');
    chat.classList.remove('is-open');
    if (reasonBox) reasonBox.classList.remove('is-interactive', 'is-collapsed');
    if (toggle) toggle.setAttribute('aria-expanded', 'true');
    if (label) { gsap.set(label, { opacity: 1 }); label.textContent = demoEN ? 'Reasoning with your data' : 'Razonando con tus datos'; }
    if (statusEl) { gsap.set(statusEl, { opacity: 1 }); statusEl.textContent = demoEN ? 'Reasoning with your data' : 'Razonando con tus datos'; }
    if (aiBubble) aiBubble.classList.add('demo-pending');
    if (genWrap) genWrap.classList.add('demo-pending');
    bindToggle(chat);

    if (reduceMotion) {
      gsap.set([user, reasonBox].concat(reasonLines), { clearProps: 'all' });
      if (reasonBody) gsap.set(reasonBody, { height: 0, opacity: 0 });
      if (reasonBox) reasonBox.classList.add('is-interactive', 'is-collapsed');
      if (label) label.textContent = demoEN ? 'Reasoned with your data' : 'Razonado con tus datos';
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
      if (statusEl) statusEl.textContent = demoEN ? 'Session generated ✓' : 'Sesión generada ✓';
      if (aiBubble) aiBubble.classList.remove('demo-pending');
      if (genWrap) genWrap.classList.remove('demo-pending');
      restartMarquee(chat);
      return;
    }

    gsap.set([user, reasonBox], { opacity: 0, y: 14 });
    gsap.set(reasonLines, { opacity: 0, y: 8 });
    if (reasonBody) gsap.set(reasonBody, { height: 'auto', opacity: 1 });
    gsap.set([genHead, carousel, goBtn].filter(Boolean), { opacity: 0, y: 14 });

    function setStatus(t) {
      if (!statusEl) return;
      gsap.to(statusEl, { opacity: 0, duration: 0.15, onComplete: function() {
        statusEl.textContent = t;
        gsap.to(statusEl, { opacity: 1, duration: 0.15 });
      }});
    }
    function setPhrase(t) {
      if (!label) return;
      gsap.to(label, { opacity: 0, duration: 0.15, onComplete: function() {
        label.textContent = t;
        gsap.to(label, { opacity: 1, duration: 0.15 });
      }});
    }

    // Siempre timeline inmediata (sin ScrollTrigger): más fiable al cambiar de tab
    var tl = gsap.timeline({ defaults: { ease: 'power2.out' } });
    activeTl = tl;

    tl.to(user, { opacity: 1, y: 0, duration: 0.35 });
    tl.to(reasonBox, { opacity: 1, y: 0, duration: 0.35 }, '+=0.2');

    reasonLines.forEach(function(line, i) {
      tl.call(setPhrase, [phrases[i % phrases.length]]);
      tl.to(line, { opacity: 1, y: 0, duration: 0.28 }, '+=0.04');
      tl.to({}, { duration: 0.35 });
    });

    tl.call(function() {
      if (reasonBox) reasonBox.classList.add('is-interactive', 'is-collapsed');
      if (label) { gsap.set(label, { opacity: 1 }); label.textContent = demoEN ? 'Reasoned with your data' : 'Razonado con tus datos'; }
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
    }, null, '+=0.2');
    tl.to(reasonBody, { height: 0, opacity: 0, duration: 0.4, ease: 'power2.inOut' });
    tl.call(setStatus, [demoEN ? 'Generating your session…' : 'Generando tu sesión…']);

    tl.call(function() { if (aiBubble) aiBubble.classList.remove('demo-pending'); });
    tl.fromTo(aiBubble, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.35 }, '+=0.05');

    tl.call(function() {
      if (genWrap) genWrap.classList.remove('demo-pending');
      restartMarquee(chat);
    });
    tl.to(genHead, { opacity: 1, y: 0, duration: 0.3 }, '+=0.08');
    tl.to(carousel, { opacity: 1, y: 0, duration: 0.4, ease: 'power3.out' }, '-=0.1');
    tl.call(function() {
      setStatus(demoEN ? 'Session generated ✓' : 'Sesión generada ✓');
      restartMarquee(chat);
    });
    tl.to(goBtn, { opacity: 1, y: 0, duration: 0.3 }, '+=0.05');
  }

  // Prep visual inicial: oculta lo animable hasta que entre en vista
  scenarios.forEach(function(sc) {
    var user = sc.querySelector('.demo-bubble--user');
    var reasonBox = sc.querySelector('.demo-reason');
    var aiBubble = sc.querySelector('.demo-bubble--ai');
    var genWrap = sc.querySelector('.demo-gen');
    sc.classList.add('demo-chat--seq');
    if (aiBubble) aiBubble.classList.add('demo-pending');
    if (genWrap) genWrap.classList.add('demo-pending');
    if (!reduceMotion) {
      if (user) gsap.set(user, { opacity: 0, y: 14 });
      if (reasonBox) gsap.set(reasonBox, { opacity: 0, y: 14 });
    }
  });
  showOnly('pain');

  tabs.forEach(function(tab, i) {
    tab.addEventListener('click', function() {
      var key = tab.getAttribute('data-scenario');
      if (!key || tab.getAttribute('aria-selected') === 'true') return;
      var chat = showOnly(key);
      requestAnimationFrame(function() { playChat(chat); });
    });
    tab.addEventListener('keydown', function(e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault();
      var to = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      to.focus();
      to.click();
    });
  });

  // Arranca al entrar en viewport (IntersectionObserver, sin ScrollTrigger)
  function startWhenVisible() {
    if (hasStarted) return;
    hasStarted = true;
    var chat = section.querySelector('.demo-scenario.on') || scenarios[0];
    playChat(chat);
  }

  if (reduceMotion) {
    startWhenVisible();
  } else if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function(entries) {
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].isIntersecting) {
          startWhenVisible();
          io.disconnect();
          break;
        }
      }
    }, { threshold: 0.25, rootMargin: '0px 0px -10% 0px' });
    io.observe(section);
  } else {
    startWhenVisible();
  }
})();

// ===== "Pruébalo ya mismo": en móvil va DESPUÉS del chat (primero ves la demo, luego la usas) =====
(function() {
  var cta = document.querySelector('.demo-head__cta');
  var head = document.querySelector('.demo-head');
  var wrap = document.querySelector('#demo .demo-scenarios') || document.querySelector('#demo .demo-chat');
  if (!cta || !head || !wrap) return;
  var mq = window.matchMedia('(max-width: 860px)');
  function place() {
    if (mq.matches) {
      if (wrap.nextElementSibling !== cta) wrap.parentNode.insertBefore(cta, wrap.nextSibling);
    } else {
      if (cta.parentNode !== head) head.appendChild(cta);
    }
  }
  place();
  if (mq.addEventListener) mq.addEventListener('change', place);
  else if (mq.addListener) mq.addListener(place);
})();
