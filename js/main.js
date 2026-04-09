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

// Product catalog filters
document.addEventListener('DOMContentLoaded', function() {
  var filterBtns = document.querySelectorAll('.filter-btn');
  if (!filterBtns.length) return;

  filterBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var group = btn.getAttribute('data-filter');
      // Toggle active within same group
      document.querySelectorAll('.filter-btn[data-filter="' + group + '"]').forEach(function(b) {
        b.classList.remove('active');
      });
      btn.classList.add('active');

      // Get active filters
      var tipo = document.querySelector('.filter-btn[data-filter="tipo"].active').getAttribute('data-value');
      var tensao = document.querySelector('.filter-btn[data-filter="tensao"].active').getAttribute('data-value');

      // Filter cards
      var cards = document.querySelectorAll('.product-card');
      var count = 0;
      cards.forEach(function(card) {
        var cardTipo = card.getAttribute('data-tipo') || '';
        var cardTensao = card.getAttribute('data-tensao') || '';
        var showTipo = tipo === 'all' || cardTipo === tipo;
        var showTensao = tensao === 'all' || cardTensao === tensao;
        if (showTipo && showTensao) {
          card.style.display = '';
          count++;
        } else {
          card.style.display = 'none';
        }
      });

      // Update count
      var countEl = document.querySelector('.catalog__count');
      if (countEl) countEl.textContent = count + ' produto(s) encontrado(s)';
    });
  });
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
