// Product image carousel — cross-fade, no auto-advance. Hides controls when one slide.
document.addEventListener('DOMContentLoaded', function() {
  var carousel = document.querySelector('.product-detail__carousel');
  if (!carousel) return;

  var slides = carousel.querySelectorAll('.product-detail__slide');
  var dots = carousel.querySelectorAll('.product-detail__dot');
  var prevBtn = carousel.querySelector('.product-detail__nav--prev');
  var nextBtn = carousel.querySelector('.product-detail__nav--next');
  var dotsWrap = carousel.querySelector('.product-detail__dots');

  if (slides.length <= 1) {
    if (prevBtn) prevBtn.style.display = 'none';
    if (nextBtn) nextBtn.style.display = 'none';
    if (dotsWrap) dotsWrap.style.display = 'none';
    return;
  }

  var current = 0;
  function goTo(idx) {
    current = (idx + slides.length) % slides.length;
    slides.forEach(function(s, i) { s.classList.toggle('is-active', i === current); });
    dots.forEach(function(d, i) {
      var active = i === current;
      d.classList.toggle('is-active', active);
      if (active) {
        d.setAttribute('aria-current', 'true');
      } else {
        d.removeAttribute('aria-current');
      }
    });
  }
  if (nextBtn) nextBtn.addEventListener('click', function() { goTo(current + 1); });
  if (prevBtn) prevBtn.addEventListener('click', function() { goTo(current - 1); });
  dots.forEach(function(d, i) {
    d.addEventListener('click', function() { goTo(i); });
  });
});

// Hero carousel — cross-fade with auto-advance, dots, prev/next, pause on hover.
// Respects prefers-reduced-motion (starts paused) and exposes a manual pause/play toggle
// (WCAG 2.2.2 — auto-advancing content needs a way to stop it besides hover/focus).
document.addEventListener('DOMContentLoaded', function() {
  var carousel = document.querySelector('.hero__carousel');
  if (!carousel) return;

  var slides = carousel.querySelectorAll('.hero__slide');
  var dots = carousel.querySelectorAll('.hero__dot');
  var prevBtn = carousel.querySelector('.hero__nav--prev');
  var nextBtn = carousel.querySelector('.hero__nav--next');
  var pauseBtn = carousel.querySelector('.hero__pause');
  if (slides.length <= 1) {
    if (prevBtn) prevBtn.style.display = 'none';
    if (nextBtn) nextBtn.style.display = 'none';
    if (dots.length) dots.forEach(function(d) { d.style.display = 'none'; });
    if (pauseBtn) pauseBtn.style.display = 'none';
    return;
  }

  var PAUSE_ICON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"></rect><rect x="14" y="5" width="4" height="14" rx="1"></rect></svg>';
  var PLAY_ICON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"></path></svg>';

  var current = 0;
  var timer = null;
  var DELAY = 6000;
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var userPaused = reduceMotion;

  function goTo(idx) {
    current = (idx + slides.length) % slides.length;
    slides.forEach(function(s, i) { s.classList.toggle('is-active', i === current); });
    dots.forEach(function(d, i) {
      var active = i === current;
      d.classList.toggle('is-active', active);
      if (active) {
        d.setAttribute('aria-current', 'true');
      } else {
        d.removeAttribute('aria-current');
      }
    });
  }

  function next() { goTo(current + 1); }
  function prev() { goTo(current - 1); }

  function start() { stop(); if (!userPaused) timer = setInterval(next, DELAY); }
  function stop() { if (timer) { clearInterval(timer); timer = null; } }

  function updatePauseBtn() {
    if (!pauseBtn) return;
    pauseBtn.setAttribute('aria-pressed', userPaused ? 'true' : 'false');
    pauseBtn.setAttribute('aria-label', userPaused ? 'Retomar apresentação automática' : 'Pausar apresentação automática');
    pauseBtn.innerHTML = userPaused ? PLAY_ICON : PAUSE_ICON;
  }

  if (nextBtn) nextBtn.addEventListener('click', function() { next(); start(); });
  if (prevBtn) prevBtn.addEventListener('click', function() { prev(); start(); });
  dots.forEach(function(d, i) {
    d.addEventListener('click', function() { goTo(i); start(); });
  });

  if (pauseBtn) {
    pauseBtn.addEventListener('click', function() {
      userPaused = !userPaused;
      updatePauseBtn();
      if (userPaused) { stop(); } else { start(); }
    });
  }

  carousel.addEventListener('mouseenter', stop);
  carousel.addEventListener('mouseleave', function() { if (!userPaused) start(); });
  carousel.addEventListener('focusin', stop);
  carousel.addEventListener('focusout', function() { if (!userPaused) start(); });

  updatePauseBtn();
  start();
});

// Hero background video — only load it on desktop widths. It's a 4MB+ file that autoplay
// would otherwise pull in full on every visit, mobile included; small screens keep the
// solid hero background instead. Mirrors the CSS breakpoint at max-width: 768px.
document.addEventListener('DOMContentLoaded', function() {
  var video = document.querySelector('.hero__video-bg video');
  if (!video) return;
  var src = video.getAttribute('data-src');
  if (!src) return;

  var mq = window.matchMedia('(min-width: 769px)');
  function apply() {
    if (mq.matches) {
      if (!video.getAttribute('src')) {
        video.setAttribute('src', src);
        video.load();
        video.play().catch(function() {});
      }
    } else if (video.getAttribute('src')) {
      video.pause();
      video.removeAttribute('src');
      video.load();
    }
  }
  apply();
  if (mq.addEventListener) mq.addEventListener('change', apply);
});

// Mobile menu toggle
function toggleMenu() {
  var nav = document.getElementById('mainNav');
  nav.classList.toggle('open');
}

// Close mobile menu when clicking a link
document.addEventListener('DOMContentLoaded', function() {
  var navLinks = document.querySelectorAll('.header__nav a');
  navLinks.forEach(function(link) {
    link.addEventListener('click', function() {
      var nav = document.getElementById('mainNav');
      nav.classList.remove('open');
    });
  });
});

// Sync aria-expanded on nav dropdown so AT announcements reflect actual state.
// CSS opens the menu on :hover/:focus-within; we mirror that to ARIA here.
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.nav-dropdown').forEach(function(dd) {
    var trigger = dd.querySelector('[aria-haspopup="true"]');
    if (!trigger) return;
    function open() { trigger.setAttribute('aria-expanded', 'true'); }
    function close() { trigger.setAttribute('aria-expanded', 'false'); }
    dd.addEventListener('mouseenter', open);
    dd.addEventListener('mouseleave', close);
    dd.addEventListener('focusin', open);
    dd.addEventListener('focusout', function(e) {
      if (!dd.contains(e.relatedTarget)) close();
    });
  });
});

// Product catalog filters — two-tier tipo + contextual secondary filters.
// Supports URL preselect via ?tipo=micro-ac|micro-dc|axial|acessorio.
document.addEventListener('DOMContentLoaded', function() {
  var filterBtns = document.querySelectorAll('.filter-btn');
  if (!filterBtns.length) return;

  function setActive(btn, active) {
    btn.classList.toggle('active', active);
    btn.setAttribute('aria-pressed', active ? 'true' : 'false');
  }
  filterBtns.forEach(function(btn) { setActive(btn, btn.classList.contains('active')); });

  function activeValue(name) {
    var groups = document.querySelectorAll('.filter-group');
    for (var i = 0; i < groups.length; i++) {
      var g = groups[i];
      if (g.classList.contains('is-hidden')) continue;
      var btn = g.querySelector('.filter-btn[data-filter="' + name + '"].active');
      if (btn) return btn.getAttribute('data-value');
    }
    return 'all';
  }

  function syncGroupVisibility(tipo) {
    document.querySelectorAll('.filter-group[data-context]').forEach(function(g) {
      var ctx = g.getAttribute('data-context').split(/\s+/);
      var show = ctx.indexOf(tipo) >= 0;
      g.classList.toggle('is-hidden', !show);
      if (!show) {
        g.querySelectorAll('.filter-btn').forEach(function(b) { setActive(b, false); });
        var allBtn = g.querySelector('.filter-btn[data-value="all"]');
        if (allBtn) setActive(allBtn, true);
      }
    });
  }

  function applyFilters() {
    var tipo = activeValue('tipo');
    syncGroupVisibility(tipo);

    var subtipo = activeValue('subtipo');
    var tensao = activeValue('tensao');
    var mancal = activeValue('mancal');
    var funcao = activeValue('funcao');

    var cards = document.querySelectorAll('.product-card');
    var count = 0;
    cards.forEach(function(card) {
      var cardTipo = card.getAttribute('data-tipo') || '';
      var cardSubtipo = card.getAttribute('data-subtipo') || '';
      var cardTensao = card.getAttribute('data-tensao') || '';
      var cardMancal = card.getAttribute('data-mancal') || '';
      var cardFuncao = card.getAttribute('data-funcao') || '';

      var show =
        (tipo === 'all' || cardTipo === tipo) &&
        (subtipo === 'all' || cardSubtipo === subtipo) &&
        (tensao === 'all' || cardTensao === tensao) &&
        (mancal === 'all' || cardMancal === mancal) &&
        (funcao === 'all' || cardFuncao === funcao);

      card.style.display = show ? '' : 'none';
      if (show) count++;
    });

    var countEl = document.querySelector('.catalog__count');
    if (countEl) countEl.textContent = count + ' produto(s) encontrado(s)';
  }

  filterBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var parentGroup = btn.closest('.filter-group');
      if (parentGroup) {
        parentGroup.querySelectorAll('.filter-btn').forEach(function(b) {
          setActive(b, false);
        });
      }
      setActive(btn, true);
      applyFilters();
    });
  });

  // Pre-select from ?tipo= and ?subtipo= URL params so links from index/header land on a filtered view.
  var urlParams = new URLSearchParams(location.search);
  var tipoParam = urlParams.get('tipo');
  if (tipoParam) {
    var preselect = document.querySelector('.filter-btn[data-filter="tipo"][data-value="' + tipoParam + '"]');
    if (preselect) {
      document.querySelectorAll('.filter-btn[data-filter="tipo"]').forEach(function(b) {
        setActive(b, false);
      });
      setActive(preselect, true);
    }
  }

  var subtipoParam = urlParams.get('subtipo');
  if (subtipoParam) {
    var preselectSub = document.querySelector('.filter-btn[data-filter="subtipo"][data-value="' + subtipoParam + '"]');
    if (preselectSub) {
      document.querySelectorAll('.filter-btn[data-filter="subtipo"]').forEach(function(b) {
        setActive(b, false);
      });
      setActive(preselectSub, true);
    }
  }

  applyFilters();
});

// Submits a form to /submit.php and updates the inline success/error elements.
function submitForm(form, type, successId, errorId) {
  var data = new FormData(form);
  data.append('type', type);

  var button = form.querySelector('button[type="submit"]');
  var originalText = button ? button.textContent : '';
  var successEl = document.getElementById(successId);
  var errorEl = document.getElementById(errorId);

  if (successEl) successEl.classList.remove('show');
  if (errorEl) errorEl.classList.remove('show');
  if (button) {
    button.disabled = true;
    button.textContent = 'Enviando...';
  }

  fetch('/submit.php', { method: 'POST', body: data })
    .then(function (resp) {
      return resp.json().then(function (json) {
        return { status: resp.status, json: json };
      });
    })
    .then(function (result) {
      if (result.json && result.json.ok) {
        if (successEl) successEl.classList.add('show');
        form.reset();
      } else {
        var msg = (result.json && result.json.error)
          ? result.json.error
          : 'Erro ao enviar mensagem. Tente novamente em instantes.';
        if (errorEl) {
          errorEl.textContent = msg;
          errorEl.classList.add('show');
        }
      }
    })
    .catch(function () {
      if (errorEl) {
        errorEl.textContent = 'Falha de conexao. Verifique sua internet e tente novamente.';
        errorEl.classList.add('show');
      }
    })
    .finally(function () {
      if (button) {
        button.disabled = false;
        button.textContent = originalText;
      }
    });
}

// Contact form handler — fale-conosco.html
function handleContactForm(e) {
  e.preventDefault();
  submitForm(e.target, 'contact', 'contactSuccess', 'contactError');
  return false;
}

// Career form handler — carreira.html
function handleCareerForm(e) {
  e.preventDefault();
  submitForm(e.target, 'career', 'careerSuccess', 'careerError');
  return false;
}

// Brazilian phone mask: (XX) XXXXX-XXXX (mobile) or (XX) XXXX-XXXX (landline).
// Reformats on every input so paste + typing both end up clean.
function maskPhone(el) {
  el.addEventListener('input', function () {
    var v = el.value.replace(/\D/g, '').slice(0, 11);
    if (v.length > 10) {
      el.value = '(' + v.slice(0, 2) + ') ' + v.slice(2, 7) + '-' + v.slice(7, 11);
    } else if (v.length > 6) {
      el.value = '(' + v.slice(0, 2) + ') ' + v.slice(2, 6) + '-' + v.slice(6, 10);
    } else if (v.length > 2) {
      el.value = '(' + v.slice(0, 2) + ') ' + v.slice(2);
    } else if (v.length > 0) {
      el.value = '(' + v;
    } else {
      el.value = '';
    }
  });
}

// Date mask: DD/MM/AAAA
function maskDate(el) {
  el.addEventListener('input', function () {
    var v = el.value.replace(/\D/g, '').slice(0, 8);
    if (v.length > 4) {
      el.value = v.slice(0, 2) + '/' + v.slice(2, 4) + '/' + v.slice(4, 8);
    } else if (v.length > 2) {
      el.value = v.slice(0, 2) + '/' + v.slice(2);
    } else {
      el.value = v;
    }
  });
}

// Brazilian currency mask: R$ X.XXX,XX (treats every keystroke as cents).
function maskCurrency(el) {
  el.addEventListener('input', function () {
    var digits = el.value.replace(/\D/g, '');
    if (!digits) { el.value = ''; return; }
    if (digits.length > 13) digits = digits.slice(0, 13);
    var num = (parseInt(digits, 10) / 100).toFixed(2);
    var parts = num.split('.');
    var intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    el.value = 'R$ ' + intPart + ',' + parts[1];
  });
}

document.addEventListener('DOMContentLoaded', function () {
  var byId = function (id) { return document.getElementById(id); };
  var ct = byId('contact-telefone'); if (ct) maskPhone(ct);
  var rt = byId('career-telefone');  if (rt) maskPhone(rt);
  var rn = byId('career-nascimento'); if (rn) maskDate(rn);
  var rp = byId('career-pretensao');  if (rp) maskCurrency(rp);
});
