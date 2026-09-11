document.addEventListener("DOMContentLoaded", function () {

  /* =========================================================
     SIDEBAR
     (mesmo comportamento do Kanban de Governança)
     ========================================================= */

  const sidebar = document.getElementById("sidebar");

  if (sidebar) {

    sidebar.addEventListener("mouseenter", function () {
      sidebar.classList.add("hover-expanded");
    });

    sidebar.addEventListener("mouseleave", function () {
      if (!sidebar.classList.contains("expanded")) {
        sidebar.classList.remove("hover-expanded");
      }
    });

  }


  /* =========================================================
     DEFINIR ETAPAS — ADICIONAR / REMOVER LINHAS
     ========================================================= */

  const etapasList = document.getElementById("etapasList");
  const addEtapaBtn = document.getElementById("addEtapaBtn");

  const iconRemoveSvg = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  `;


  function createEtapaRow() {

    const row = document.createElement("div");
    row.className = "etapa-row";

    row.innerHTML = `
      <input type="text" name="etapaNome[]" placeholder="Nome da etapa">

      <input type="text" name="etapaResponsavel[]" placeholder="Responsável">

      <input type="date" name="etapaInicio[]">

      <input type="date" name="etapaFim[]">

      <select name="etapaPrioridade[]">
        <option value="">Selecione a prioridade específica</option>
      </select>

      <button type="button" class="etapa-remove" aria-label="Remover etapa">
        ${iconRemoveSvg}
      </button>
    `;

    return row;
  }


  if (addEtapaBtn && etapasList) {

    addEtapaBtn.addEventListener("click", function () {

      const newRow = createEtapaRow();

      etapasList.appendChild(newRow);

    });

  }


  if (etapasList) {

    etapasList.addEventListener("click", function (event) {

      const removeBtn = event.target.closest(".etapa-remove");

      if (!removeBtn) {
        return;
      }

      const row = removeBtn.closest(".etapa-row");

      if (row) {
        row.remove();
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
