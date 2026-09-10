document.addEventListener("DOMContentLoaded", function () {

  /* =========================================================
     SIDEBAR
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
     MENU DE DETALHES DA AÇÃO
     ========================================================= */

  const menuButtons = document.querySelectorAll(".status-menu-toggle");

  function closeAllMenus(exceptCard = null) {

    document.querySelectorAll(".task-card.menu-open").forEach(function (card) {

      if (card !== exceptCard) {

        card.classList.remove("menu-open");

        const menu = card.querySelector(".action-menu");

        if (menu) {
          menu.classList.remove("open");
        }

      }

    });

  }


  function positionActionMenu(card, menu, button) {

    const buttonRect = button.getBoundingClientRect();

    const menuWidth = 330;
    const menuHeight = menu.offsetHeight;

    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let left = buttonRect.right + 10;
    let top = buttonRect.top;

    if (left + menuWidth > viewportWidth - 10) {
      left = buttonRect.left - menuWidth - 10;
    }

    if (left < 10) {
      left = 10;
    }

    if (top + menuHeight > viewportHeight - 10) {
      top = viewportHeight - menuHeight - 10;
    }

    if (top < 10) {
      top = 10;
    }

    menu.style.left = `${left}px`;
    menu.style.top = `${top}px`;
  }


  menuButtons.forEach(function (button) {

    button.addEventListener("click", function (event) {

      event.stopPropagation();

      const card = button.closest(".task-card");
      const menu = card.querySelector(".action-menu");

      if (!menu) {
        return;
      }

      const alreadyOpen = card.classList.contains("menu-open");

      closeAllMenus(card);

      if (alreadyOpen) {

        card.classList.remove("menu-open");
        menu.classList.remove("open");

        return;
      }

      card.classList.add("menu-open");
      menu.classList.add("open");

      positionActionMenu(card, menu, button);

    });

  });


  document.addEventListener("click", function (event) {

    if (
      !event.target.closest(".action-menu") &&
      !event.target.closest(".status-menu-toggle")
    ) {
      closeAllMenus();
    }

  });


  window.addEventListener("resize", function () {

    document.querySelectorAll(".task-card.menu-open").forEach(function (card) {

      const menu = card.querySelector(".action-menu");
      const button = card.querySelector(".status-menu-toggle");

      if (menu && button && menu.classList.contains("open")) {
        positionActionMenu(card, menu, button);
      }

    });

  });


  window.addEventListener("scroll", function () {

    document.querySelectorAll(".task-card.menu-open").forEach(function (card) {

      const menu = card.querySelector(".action-menu");
      const button = card.querySelector(".status-menu-toggle");

      if (menu && button && menu.classList.contains("open")) {
        positionActionMenu(card, menu, button);
      }

    });

  }, true);


  /* =========================================================
     ALTERAÇÃO DE STATUS
     ========================================================= */

  const statusOptions = document.querySelectorAll(".status-option");

  statusOptions.forEach(function (option) {

    option.addEventListener("click", function (event) {

      event.preventDefault();
      event.stopPropagation();

      const card = option.closest(".task-card");

      if (!card) {
        return;
      }

      /*
       * Ação cancelada é definitiva.
       * Não existe formulário de alteração dentro dela.
       */
      if (card.closest(".column")?.classList.contains("col-cancelado")) {
        return;
      }

      const status = option.dataset.status;

      const form = card.querySelector("form");

      if (!form || !status) {
        return;
      }

      const statusInput = form.querySelector('input[name="status"]');

      if (!statusInput) {
        return;
      }

      statusInput.value = status;

      form.submit();

    });

  });


  /* =========================================================
     DRAG AND DROP
     ========================================================= */

  let draggedCard = null;

  const taskCards = document.querySelectorAll(".task-card");

  taskCards.forEach(function (card) {

    /*
     * Cards da coluna Cancelado não podem ser arrastados.
     */
    const isCancelled = card.closest(".col-cancelado");

    if (isCancelled) {

      card.setAttribute("draggable", "false");
      card.classList.remove("dragging");

      return;
    }


    card.addEventListener("dragstart", function (event) {

      if (card.closest(".col-cancelado")) {
        event.preventDefault();
        return;
      }

      draggedCard = card;

      card.classList.add("dragging");

      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", "kanban-card");

    });


    card.addEventListener("dragend", function () {

      card.classList.remove("dragging");

      document.querySelectorAll(".column-body").forEach(function (body) {
        body.classList.remove("drag-over");
      });

      draggedCard = null;

    });

  });


  const columnBodies = document.querySelectorAll(".column-body");

  columnBodies.forEach(function (body) {

    body.addEventListener("dragover", function (event) {

      if (!draggedCard) {
        return;
      }

      /*
       * Nunca permitir drop em Cancelado.
       */
      if (body.dataset.status === "cancelado") {
        event.preventDefault();
        event.dataTransfer.dropEffect = "none";
        return;
      }

      event.preventDefault();

      event.dataTransfer.dropEffect = "move";

      body.classList.add("drag-over");

    });


    body.addEventListener("dragleave", function (event) {

      if (
        event.relatedTarget &&
        body.contains(event.relatedTarget)
      ) {
        return;
      }

      body.classList.remove("drag-over");

    });


    body.addEventListener("drop", function (event) {

      event.preventDefault();

      body.classList.remove("drag-over");

      if (!draggedCard) {
        return;
      }

      /*
       * Não permitir mover ação cancelada.
       */
      if (draggedCard.closest(".col-cancelado")) {
        return;
      }

      /*
       * Não permitir colocar nenhuma ação em Cancelado
       * pelo drag and drop.
       *
       * O cancelamento continua sendo feito pelo menu
       * de alteração de status.
       */
      if (body.dataset.status === "cancelado") {
        return;
      }

      const newStatus = body.dataset.status;

      if (!newStatus) {
        return;
      }

      const form = draggedCard.querySelector("form");

      if (!form) {
        return;
      }

      const statusInput = form.querySelector('input[name="status"]');

      if (!statusInput) {
        return;
      }

      statusInput.value = newStatus;

      form.submit();

    });

  });


  /* =========================================================
     BUSCA DE AÇÃO
     ========================================================= */

  const searchInput = document.getElementById("actionSearch");

  /*
   * Normaliza o texto para facilitar a busca.
   *
   * Exemplo:
   * "AÇÃO 123" também pode ser encontrado digitando "acao 123".
   */
  function normalizeText(text) {

    return String(text || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();

  }


  function applyFilters() {

    const searchValue = normalizeText(
      searchInput ? searchInput.value : ""
    );

    const eixoValue = eixoFilter
      ? normalizeText(eixoFilter.value)
      : "";


    document.querySelectorAll(".column").forEach(function (column) {

      const cards = column.querySelectorAll(".task-card");

      cards.forEach(function (card) {

        const searchData = normalizeText(
          card.dataset.search
        );

        const cardEixo = normalizeText(
          card.dataset.eixo
        );


        const matchesSearch =
          searchValue === "" ||
          searchData.includes(searchValue);


        const matchesEixo =
          eixoValue === "" ||
          cardEixo === eixoValue;


        if (matchesSearch && matchesEixo) {

          card.style.display = "";

        } else {

          card.style.display = "none";

        }

      });

    });

  }


  if (searchInput) {

    searchInput.addEventListener("input", function () {
      applyFilters();
    });

  }


  /* =========================================================
     FILTRO POR EIXO
     ========================================================= */

  const eixoFilter = document.getElementById("eixoFilter");


  function populateEixoFilter() {

    if (!eixoFilter) {
      return;
    }

    const eixos = new Map();

    document.querySelectorAll(".task-card").forEach(function (card) {

      const eixo = card.dataset.eixo;

      if (!eixo) {
        return;
      }

      const value = String(eixo).trim();

      if (!value) {
        return;
      }

      const normalized = normalizeText(value);

      if (!eixos.has(normalized)) {
        eixos.set(normalized, value);
      }

    });


    const sortedEixos = Array.from(eixos.values()).sort(function (a, b) {

      return normalizeText(a).localeCompare(
        normalizeText(b),
        "pt-BR"
      );

    });


    sortedEixos.forEach(function (eixo) {

      const option = document.createElement("option");

      option.value = eixo;
      option.textContent = eixo;

      eixoFilter.appendChild(option);

    });

  }


  if (eixoFilter) {

    eixoFilter.addEventListener("change", function () {
      applyFilters();
    });

  }


  populateEixoFilter();


  /* =========================================================
     ATUALIZAÇÃO INICIAL DOS FILTROS
     ========================================================= */

  applyFilters();

});