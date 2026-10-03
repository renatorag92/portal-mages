const form = document.querySelector('form');

const contrato = form.querySelector('input[name="contrato"]');
const senha = form.querySelector('input[name="senha"]');
const campos = [contrato, senha];

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
  if (!contrato.value.trim()) erros.push([contrato, 'Preencha o número do contrato.']);
  if (!senha.value) erros.push([senha, 'Preencha a senha.']);

  if (erros.length === 0) return; // tudo preenchido: envia normalmente

  e.preventDefault();
  erros.forEach(function (item) { mostrarErro(item[0], item[1]); });
  erros[0][0].focus();
});

// Ao digitar em um campo, o vermelho some só dele
campos.forEach(function (campo) {
  campo.addEventListener('input', function () { limparErro(campo); });
});