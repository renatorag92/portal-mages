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

  const iconRemoveSvg = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <polyline points="3 6 5 6 21 6"></polyline>
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
    </svg>
  `;

  const iconAddSvg = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
      <line x1="12" y1="5" x2="12" y2="19" />
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
        <option value="baixa">Baixa</option>
        <option value="media">Média</option>
        <option value="alta">Alta</option>
      </select>

      <div class="etapa-actions">
        <button type="button" class="etapa-remove" aria-label="Remover etapa">
          ${iconRemoveSvg}
        </button>

        <button type="button" class="etapa-add" aria-label="Adicionar etapa">
          ${iconAddSvg}
        </button>
      </div>
    `;

    return row;
  }


  if (etapasList) {

    etapasList.addEventListener("click", function (event) {

      const addBtn = event.target.closest(".etapa-add");
      const removeBtn = event.target.closest(".etapa-remove");

      // Adicionar nova linha
      if (addBtn) {
        event.preventDefault();
        event.stopPropagation();

        const newRow = createEtapaRow();
        etapasList.appendChild(newRow);
        etapasList.scrollTop = etapasList.scrollHeight;
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