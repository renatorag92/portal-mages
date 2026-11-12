const form = document.querySelector('form');

const contrato = form.querySelector('input[name="contrato"]');
const senha = form.querySelector('input[name="senha"]');
const campos = [contrato, senha];
const forgotPasswordForm = document.getElementById('forgotPasswordForm');
const forgotPasswordCpf = document.getElementById('forgotPasswordCpf');
const forgotPasswordError = document.getElementById('erro-solicitacao-cpf');
const forgotPasswordLink = document.getElementById('forgotPasswordLink');

function mensagemDe(campo) {
  return document.getElementById('erro-' + campo.name);
}

function mostrarErro(campo, texto) {
  campo.classList.add('invalido');
  campo.setAttribute('aria-invalid', 'true');
  const msg = mensagemDe(campo);
  msg.textContent = texto;
  msg.hidden = false;
}

function limparErro(campo) {
  campo.classList.remove('invalido');
  campo.removeAttribute('aria-invalid');
  mensagemDe(campo).hidden = true;
}

// Ao enviar: se tiver campo vazio, não envia e mostra o aviso embaixo do campo
form.addEventListener('submit', function (e) {
  campos.forEach(limparErro);

  const erros = []; // [campo, mensagem]
  if (!contrato.value.trim()) erros.push([contrato, 'Digite o CPF.']);
  if (!senha.value) erros.push([senha, 'Digite a senha.']);

  if (erros.length === 0) return; // tudo preenchido: envia normalmente

  e.preventDefault();
  erros.forEach(function (item) { mostrarErro(item[0], item[1]); });
  erros[0][0].focus();
});

// Ao digitar em um campo, o vermelho some só dele
campos.forEach(function (campo) {
  campo.addEventListener('input', function () { limparErro(campo); });
});

// Máscara de CPF enquanto digita: 123.456.789-09
contrato.addEventListener('input', function () {
  contrato.value = contrato.value
    .replace(/\D/g, '')
    .slice(0, 11)
    .replace(/^(\d{3})(\d)/, '$1.$2')
    .replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1-$2');
  if (contrato.value.replace(/\D/g, '').length === 11) {
    forgotPasswordError.hidden = true;
  }
});

forgotPasswordLink.addEventListener('click', function (event) {
  event.preventDefault();
  const cpf = contrato.value.replace(/\D/g, '');
  if (cpf.length !== 11) {
    forgotPasswordError.hidden = false;
    contrato.classList.add('invalido');
    contrato.setAttribute('aria-invalid', 'true');
    contrato.focus();
    return;
  }
  forgotPasswordCpf.value = cpf;
  forgotPasswordForm.submit();
});