document.addEventListener("DOMContentLoaded", function () {

  /* =========================================================
     DEFINIR ETAPAS — ADICIONAR / REMOVER LINHAS
     ========================================================= */

  const etapasList = document.getElementById("etapasList");

  if (etapasList) {

    etapasList.addEventListener("click", function (event) {

      const addBtn = event.target.closest(".etapa-add");
      const removeBtn = event.target.closest(".etapa-remove");

      // Adicionar nova linha clonando a primeira para preservar o template do Django
      if (addBtn) {
        event.preventDefault();
        event.stopPropagation();

        const firstRow = etapasList.querySelector(".etapa-row");
        if (firstRow) {
          const newRow = firstRow.cloneNode(true);

          // Limpa os valores dos inputs e reseta o select
          newRow.querySelectorAll("input").forEach(input => input.value = "");
          newRow.querySelectorAll("select").forEach(select => select.selectedIndex = 0);

          etapasList.appendChild(newRow);
          etapasList.scrollTop = etapasList.scrollHeight;
        }
        return;
      }

      // Remover exatamente a linha clicada
      if (removeBtn) {
        event.preventDefault();
        event.stopPropagation();

        const rows = etapasList.querySelectorAll(".etapa-row");
        if (rows.length > 1) {
          const rowToRemove = removeBtn.closest(".etapa-row");
          if (rowToRemove) {
            rowToRemove.remove();
          }
        }
      }

    });

  }


  /* =========================================================
     ENVIO E CANCELAMENTO DO FORMULÁRIO
     ========================================================= */

  const form = document.getElementById("formCadastroAcao");
  const cancelarBtn = document.getElementById("cancelarBtn");

  if (form) {

    form.addEventListener("submit", function (event) {

      event.preventDefault();

      // Ponto de integração: enviar os dados do formulário
      // para o backend responsável pelo cadastro da ação.
      alert("Ação cadastrada com sucesso!");

    });

  }

  if (cancelarBtn) {

    cancelarBtn.addEventListener("click", function () {

      if (form) {
        form.reset();
      }

      // Ponto de integração: redirecionar de volta para o
      // Kanban de Governança ou fechar o formulário.

    });

  }

});