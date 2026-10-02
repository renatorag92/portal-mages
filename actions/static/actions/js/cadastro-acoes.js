document.addEventListener("DOMContentLoaded", function () {

  /* Cor do texto dinâmica (cinza se padrão, preto se selecionado) */
  function atualizarCorCampo(campo) {
    if (!campo) return;
    if (campo.tagName === "SELECT") {
      if (campo.value === "") {
        campo.classList.add("placeholder-ativo");
      } else {
        campo.classList.remove("placeholder-ativo");
      }
    } else if (campo.type === "date") {
      campo.style.color = campo.value ? "var(--text-dark, #333)" : "#999";
    }
  }

  function inicializarCoresVazias() {
    document.querySelectorAll('select, input[type="date"]').forEach(campo => {
      atualizarCorCampo(campo);
    });
  }

  document.addEventListener("change", function (event) {
    if (event.target.tagName === "SELECT" || event.target.type === "date") {
      atualizarCorCampo(event.target);
    }
  });

  inicializarCoresVazias();

  /* Pesquisa e Dropdown */
  const selectEixo = document.getElementById("eixo");
  const acaoTexto = document.getElementById("acaoTexto");
  const customAcoesList = document.getElementById("customAcoesList");
  const selectAcao = document.getElementById("acao");
  const inputNovaAcao = document.getElementById("novaAcao");

  if (acaoTexto && selectAcao && customAcoesList) {
    const todasAsAcoes = Array.from(selectAcao.options);
    let acoesPermitidas = [];

    function atualizarAcoesPermitidas() {
      // Converte para String e remove espaços extras
      const eixoSelecionado = selectEixo && selectEixo.value ? String(selectEixo.value).trim() : "";

      acoesPermitidas = [];
      todasAsAcoes.forEach(opcao => {
        const val = opcao.value;
        // Pega o data-eixo e limpa espaços
        const eixoDaAcao = opcao.getAttribute("data-eixo") ? String(opcao.getAttribute("data-eixo")).trim() : "";

        if (val !== "outra" && !val.startsWith("divisor_")) {
          // Faz a comparação direta sem restrição de tipo estrito
          if (eixoSelecionado && eixoDaAcao === eixoSelecionado) {
            acoesPermitidas.push({ valor: val, rotulo: opcao.text });
          }
        }
      });
    }

    function renderizarLista(filtro = "") {
      if (!customAcoesList) return;

      // Limpa a lista atual
      customAcoesList.innerHTML = "";

      // Se não houver eixo selecionado, mostra o aviso
      if (!selectEixo || !selectEixo.value) {
        const li = document.createElement("li");
        li.textContent = "⚠️ Selecione um Eixo primeiro";
        li.style.color = "#888";
        li.style.padding = "10px";
        customAcoesList.appendChild(li);
        customAcoesList.style.display = "block";
        return;
      }

      const termo = filtro.toLowerCase().trim();

      // Cria cada item da lista suspensa (<li>) com base nas ações permitidas
      acoesPermitidas.forEach(acao => {
        if (acao.rotulo.toLowerCase().includes(termo) || acao.valor === "outra") {
          const li = document.createElement("li");
          li.textContent = acao.rotulo;
          li.style.padding = "8px 12px";
          li.style.cursor = "pointer";
          li.style.borderBottom = "1px solid #f0f0f0";

          // Ação ao clicar no item da lista
          li.addEventListener("click", function () {
            if (acaoTexto) acaoTexto.value = acao.rotulo; // Preenche o texto
            if (selectAcao) selectAcao.value = acao.valor; // Atualiza o <select> original
            customAcoesList.style.display = "none"; // Esconde a lista
            if (typeof sincronizarValores === "function") sincronizarValores();
          });

          customAcoesList.appendChild(li);
        }
      });

      // Mostra a lista final
      customAcoesList.style.display = "block";
    }

    if (selectEixo) {
      selectEixo.addEventListener("change", function () {
        // Atualiza a lista de ações com base no eixo escolhido
        atualizarAcoesPermitidas();

        // Limpa o texto da caixa de pesquisa
        if (acaoTexto) acaoTexto.value = "";

        // Reseta os valores e esconde a lista suspensa
        sincronizarValores();
        if (customAcoesList) customAcoesList.style.display = "none";
      });
    }

    if (acaoTexto) {
      // Quando o utilizador clica na caixa de texto -> Renderiza e abre a lista
      acaoTexto.addEventListener("click", function () {
        renderizarLista(this.value);
      });

      // Quando o utilizador digita algo na caixa de texto -> Filtra a lista em tempo real
      acaoTexto.addEventListener("input", function () {
        renderizarLista(this.value);
        sincronizarValores();
      });
    }

    // Oculta a lista suspensa se o utilizador clicar fora da caixa
    document.addEventListener("click", function (e) {
      if (customAcoesList && acaoTexto && !acaoTexto.contains(e.target) && !customAcoesList.contains(e.target)) {
        customAcoesList.style.display = "none";
      }
    });

  }
  /* Definir etapas - adicionar/remover linhas */
  const etapasList = document.getElementById("etapasList");
  if (etapasList) {
    etapasList.addEventListener("click", function (event) {
      const addBtn = event.target.closest(".etapa-add");
      const removeBtn = event.target.closest(".etapa-remove");

      if (addBtn) {
        event.preventDefault();
        event.stopPropagation();
        const firstRow = etapasList.querySelector(".etapa-row");
        if (firstRow) {
          const newRow = firstRow.cloneNode(true);

          newRow.querySelectorAll("input").forEach(input => {
            input.value = "";
            if (input.type === "date") input.style.color = "#999";
          });
          newRow.querySelectorAll("select").forEach(select => {
            select.selectedIndex = 0;
            select.classList.add("placeholder-ativo");
          });

          etapasList.appendChild(newRow);
          etapasList.scrollTop = etapasList.scrollHeight;
        }
        return;
      }

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

  /* Envio e cancelamento do formulário (Django Fetch + Validações) */
  const form = document.getElementById("formCadastroAcao");
  const cancelarBtn = document.getElementById("cancelarBtn");

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();

      const eixo = document.getElementById("eixo").value;
      const acao = selectAcao ? selectAcao.value : "";
      const acaoTextoVal = acaoTexto ? acaoTexto.value.trim() : "";
      const prioridade = document.getElementById("prioridade").value;
      const custo = document.getElementById("custo").value;
      const dataInicio = document.getElementById("dataInicio").value;
      const dataFim = document.getElementById("dataFim").value;
      const observacoes = document.getElementById("observacoes").value;

      if (!eixo || !acaoTextoVal || !prioridade || !custo || !dataInicio || !dataFim) {
        alert("Por favor, preencha todos os campos obrigatórios marcados com asterisco (*) antes de salvar.");
        return;
      }

      let etapasValidas = true;
      const etapasRows = document.querySelectorAll(".etapa-row");
      const etapasData = [];

      etapasRows.forEach((row) => {
        const nomeEtapa = row.querySelector("input[name='etapaNome[]']").value;
        const cpfEtapa = row.querySelector("input[name='etapaResponsavelCpf[]']").value;
        const inicioEtapa = row.querySelector("input[name='etapaInicio[]']").value;
        const fimEtapa = row.querySelector("input[name='etapaFim[]']").value;
        const prioridadeEtapa = row.querySelector("select[name='etapaPrioridade[]']").value;
        const obsEtapa = row.querySelector("input[name='etapaObservacoes[]']").value;

        if (nomeEtapa || cpfEtapa || inicioEtapa || fimEtapa || prioridadeEtapa || obsEtapa) {
          if (!nomeEtapa || !cpfEtapa || !inicioEtapa || !fimEtapa || !prioridadeEtapa) {
            etapasValidas = false;
          } else {
            etapasData.push({
              nome: nomeEtapa,
              cpf: cpfEtapa,
              inicio: inicioEtapa,
              fim: fimEtapa,
              prioridade: prioridadeEtapa,
              observacoes: obsEtapa
            });
          }
        }
      });

      if (!etapasValidas) {
        alert("Preencha todos os campos obrigatórios de cada etapa iniciada.");
        return;
      }

      let custoTratado = custo.replace(/\./g, "").replace(",", ".");    /* Tratamento do custo para o padrão que o Django aceita (ex: 23.22) */

      const dadosFormulario = {
        eixo: eixo,
        acao: acao,
        nova_acao_texto: acaoTextoVal,
        prioridade: prioridade,
        custo: custoTratado,
        dataInicio: dataInicio,
        dataFim: dataFim,
        observacoes: observacoes,
        etapas: etapasData,
        status: "planejado"
      };

      const csrftoken = getCookie('csrftoken');

      fetch(window.location.href, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken
        },
        body: JSON.stringify(dadosFormulario)
      })
        .then(response => {
          if (response.ok) {
            alert("Ação cadastrada com sucesso!");
            form.reset();
            if (selectEixo) selectEixo.dispatchEvent(new Event("change"));
            inicializarCoresVazias();
          } else {
            alert("Ocorreu um erro ao guardar a ação. Verifique os dados introduzidos.");
          }
        })
        .catch(error => {
          console.error("Erro na requisição:", error);
          alert("Erro de ligação com o servidor.");
        });
    });
  }

  if (cancelarBtn) {
    cancelarBtn.addEventListener("click", function () {
      const confirmar = confirm("Pretende cancelar o cadastro da ação?");
      if (confirmar) {
        if (form) {
          form.reset();
          if (selectEixo) selectEixo.dispatchEvent(new Event("change"));
          inicializarCoresVazias();
        }
      }
    });
  }

  /* Máscaras automáticas para CPF e Custo */
  const etapasListContainer = document.getElementById("etapasList");
  if (etapasListContainer) {
    etapasListContainer.addEventListener("input", function (e) {
      if (e.target && e.target.name === "etapaResponsavelCpf[]") {    /* Verifica se o input que está recebendo texto é um CPF de etapa */
        let value = e.target.value.replace(/\D/g, "");
        if (value.length > 11) value = value.slice(0, 11);

        if (value.length > 9) {
          value = value.replace(/^(\d{3})(\d{3})(\d{3})(\d{1,2})$/, "$1.$2.$3-$4");
        } else if (value.length > 6) {
          value = value.replace(/^(\d{3})(\d{3})(\d{1,3})$/, "$1.$2.$3");
        } else if (value.length > 3) {
          value = value.replace(/^(\d{3})(\d{1,3})$/, "$1.$2");
        }
        e.target.value = value;
      }
    });
  }

  const inputCusto = document.getElementById("custo");
  if (inputCusto) {   /* Garante que o input seja do tipo texto para aceitar formatação visual */
    if (inputCusto.type === "number") {
      inputCusto.type = "text";
    }

    inputCusto.addEventListener("input", function (e) {
      let value = e.target.value.replace(/\D/g, "");

      if (!value) {
        e.target.value = "";
        return;
      }

      /* Converte para formato decimal e formata em BRL */
      let numero = (parseInt(value, 10) / 100).toFixed(2);
      let partes = numero.split(".");
      let inteiro = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
      let decimal = partes[1];

      e.target.value = inteiro + "," + decimal;
    });
  }
});

