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

// Product catalog filters — two-tier tipo + contextual secondary filters
document.addEventListener('DOMContentLoaded', function() {
  var filterBtns = document.querySelectorAll('.filter-btn');
  if (!filterBtns.length) return;

  // Get currently active value for a filter name; only reads from visible groups.
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

  // Show/hide filter groups based on the current tipo.
  // A group without data-context is always visible.
  // A group with data-context="x y z" is visible if tipo is 'all' matches x/y/z... actually:
  // spec: groups show when the selected tipo is in their context list. When tipo='all',
  // only the primary Tipo group is shown (all secondary groups hidden since they don't apply globally).
  function syncGroupVisibility(tipo) {
    document.querySelectorAll('.filter-group[data-context]').forEach(function(g) {
      var ctx = g.getAttribute('data-context').split(/\s+/);
      var show = ctx.indexOf(tipo) >= 0;
      g.classList.toggle('is-hidden', !show);
      if (!show) {
        // Reset this group's active button to 'all' so hidden filters don't contribute
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
      // Toggle active within the same .filter-group (scope to the parent group so sibling
      // groups sharing a data-filter name — e.g. two "tensao" groups — don't interfere).
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

  // Initial state
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
    'Gênero: ' + data.get('genero') + '\n' +
    'Estado Civil: ' + (data.get('estado_civil') || '-') + '\n' +
    'CPF: ' + data.get('cpf') + '\n' +
    'Endereço: ' + data.get('endereco') + '\n' +
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
