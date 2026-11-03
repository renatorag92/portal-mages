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

  const abas = document.querySelectorAll(".dash-aba");
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

});