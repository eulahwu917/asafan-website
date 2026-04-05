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
