/*
 * Dashboard: troca os painéis da distribuição (visão geral, por eixo e por prazo).
 * Os números já vêm prontos do servidor.
 */
document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll("[data-gradiente]").forEach(function (el) {
    el.style.background = el.dataset.gradiente;
    });
    document.querySelectorAll("[data-cor]").forEach(function (el) {
        el.style.background = el.dataset.cor;
    });
    document.querySelectorAll("[data-largura]").forEach(function (el) {
        el.style.width = el.dataset.largura + "%";
    });

  const abas = document.querySelectorAll(".dash-abas:not(.dash-prazo-abas) .dash-aba");
  const paineis = document.querySelectorAll(".dash-painel");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      const chave = aba.dataset.aba;

      abas.forEach(function (a) {
        const ativa = a === aba;
        a.classList.toggle("ativa", ativa);
        a.setAttribute("aria-selected", String(ativa));
      });

      paineis.forEach(function (painel) {
        painel.classList.toggle("ativo", painel.dataset.painel === chave);
      });
    });
  });

  const abasPrazo = document.querySelectorAll(".dash-prazo-abas .dash-aba");
  const paineisPrazo = document.querySelectorAll(".dash-prazo-painel");
  const subtitulosPrazo = document.querySelectorAll("[data-prazo-subtitulo]");

  abasPrazo.forEach(function (aba) {
    aba.addEventListener("click", function () {
      const prazo = aba.dataset.prazoAba;

      abasPrazo.forEach(function (outraAba) {
        const ativa = outraAba === aba;
        outraAba.classList.toggle("ativa", ativa);
        outraAba.setAttribute("aria-selected", String(ativa));
        outraAba.tabIndex = ativa ? 0 : -1;
      });

      paineisPrazo.forEach(function (painel) {
        painel.hidden = painel.id !== aba.getAttribute("aria-controls");
      });
      subtitulosPrazo.forEach(function (subtitulo) {
        subtitulo.hidden = subtitulo.dataset.prazoSubtitulo !== prazo;
      });
    });
  });

});