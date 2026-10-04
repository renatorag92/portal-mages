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

  // O pop-up de cadastro dispara este evento depois de inserir um card novo
  document.addEventListener("kanban:card-added", function () {
    populateEixoFilter();
    applyFilters();
  });

  populateEixoFilter();
  applyFilters();

    /* =========================================================
     AVISO (TOAST) NO CANTO SUPERIOR DIREITO
     ========================================================= */

  const DURACAO_TOAST = 4000; // milissegundos

  function mostrarToast(mensagem) {
    let pilha = document.getElementById("kbToasts");
    if (!pilha) {
      pilha = document.createElement("div");
      pilha.id = "kbToasts";
      pilha.className = "kb-toasts";
      pilha.setAttribute("aria-live", "polite");
      document.body.appendChild(pilha);
    }

    const toast = document.createElement("div");
    toast.className = "kb-toast";
    toast.setAttribute("role", "status");
    toast.style.setProperty("--kb-toast-duracao", DURACAO_TOAST + "ms");
    toast.innerHTML =
      '<span class="kb-toast-icone"><i class="bi bi-check-lg"></i></span>' +
      '<p class="kb-toast-texto"></p>' +
      '<button type="button" class="kb-toast-fechar" aria-label="Fechar aviso"><i class="bi bi-x-lg"></i></button>' +
      '<span class="kb-toast-barra"></span>';
    toast.querySelector(".kb-toast-texto").textContent = mensagem;
    pilha.appendChild(toast);

    const timer = setTimeout(fechar, DURACAO_TOAST);

    function fechar() {
      clearTimeout(timer);
      if (toast.classList.contains("saindo")) return;
      toast.classList.add("saindo");
      setTimeout(function () { toast.remove(); }, 200);
    }

    toast.querySelector(".kb-toast-fechar").addEventListener("click", fechar);
  }

  // Aviso enviado pelo servidor (ex.: depois de mover uma ação de status)
  const dadosToast = document.getElementById("kanban-toast");
  if (dadosToast) {
    try {
      mostrarToast(JSON.parse(dadosToast.textContent).mensagem);
    } catch (erro) { /* sem aviso, sem problema */ }
  }

});