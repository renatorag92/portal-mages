document.addEventListener('DOMContentLoaded', function () {
  /* =====================================================
     SIDEBAR
  ===================================================== */
  const sidebar = document.getElementById('sidebar');

  if (sidebar) {
    sidebar.addEventListener('mouseenter', function () {
      sidebar.classList.add('hover-expanded');
    });

    sidebar.addEventListener('mouseleave', function () {
      sidebar.classList.remove('hover-expanded');
    });
  }

  /* =====================================================
     DRAG AND DROP DO KANBAN
  ===================================================== */
  /*
   * Apenas cards que possuem draggable="true" podem ser arrastados.
   * Os cards da coluna "Cancelado" não possuem esse atributo.
   */
  const cards = document.querySelectorAll('.task-card[draggable="true"]');

  /*
   * Pegamos as colunas inteiras como área de drop para funcionar 
   * mesmo ao arrastar sobre o cabeçalho ou elementos internos.
   */
  const columns = document.querySelectorAll('.column');

  let draggedCard = null;

  /* =====================================================
     INÍCIO E FIM DO ARRASTE (CARDS)
  ===================================================== */
  cards.forEach(function (card) {
    card.addEventListener('dragstart', function (event) {
      /*
       * Segurança adicional: se por algum motivo um card cancelado 
       * receber draggable="true", impede o arraste.
       */
      const origemBody = card.closest('.column-body');

      if (origemBody && origemBody.dataset.status === 'cancelado') {
        event.preventDefault();
        draggedCard = null;
        return;
      }

      draggedCard = card;
      card.classList.add('dragging');

      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData(
        'text/plain',
        card.querySelector('.task-id')?.textContent || 'card'
      );
    });

    card.addEventListener('dragend', function () {
      card.classList.remove('dragging');

      // Remove o destaque de todas as colunas
      columns.forEach(function (column) {
        column.classList.remove('drag-over');
      });

      draggedCard = null;
    });
  });

  /* =====================================================
     ÁREAS DE DROP (COLUNAS)
  ===================================================== */
  columns.forEach(function (column) {
    /* --- DRAGENTER --- */
    column.addEventListener('dragenter', function (event) {
      event.preventDefault();

      if (!draggedCard) return;

      const columnBody = column.querySelector('.column-body');
      if (!columnBody || !columnBody.dataset.status) return;

      column.classList.add('drag-over');
    });

    /* --- DRAGOVER --- */
    column.addEventListener('dragover', function (event) {
      // Sem preventDefault() o navegador impede o drop
      event.preventDefault();

      if (!draggedCard) return;

      event.dataTransfer.dropEffect = 'move';

      const columnBody = column.querySelector('.column-body');
      if (!columnBody || !columnBody.dataset.status) return;

      column.classList.add('drag-over');
    });

    /* --- DRAGLEAVE --- */
    column.addEventListener('dragleave', function (event) {
      // Só remove o destaque quando o cursor realmente sair da coluna
      if (!column.contains(event.relatedTarget)) {
        column.classList.remove('drag-over');
      }
    });

    /* --- DROP --- */
    column.addEventListener('drop', function (event) {
      event.preventDefault();
      event.stopPropagation();

      column.classList.remove('drag-over');

      // 1. Verifica se existe card sendo arrastado
      if (!draggedCard) {
        console.warn('Nenhum card está sendo arrastado.');
        return;
      }

      // 2. Descobre a coluna e corpo de origem
      const origemBody = draggedCard.closest('.column-body');
      const origemColumn = draggedCard.closest('.column');

      // SEGURANÇA: ação cancelada não pode sair de Cancelado
      if (origemBody && origemBody.dataset.status === 'cancelado') {
        console.warn('Ação cancelada não pode ser movimentada.');
        return;
      }

      // 3. Descobre o corpo da coluna de destino e seu novo status
      const destinoBody = column.querySelector('.column-body');

      if (!destinoBody) {
        console.error('Não foi encontrado o .column-body da coluna.');
        return;
      }

      const novoStatus = destinoBody.dataset.status;

      if (!novoStatus) {
        console.error('A coluna de destino não possui data-status.');
        return;
      }

      // 4. Não faz nada se for a mesma coluna
      if (origemColumn === column) {
        return;
      }

      // 5. Encontra a URL para atualizar a ação
      const form = draggedCard.querySelector('form');
      let url = form ? form.action : draggedCard.dataset.updateUrl;

      if (!url) {
        console.error('URL de atualização não encontrada.');
        alert('Não foi possível encontrar a URL para atualizar esta ação.');
        return;
      }

      // 6. Obtém o CSRF Token
      const csrfInput =
        draggedCard.querySelector('input[name="csrfmiddlewaretoken"]') ||
        document.querySelector('input[name="csrfmiddlewaretoken"]');

      const csrfToken = csrfInput ? csrfInput.value : getCookie('csrftoken');

      if (!csrfToken) {
        console.error('Token CSRF não encontrado.');
        alert('Token CSRF não encontrado.');
        return;
      }

      // DEBUG LOGS
      console.log('=================================');
      console.log('Movendo ação');
      console.log('Status anterior:', origemBody?.dataset.status);
      console.log('Novo status:', novoStatus);
      console.log('URL:', url);
      console.log('=================================');

      // 7. Move visualmente o card
      destinoBody.appendChild(draggedCard);

      // 8. Envia alteração para o Django via Fetch API
      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: new URLSearchParams({
          status: novoStatus,
          csrfmiddlewaretoken: csrfToken,
        }),
      })
        .then(function (response) {
          console.log('Resposta do servidor:', response.status);

          if (!response.ok) {
            throw new Error('Erro HTTP ' + response.status);
          }

          return response;
        })
        .then(function () {
          console.log('Ação atualizada com sucesso!');
          // Recarrega a página para sincronizar contadores e estado do banco
          window.location.reload();
        })
        .catch(function (error) {
          console.error('Erro ao mover ação:', error);
          alert('Não foi possível mover a ação.');
          // Volta para o estado salvo no banco recarregando a página
          window.location.reload();
        });
    });
  });

  /* =====================================================
     FUNÇÃO AUXILIAR: OBTER CSRF DO COOKIE
  ===================================================== */
  function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');

      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();

        if (cookie.substring(0, name.length + 1) === name + '=') {
          cookieValue = decodeURIComponent(
            cookie.substring(name.length + 1)
          );
          break;
        }
      }
    }

    return cookieValue;
  }
});