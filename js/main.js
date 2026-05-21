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
      d.setAttribute('aria-selected', active ? 'true' : 'false');
    });
  }
  if (nextBtn) nextBtn.addEventListener('click', function() { goTo(current + 1); });
  if (prevBtn) prevBtn.addEventListener('click', function() { goTo(current - 1); });
  dots.forEach(function(d, i) {
    d.addEventListener('click', function() { goTo(i); });
  });
});

// Hero carousel — cross-fade with auto-advance, dots, prev/next, pause on hover
document.addEventListener('DOMContentLoaded', function() {
  var carousel = document.querySelector('.hero__carousel');
  if (!carousel) return;

  var slides = carousel.querySelectorAll('.hero__slide');
  var dots = carousel.querySelectorAll('.hero__dot');
  var prevBtn = carousel.querySelector('.hero__nav--prev');
  var nextBtn = carousel.querySelector('.hero__nav--next');
  if (slides.length <= 1) {
    if (prevBtn) prevBtn.style.display = 'none';
    if (nextBtn) nextBtn.style.display = 'none';
    if (dots.length) dots.forEach(function(d) { d.style.display = 'none'; });
    return;
  }

  var current = 0;
  var timer = null;
  var DELAY = 6000;

  function goTo(idx) {
    current = (idx + slides.length) % slides.length;
    slides.forEach(function(s, i) { s.classList.toggle('is-active', i === current); });
    dots.forEach(function(d, i) {
      var active = i === current;
      d.classList.toggle('is-active', active);
      d.setAttribute('aria-selected', active ? 'true' : 'false');
    });
  }

  function next() { goTo(current + 1); }
  function prev() { goTo(current - 1); }

  function start() { stop(); timer = setInterval(next, DELAY); }
  function stop() { if (timer) { clearInterval(timer); timer = null; } }

  if (nextBtn) nextBtn.addEventListener('click', function() { next(); start(); });
  if (prevBtn) prevBtn.addEventListener('click', function() { prev(); start(); });
  dots.forEach(function(d, i) {
    d.addEventListener('click', function() { goTo(i); start(); });
  });

  carousel.addEventListener('mouseenter', stop);
  carousel.addEventListener('mouseleave', start);
  carousel.addEventListener('focusin', stop);
  carousel.addEventListener('focusout', start);

  start();
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
        g.querySelectorAll('.filter-btn').forEach(function(b) { b.classList.remove('active'); });
        var allBtn = g.querySelector('.filter-btn[data-value="all"]');
        if (allBtn) allBtn.classList.add('active');
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
          b.classList.remove('active');
        });
      }
      btn.classList.add('active');
      applyFilters();
    });
  });

  // Pre-select from ?tipo= URL param so links from index/header land on a filtered view.
  var tipoParam = new URLSearchParams(location.search).get('tipo');
  if (tipoParam) {
    var preselect = document.querySelector('.filter-btn[data-filter="tipo"][data-value="' + tipoParam + '"]');
    if (preselect) {
      document.querySelectorAll('.filter-btn[data-filter="tipo"]').forEach(function(b) {
        b.classList.remove('active');
      });
      preselect.classList.add('active');
    }
  }

  applyFilters();
});

// Contact form handler
function handleContactForm(e) {
  e.preventDefault();
  var form = e.target;
  var data = new FormData(form);

  // Build mailto link as fallback (static site on shared hosting)
  var subject = encodeURIComponent('Contato via Site - ' + data.get('nome'));
  var body = encodeURIComponent(
    'Nome: ' + data.get('nome') + '\n' +
    'Telefone: ' + data.get('telefone') + '\n' +
    'E-mail: ' + data.get('email') + '\n\n' +
    'Mensagem:\n' + (data.get('mensagem') || '(sem mensagem)')
  );
  window.location.href = 'mailto:comercial@asafan.com.br?subject=' + subject + '&body=' + body;

  document.getElementById('contactSuccess').classList.add('show');
  form.reset();
  return false;
}

// Career form handler
function handleCareerForm(e) {
  e.preventDefault();
  var form = e.target;
  var data = new FormData(form);

  var subject = encodeURIComponent('Currículo - ' + data.get('nome') + ' - ' + data.get('cargo'));
  var body = encodeURIComponent(
    'Nome: ' + data.get('nome') + '\n' +
    'Data de Nascimento: ' + data.get('nascimento') + '\n' +
    'E-mail: ' + data.get('email') + '\n' +
    'Telefone: ' + data.get('telefone') + '\n' +
    'Cargo de Interesse: ' + data.get('cargo') + '\n' +
    'Pretensão Salarial: ' + (data.get('pretensao') || '-') + '\n\n' +
    'Experiência Profissional:\n' + data.get('experiencia') + '\n\n' +
    'Formação:\n' + data.get('formacao') + '\n\n' +
    'Informações Complementares:\n' + (data.get('complementares') || '-')
  );
  window.location.href = 'mailto:comercial@asafan.com.br?subject=' + subject + '&body=' + body;

  document.getElementById('careerSuccess').classList.add('show');
  form.reset();
  return false;
}
