/*
 * Kanban de Governança: arrastar cards, busca e filtro por eixo.
 *
 * Os detalhes da ação (pop-up) ficam no kanban-detalhes.js.
 * Os eventos usam delegação (ouvem o document), então cards inseridos depois
 * do carregamento da página funcionam sem reinicializar.
 */
document.addEventListener("DOMContentLoaded", function () {

  const eixoFilter = document.getElementById("eixoFilter");
  const searchInput = document.getElementById("actionSearch");

  function luminancia(rgb) {
    const canais = rgb.map(function (valor) {
      const canal = valor / 255;
      return canal <= 0.04045 ? canal / 12.92 : Math.pow((canal + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2];
  }

  function aplicarContrasteCabecalhos() {
    document.querySelectorAll(".column-header").forEach(function (header) {
      const cor = getComputedStyle(header).backgroundColor;
      const canais = cor.match(/[\d.]+/g);
      if (!canais || canais.length < 3) return;

      const rgb = canais.slice(0, 3).map(Number);
      const lumFundo = luminancia(rgb);
      const contrastePreto = (lumFundo + 0.05) / 0.05;
      const contrasteBranco = 1.05 / (lumFundo + 0.05);
      const usarBranco = contrasteBranco > contrastePreto;

      header.style.setProperty("--column-foreground", usarBranco ? "#fff" : "#000");
      header.style.setProperty("--column-foreground-rgb", usarBranco ? "255, 255, 255" : "0, 0, 0");
    });
  }

  const modalEdicaoStatus = document.getElementById("kanbanStatusEditModal");
  const formEdicaoStatus = document.getElementById("kanbanStatusEditForm");
  const campoNomeStatus = document.getElementById("kanbanStatusName");
  const campoCorStatus = document.getElementById("kanbanStatusColor");
  let botaoEdicaoStatusAtivo = null;

  function limparErrosEdicaoStatus() {
    modalEdicaoStatus.querySelectorAll("[data-error-for]").forEach(function (elemento) {
      elemento.textContent = "";
      elemento.hidden = true;
    });
    formEdicaoStatus.querySelectorAll("input").forEach(function (campo) {
      campo.removeAttribute("aria-invalid");
    });
  }

  function fecharModalEdicaoStatus() {
    modalEdicaoStatus.hidden = true;
    document.body.style.overflow = "";
    if (botaoEdicaoStatusAtivo) {
      botaoEdicaoStatusAtivo.focus();
      botaoEdicaoStatusAtivo = null;
    }
  }

  document.addEventListener("click", function (event) {
    const botao = event.target.closest && event.target.closest(".column-status-edit");
    if (!botao || !modalEdicaoStatus || !formEdicaoStatus) return;

    botaoEdicaoStatusAtivo = botao;
    formEdicaoStatus.action = botao.dataset.editUrl;
    campoNomeStatus.value = botao.dataset.statusName || "";
    campoCorStatus.value = botao.dataset.statusColor || "";
    limparErrosEdicaoStatus();
    modalEdicaoStatus.hidden = false;
    document.body.style.overflow = "hidden";
    campoNomeStatus.focus();
  });

  if (modalEdicaoStatus) {
    modalEdicaoStatus.querySelectorAll("[data-close-status-modal]").forEach(function (botao) {
      botao.addEventListener("click", fecharModalEdicaoStatus);
    });

    modalEdicaoStatus.addEventListener("click", function (event) {
      if (event.target === modalEdicaoStatus) fecharModalEdicaoStatus();
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !modalEdicaoStatus.hidden) {
        fecharModalEdicaoStatus();
      }
    });
  }

  if (formEdicaoStatus) {
    formEdicaoStatus.addEventListener("submit", async function (event) {
      event.preventDefault();
      limparErrosEdicaoStatus();

      const botaoSalvar = formEdicaoStatus.querySelector(".status-edit-save");
      const token = formEdicaoStatus.querySelector('[name="csrfmiddlewaretoken"]').value;
      botaoSalvar.disabled = true;

      try {
        const resposta = await fetch(formEdicaoStatus.action, {
          method: "POST",
          headers: { "X-CSRFToken": token },
          body: new FormData(formEdicaoStatus)
        });
        let dados;
        try {
          dados = await resposta.json();
        } catch (erro) {
          throw new Error("Não foi possível salvar o status. Tente novamente.");
        }

        if (!resposta.ok || !dados.success) {
          if (dados.errors) {
            Object.keys(dados.errors).forEach(function (campo) {
              const destino = modalEdicaoStatus.querySelector('[data-error-for="' + campo + '"]');
              if (!destino) return;
              destino.textContent = dados.errors[campo].join(" ");
              destino.hidden = false;
              const input = formEdicaoStatus.querySelector('[name="' + campo + '"]');
              if (input) input.setAttribute("aria-invalid", "true");
            });
          } else {
            throw new Error("Não foi possível salvar o status. Tente novamente.");
          }
          return;
        }

        window.location.reload();
      } catch (erro) {
        const erroGeral = modalEdicaoStatus.querySelector('[data-error-for="__all__"]');
        erroGeral.textContent = erro.message;
        erroGeral.hidden = false;
      } finally {
        botaoSalvar.disabled = false;
      }
    });
  }

  function normalizeText(text) {
    return String(text || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }


  /* =========================================================
     ALTERAÇÃO DE STATUS (arrastar o card para outra coluna)
     ========================================================= */

  // Ação já Cancelada é definitiva: não troca mais de status.
  function submitStatus(card, status) {
    if (!card || !status || card.closest(".col-cancelado")) return;

    const form = card.querySelector("form");
    const input = form && form.querySelector('input[name="status"]');
    if (!input) return;

    input.value = status;
    form.submit();
  }


  /* =========================================================
     DRAG AND DROP
     ========================================================= */

  let draggedCard = null;

  function columnBodyOf(event) {
    return event.target.closest ? event.target.closest(".column-body") : null;
  }

  document.addEventListener("dragstart", function (event) {
    const card = event.target.closest && event.target.closest(".task-card");
    if (!card) return;

    // Cards em Cancelado não podem ser arrastados
    if (card.closest(".col-cancelado")) {
      event.preventDefault();
      draggedCard = null;
      return;
    }

    draggedCard = card;
    card.classList.add("dragging");
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", "kanban-card");
  });

  document.addEventListener("click", async function (event) {
    const button = event.target.closest && event.target.closest("[data-confirm-status]");
    if (!button) return;

    const form = button.closest("form");
    if (!form) return;

    const nomeStatus = button.dataset.confirmStatus;
    const confirmar = window.confirmarSite;
    const confirmado = typeof confirmar === "function"
      ? await confirmar({
        titulo: "Excluir status?",
        texto: 'Tem certeza de que deseja excluir o status "' + nomeStatus + '"? Esta ação não pode ser desfeita.',
        sim: "Excluir",
        nao: "Cancelar"
      })
      : window.confirm('Tem certeza de que deseja excluir o status "' + nomeStatus + '"? Esta ação não pode ser desfeita.');

    if (!confirmado) return;
    button.disabled = true;
    const token = form.querySelector('[name="csrfmiddlewaretoken"]').value;
    try {
      const response = await fetch(form.action, {
        method: "POST",
        headers: { "X-CSRFToken": token }
      });
      let data;
      try {
        data = await response.json();
      } catch (erro) {
        throw new Error("Não foi possível excluir o status. Tente novamente.");
      }

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Não foi possível excluir o status.");
      }

      const column = button.closest(".column");
      if (column) column.remove();
      window.mostrarKanbanToast(data.message, "status-deleted");
    } catch (erro) {
      button.disabled = false;
      window.mostrarKanbanToast(erro.message, "error");
    }
  });

  document.addEventListener("dragend", function () {
    if (draggedCard) draggedCard.classList.remove("dragging");
    document.querySelectorAll(".column-body.drag-over").forEach(function (body) {
      body.classList.remove("drag-over");
    });
    draggedCard = null;
  });

  document.addEventListener("dragover", function (event) {
    const body = columnBodyOf(event);
    if (!body || !draggedCard) return;

    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    body.classList.add("drag-over");
  });

  document.addEventListener("dragleave", function (event) {
    const body = columnBodyOf(event);
    if (!body) return;
    if (event.relatedTarget && body.contains(event.relatedTarget)) return;
    body.classList.remove("drag-over");
  });

  document.addEventListener("drop", function (event) {
    const body = columnBodyOf(event);
    if (!body || !draggedCard) return;

    event.preventDefault();
    body.classList.remove("drag-over");
    submitStatus(draggedCard, body.dataset.status);
  });


  /* =========================================================
     BUSCA E FILTRO POR EIXO
     ========================================================= */

  function applyFilters() {
    const searchValue = normalizeText(searchInput ? searchInput.value : "");
    const eixoValue = normalizeText(eixoFilter ? eixoFilter.value : "");

    document.querySelectorAll(".task-card").forEach(function (card) {
      const matchesSearch =
        searchValue === "" || normalizeText(card.dataset.search).includes(searchValue);
      const matchesEixo =
        eixoValue === "" || normalizeText(card.dataset.eixo) === eixoValue;

      card.style.display = matchesSearch && matchesEixo ? "" : "none";
    });
  }

  // Lista no filtro os eixos que têm pelo menos uma ação no quadro
  function populateEixoFilter() {
    if (!eixoFilter) return;

    const selecionado = eixoFilter.value;
    while (eixoFilter.options.length > 1) eixoFilter.remove(1);

    const eixos = new Map();
    document.querySelectorAll(".task-card").forEach(function (card) {
      const eixo = String(card.dataset.eixo || "").trim();
      if (eixo && !eixos.has(normalizeText(eixo))) {
        eixos.set(normalizeText(eixo), eixo);
      }
    });

    Array.from(eixos.values())
      .sort(function (a, b) {
        return normalizeText(a).localeCompare(normalizeText(b), "pt-BR");
      })
      .forEach(function (eixo) {
        eixoFilter.add(new Option(eixo, eixo));
      });

    eixoFilter.value = selecionado;
  }

  if (searchInput) searchInput.addEventListener("input", applyFilters);
  if (eixoFilter) eixoFilter.addEventListener("change", applyFilters);

  aplicarContrasteCabecalhos();
  populateEixoFilter();
  applyFilters();

    /* =========================================================
     AVISO (TOAST) NO CANTO SUPERIOR DIREITO
     ========================================================= */

  const DURACAO_TOAST = 6000;

  function mostrarToast(mensagem, tipo) {
    let pilha = document.getElementById("kbToasts");
    if (!pilha) {
      pilha = document.createElement("div");
      pilha.id = "kbToasts";
      pilha.className = "status-messages kanban-status-messages";
      pilha.setAttribute("aria-live", "polite");
      document.body.appendChild(pilha);
    }

    const toast = document.createElement("div");
    const categoria = tipo || "success";
    toast.className = "status-message status-message-" + (
      categoria === "error" ? "error" : "success"
    );
    if (categoria.indexOf("status-") === 0) {
      toast.classList.add("status-message-" + categoria);
    }
    toast.setAttribute("role", "status");
    const icone = categoria === "status-updated"
      ? '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L8 18l-4 1 1-4Z"/>'
      : categoria === "status-deleted"
        ? '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m19 6-1 14H6L5 6"/><path d="M10 11v5M14 11v5"/>'
        : categoria === "error"
          ? '<circle cx="12" cy="12" r="9"/><path d="M12 8v4m0 4h.01"/>'
          : '<path d="m5 12 4 4L19 6"/>';
    toast.innerHTML =
      '<span class="status-message-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' + icone + '</svg></span>' +
      '<span class="status-message-text"></span>' +
      '<button type="button" class="status-message-close" aria-label="Fechar notificação">&times;</button>' +
      '<span class="status-message-progress" aria-hidden="true"></span>';
    toast.querySelector(".status-message-text").textContent = mensagem;
    pilha.appendChild(toast);

    const timer = setTimeout(fechar, DURACAO_TOAST);

    function fechar() {
      clearTimeout(timer);
      if (toast.classList.contains("is-leaving")) return;
      toast.classList.add("is-leaving");
      setTimeout(function () { toast.remove(); }, 200);
    }

    toast.querySelector(".status-message-close").addEventListener("click", fechar);
  }

  window.mostrarKanbanToast = mostrarToast;

  // Aviso enviado pelo servidor (ex.: depois de mover uma ação de status)
  const dadosToast = document.getElementById("kanban-toast");
  if (dadosToast) {
    try {
      const dados = JSON.parse(dadosToast.textContent);
      mostrarToast(dados.mensagem, dados.tipo);
    } catch (erro) { /* sem aviso, sem problema */ }
  }

});