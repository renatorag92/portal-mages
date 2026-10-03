/*
 * Kanban de Governança
 *
 * Os eventos usam delegação (ouvem o document), então cards inseridos depois
 * do carregamento da página (pelo pop-up de cadastro) funcionam sem reinicializar.
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
     MENU DE DETALHES DA AÇÃO
     ========================================================= */

  function positionActionMenu(menu, button) {
    const rect = button.getBoundingClientRect();
    const menuWidth = 330;
    const menuHeight = menu.offsetHeight;

    let left = rect.right + 10;
    let top = rect.top;

    // Sem espaço à direita: abre para a esquerda
    if (left + menuWidth > window.innerWidth - 10) {
      left = rect.left - menuWidth - 10;
    }
    if (left < 10) left = 10;

    // Não deixa sair por baixo nem por cima
    if (top + menuHeight > window.innerHeight - 10) {
      top = window.innerHeight - menuHeight - 10;
    }
    if (top < 10) top = 10;

    menu.style.left = left + "px";
    menu.style.top = top + "px";
  }

  function closeAllMenus(exceptCard) {
    document.querySelectorAll(".task-card.menu-open").forEach(function (card) {
      if (card === exceptCard) return;
      card.classList.remove("menu-open");
      const menu = card.querySelector(".action-menu");
      if (menu) menu.classList.remove("open");
    });
  }

  function repositionOpenMenus() {
    document.querySelectorAll(".task-card.menu-open").forEach(function (card) {
      const menu = card.querySelector(".action-menu");
      const button = card.querySelector(".status-menu-toggle");
      if (menu && button && menu.classList.contains("open")) {
        positionActionMenu(menu, button);
      }
    });
  }

  window.addEventListener("resize", repositionOpenMenus);
  window.addEventListener("scroll", repositionOpenMenus, true);


  /* =========================================================
     ALTERAÇÃO DE STATUS (botões do menu e drag and drop)
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

  document.addEventListener("click", function (event) {

    // Abrir/fechar o menu de detalhes
    const toggle = event.target.closest(".status-menu-toggle");
    if (toggle) {
      const card = toggle.closest(".task-card");
      const menu = card && card.querySelector(".action-menu");
      if (!menu) return;

      const wasOpen = card.classList.contains("menu-open");
      closeAllMenus(card);
      card.classList.toggle("menu-open", !wasOpen);
      menu.classList.toggle("open", !wasOpen);
      if (!wasOpen) positionActionMenu(menu, toggle);
      return;
    }

    // Botões "Alterar status"
    const option = event.target.closest(".status-option");
    if (option) {
      event.preventDefault();
      submitStatus(option.closest(".task-card"), option.dataset.status);
      return;
    }

    // Clique fora do menu fecha todos
    if (!event.target.closest(".action-menu")) {
      closeAllMenus();
    }
  });


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

  // O pop-up dispara este evento depois de inserir um card novo
  document.addEventListener("kanban:card-added", function () {
    populateEixoFilter();
    applyFilters();
  });

  populateEixoFilter();
  applyFilters();

});

document.addEventListener('change', function(event) {
  if (event.target.classList.contains('etapa-check-btn')) {
    const etapaId = event.target.dataset.etapaId;
    const isChecked = event.target.checked;
    
    fetch(`/actions/etapa/${etapaId}/alterar/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
      }
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        const titulo = event.target.nextElementSibling;
        if (titulo) {
          titulo.style.textDecoration = data.concluida ? 'line-through' : 'none';
          titulo.style.color = data.concluida ? '#888' : 'inherit';
        }
      }
    });
  }
});