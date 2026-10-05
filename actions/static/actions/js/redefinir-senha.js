const form = document.querySelector('form');

const antiga = form.querySelector('input[name="old_password"]');
const nova = form.querySelector('input[name="new_password1"]');
const confirmacao = form.querySelector('input[name="new_password2"]');
const campos = [antiga, nova, confirmacao];

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
  const msg = mensagemDe(campo);
  msg.hidden = true;
}

// Ao enviar: confere os campos antes de mandar para o servidor
form.addEventListener('submit', function (e) {
  campos.forEach(limparErro);
  const erros = []; // [campo, mensagem]

  if (!antiga.value) {
    erros.push([antiga, 'Preencha a senha antiga.']);
  }

  if (!nova.value) {
    erros.push([nova, 'Preencha a nova senha.']);
  } else if (nova.value.length < 8) {
    erros.push([nova, 'A nova senha precisa ter pelo menos 8 caracteres.']);
  } else if (/^\d+$/.test(nova.value)) {
    erros.push([nova, 'A nova senha não pode ser só números.']);
  } else if (antiga.value && nova.value === antiga.value) {
    erros.push([nova, 'A nova senha deve ser diferente da antiga.']);
  }

  if (!confirmacao.value) {
    erros.push([confirmacao, 'Confirme a nova senha.']);
  } else if (nova.value && confirmacao.value !== nova.value) {
    erros.push([confirmacao, 'As senhas não conferem.']);
  }

  if (erros.length === 0) return; // tudo certo: envia normalmente

  e.preventDefault();
  erros.forEach(function (item) { mostrarErro(item[0], item[1]); });
  erros[0][0].focus();
});

// Ao digitar em um campo, o erro dele some
campos.forEach(function (campo) {
  campo.addEventListener('input', function () { limparErro(campo); });
});