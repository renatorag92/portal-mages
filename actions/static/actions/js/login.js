const form = document.querySelector('form');
const campos = Array.from(form.querySelectorAll('input[name="contrato"], input[name="senha"]'));
const erro = document.getElementById('erro');

function limpar() {
    campos.forEach(function (c) {
    c.classList.remove('invalido');
    c.removeAttribute('aria-invalid');
    });
    erro.hidden = true;
}

form.addEventListener('submit', function (e) {
    const vazios = campos.filter(function (c) { return !c.value.trim(); });
    if (vazios.length === 0) return; // tudo preenchido: envia normalmente

    e.preventDefault();
    limpar();

    vazios.forEach(function (c) {
    c.classList.add('invalido');
    c.setAttribute('aria-invalid', 'true');
    });

    if (vazios.length === 2) {
    erro.textContent = 'Preencha o número do contrato e a senha.';
    } else if (vazios[0].name === 'contrato') {
    erro.textContent = 'Preencha o número do contrato.';
    } else {
    erro.textContent = 'Preencha a senha.';
    }
    erro.hidden = false;
    vazios[0].focus();
});

campos.forEach(function (c) {
    c.addEventListener('input', limpar);
});