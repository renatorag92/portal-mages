/*
 * Pop-up de detalhes da ação (Kanban)
 *
 * Esquerda: dados da ação (botão "Editar ação").
 * Direita:  etapas da ação (botão "Editar etapa" em cada uma e caixa de concluída).
 * Os dados vêm do servidor em JSON, e o pop-up é desenhado aqui.
 */
document.addEventListener("DOMContentLoaded", function () {

  const overlay = document.getElementById("detOverlay");
  if (!overlay) return;

  // Move o pop-up para o <body>, assim nenhum container do layout limita o position: fixed
  document.body.appendChild(overlay);

  const $ = function (id) { return document.getElementById(id); };

  const elTitulo = $("detTitulo");
  const elSubtitulo = $("detSubtitulo");
  const elBadge = $("detBadge");
  const elAcao = $("detAcao");
  const elEtapas = $("detEtapas");
  const elRodape = $("detStatus");

  const urls = {
    detalhes: overlay.dataset.urlDetalhes,
    editarAcao: overlay.dataset.urlEditarAcao,
    editarEtapa: overlay.dataset.urlEditarEtapa,
    concluirEtapa: overlay.dataset.urlConcluirEtapa
  };

  let codigoAberto = null;
  // estado = { acao, etapas, prioridades, editandoAcao, editandoEtapa }
  let estado = null;


  /* =========================================================
     UTILITÁRIOS
     ========================================================= */

  // As rotas chegam com 0 no lugar do id (/kanban/acao/0/...), trocamos pelo id real
  function urlDe(base, id) {
    return base.replace("/0/", "/" + id + "/");
  }

  function csrf() {
    const campo = document.querySelector('[name="csrfmiddlewaretoken"]');
    return campo ? campo.value : "";
  }

  function esc(texto) {
    return String(texto == null ? "" : texto).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function norm(texto) {
    return String(texto || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function fmtData(iso) {
    if (!iso) return "Não informado";
    const partes = iso.split("-");
    return partes[2] + "/" + partes[1] + "/" + partes[0];
  }

  function fmtCusto(numero) {
    return Number(numero).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }

  function fmtCustoCampo(numero) {
    return Number(numero).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function mascaraCpf(valor) {
    return String(valor || "")
      .replace(/\D/g, "")
      .slice(0, 11)
      .replace(/^(\d{3})(\d)/, "$1.$2")
      .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1-$2");
  }

  function mascaraCusto(valor) {
    const digitos = String(valor || "").replace(/\D/g, "");
    if (!digitos) return "";
    const partes = (parseInt(digitos, 10) / 100).toFixed(2).split(".");
    return partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + partes[1];
  }

  async function pedir(url, opcoes) {
    const resposta = await fetch(url, opcoes);
    const json = await resposta.json().catch(function () { return null; });
    if (!resposta.ok || !json || !json.success) {
      throw new Error((json && json.error) || "Não foi possível concluir a operação.");
    }
    return json;
  }

  function mostrarErro(caixa, mensagem) {
    caixa.textContent = mensagem;
    caixa.hidden = false;
  }


  /* =========================================================
     PEÇAS DE HTML
     ========================================================= */

  function item(rotulo, valor, cheio) {
    return '<div class="det-item' + (cheio ? " full" : "") + '"><dt>' + rotulo + "</dt><dd>" + valor + "</dd></div>";
  }

  function campo(id, rotulo, obrigatorio, controle, cheio) {
    return '<div class="det-item' + (cheio ? " full" : "") + '">' +
      '<dt><label for="' + id + '">' + rotulo + (obrigatorio ? ' <span class="det-req">*</span>' : "") + "</label></dt>" +
      "<dd>" + controle + "</dd></div>";
  }

  function vazio(texto) {
    return '<span class="det-vazio-inline">' + texto + "</span>";
  }

  function chipPrioridade(prioridade) {
    if (!prioridade) return vazio("Não informada");
    return '<span class="det-chip det-chip-' + norm(prioridade) + '">' + esc(prioridade) + "</span>";
  }

  function opcoesPrioridade(selecionada) {
    return '<option value="">Selecione...</option>' + estado.prioridades.map(function (p) {
      return '<option value="' + esc(p) + '"' + (p === selecionada ? " selected" : "") + ">" + esc(p) + "</option>";
    }).join("");
  }

  function botaoSecundario(acao, id, texto, desabilitado) {
    return '<button type="button" class="det-btn det-btn-sec" data-do="' + acao + '"' +
      (id != null ? ' data-id="' + id + '"' : "") + (desabilitado ? " disabled" : "") +
      '><i class="bi bi-pencil"></i> ' + texto + "</button>";
  }

  function rodapeEdicao(salvar, cancelar, id) {
    const dado = id != null ? ' data-id="' + id + '"' : "";
    return '<div class="det-erro" role="alert" hidden></div>' +
      '<div class="det-acoes">' +
      '<button type="button" class="det-btn det-btn-salvar" data-do="' + salvar + '"' + dado + ">Salvar</button>" +
      '<button type="button" class="det-btn det-btn-cancelar" data-do="' + cancelar + '"' + dado + ">Cancelar</button>" +
      "</div>";
  }


  /* =========================================================
     DESENHO DO POP-UP
     ========================================================= */

  function renderCabecalho() {
    const a = estado.acao;
    elTitulo.textContent = "AÇÃO " + a.codigo;
    elSubtitulo.textContent = a.nome || "";
    elBadge.textContent = a.status.nome;
    elBadge.style.backgroundColor = a.status.cor;
    overlay.style.setProperty("--det-cor", a.status.cor);
  }

  function renderAcao() {
    const a = estado.acao;
    const editando = estado.editandoAcao;
    const bloqueado = estado.editandoEtapa !== null;
    let conteudo;

    if (!editando) {
      conteudo =
        item("Código", esc(a.codigo)) +
        item("Eixo", esc(a.eixo || "Não informado")) +
        item("Nome", esc(a.nome || "Não informado"), true) +
        item("Prioridade", chipPrioridade(a.prioridade)) +
        item("Custo", esc(fmtCusto(a.custo))) +
        item("Data de início", esc(fmtData(a.data_inicio))) +
        item("Data de fim", esc(fmtData(a.data_fim))) +
        item("Responsável", esc(a.responsavel || "Não informado"), true) +
        item("Observações", a.observacoes ? esc(a.observacoes) : vazio("Nenhuma observação informada."), true);
    } else {
      conteudo =
        item("Código", esc(a.codigo)) +
        item("Eixo", esc(a.eixo || "Não informado")) +
        item("Nome", esc(a.nome || "Não informado"), true) +
        campo("detf-prioridade", "Prioridade", true,
          '<select class="det-input" id="detf-prioridade" name="prioridade">' + opcoesPrioridade(a.prioridade) + "</select>") +
        campo("detf-custo", "Custo total (R$)", true,
          '<input class="det-input" id="detf-custo" name="custo" type="text" inputmode="numeric" value="' + esc(fmtCustoCampo(a.custo)) + '">') +
        campo("detf-data-inicio", "Data de início", true,
          '<input class="det-input" id="detf-data-inicio" name="data_inicio" type="date" value="' + esc(a.data_inicio) + '">') +
        campo("detf-data-fim", "Data de fim", true,
          '<input class="det-input" id="detf-data-fim" name="data_fim" type="date" value="' + esc(a.data_fim) + '">') +
        item("Responsável", esc(a.responsavel || "Não informado"), true) +
        campo("detf-observacoes", "Observações", false,
          '<textarea class="det-input" id="detf-observacoes" name="observacoes" rows="3">' + esc(a.observacoes) + "</textarea>", true);
    }

    const botaoEditar = (!a.somente_leitura && !editando)
      ? botaoSecundario("editar-acao", null, "Editar ação", bloqueado)
      : "";

    const aviso = a.somente_leitura
      ? '<p class="det-aviso"><i class="bi bi-slash-circle"></i> Ação cancelada: não pode mais ser editada.</p>'
      : "";

    elAcao.innerHTML =
      '<div class="det-card">' +
      '<div class="det-card-head"><h3><i class="bi bi-card-text"></i> Dados da ação</h3>' + botaoEditar + "</div>" +
      aviso +
      '<dl class="det-grid">' + conteudo + "</dl>" +
      (editando ? rodapeEdicao("salvar-acao", "cancelar-acao") : "") +
      "</div>";
  }

  function etapaHtml(e) {
    const editando = estado.editandoEtapa === e.id;
    const algumaEdicao = estado.editandoAcao || estado.editandoEtapa !== null;
    const somenteLeitura = estado.acao.somente_leitura;

    if (editando) {
      const p = "detf-e" + e.id + "-";
      return '<article class="det-etapa editando" data-id="' + e.id + '">' +
        '<div class="det-etapa-topo"><span class="det-etapa-titulo"><i class="bi bi-pencil-square"></i> Editando etapa</span></div>' +
        '<dl class="det-grid">' +
        campo(p + "nome", "Etapa", true,
          '<input class="det-input" id="' + p + 'nome" name="nome" type="text" maxlength="45" value="' + esc(e.nome) + '">', true) +
        campo(p + "cpf", "CPF do responsável", true,
          '<input class="det-input" id="' + p + 'cpf" name="cpf" type="text" maxlength="14" placeholder="000.000.000-00" value="' + esc(mascaraCpf(e.cpf)) + '">') +
        campo(p + "prioridade", "Prioridade", true,
          '<select class="det-input" id="' + p + 'prioridade" name="prioridade">' + opcoesPrioridade(e.prioridade) + "</select>") +
        campo(p + "inicio", "Início", true,
          '<input class="det-input" id="' + p + 'inicio" name="data_inicio" type="date" value="' + esc(e.data_inicio) + '">') +
        campo(p + "fim", "Fim", true,
          '<input class="det-input" id="' + p + 'fim" name="data_fim" type="date" value="' + esc(e.data_fim) + '">') +
        campo(p + "obs", "Observações", false,
          '<input class="det-input" id="' + p + 'obs" name="observacoes" type="text" value="' + esc(e.observacoes) + '">', true) +
        "</dl>" +
        rodapeEdicao("salvar-etapa", "cancelar-etapa", e.id) +
        "</article>";
    }

    const botao = somenteLeitura ? "" : botaoSecundario("editar-etapa", e.id, "Editar etapa", algumaEdicao);

    return '<article class="det-etapa' + (e.concluida ? " concluida" : "") + '" data-id="' + e.id + '">' +
      '<div class="det-etapa-topo">' +
      '<label class="det-check">' +
      '<input type="checkbox" class="det-check-input" data-id="' + e.id + '"' +
      (e.concluida ? " checked" : "") + (somenteLeitura || algumaEdicao ? " disabled" : "") + ">" +
      '<span class="det-etapa-nome">' + esc(e.nome) + "</span>" +
      "</label>" + botao +
      "</div>" +
      '<dl class="det-grid">' +
      item("Responsável", esc(e.responsavel) + ' <span class="det-cpf">' + esc(mascaraCpf(e.cpf)) + "</span>", true) +
      item("Prioridade", chipPrioridade(e.prioridade)) +
      item("Período", esc(fmtData(e.data_inicio)) + " até " + esc(fmtData(e.data_fim))) +
      item("Observações", e.observacoes ? esc(e.observacoes) : vazio("Sem observações."), true) +
      "</dl>" +
      "</article>";
  }

  function renderEtapas() {
    const lista = estado.etapas;
    const feitas = lista.filter(function (e) { return e.concluida; }).length;
    const porcento = lista.length ? Math.round((feitas / lista.length) * 100) : 0;

    let progresso = "";
    if (lista.length) {
      progresso =
        '<div class="det-progresso">' +
        '<div class="det-progresso-texto">' + feitas + " de " + lista.length +
        (lista.length === 1 ? " concluída" : " concluídas") + "</div>" +
        '<div class="det-progresso-barra"><div class="det-progresso-preenchido" style="width:' + porcento + '%"></div></div>' +
        "</div>";
    }

    const corpo = lista.length
      ? '<div class="det-etapas-lista">' + lista.map(etapaHtml).join("") + "</div>"
      : '<p class="det-vazio">Nenhuma etapa cadastrada para esta ação.</p>';

    elEtapas.innerHTML =
      '<div class="det-card">' +
      '<div class="det-card-head"><h3><i class="bi bi-list-check"></i> Etapas da ação</h3></div>' +
      progresso + corpo +
      "</div>";
  }

  function renderRodape() {
    elRodape.hidden = estado.acao.somente_leitura;
    elRodape.querySelectorAll(".det-status-btn").forEach(function (botao) {
      const atual = String(botao.dataset.status) === String(estado.acao.status.id);
      botao.disabled = atual;
      botao.classList.toggle("atual", atual);
    });
  }

  function render() {
    renderCabecalho();
    renderAcao();
    renderEtapas();
    renderRodape();
  }


  /* =========================================================
     ABRIR E FECHAR
     ========================================================= */

  async function abrir(codigo) {
    codigoAberto = codigo;
    estado = null;

    elTitulo.textContent = "AÇÃO " + codigo;
    elSubtitulo.textContent = "";
    elBadge.textContent = "";
    elBadge.style.backgroundColor = "";
    elRodape.hidden = true;
    elAcao.innerHTML = '<div class="det-card"><p class="det-vazio">Carregando...</p></div>';
    elEtapas.innerHTML = "";

    overlay.classList.add("open");
    overlay.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";

    try {
      const dados = await pedir(urlDe(urls.detalhes, codigo));
      if (codigoAberto !== codigo) return; // fechou enquanto carregava
      estado = {
        acao: dados.acao,
        etapas: dados.etapas,
        prioridades: dados.prioridades,
        editandoAcao: false,
        editandoEtapa: null
      };
      render();
    } catch (erro) {
      elAcao.innerHTML = '<div class="det-card"><p class="det-vazio">' + esc(erro.message) + "</p></div>";
    }
  }

  function fechar() {
    overlay.classList.remove("open");
    overlay.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    estado = null;
    codigoAberto = null;
  }

  function tentarFechar() {
    const editando = estado && (estado.editandoAcao || estado.editandoEtapa !== null);
    if (editando && !confirm("Descartar as alterações que estão sendo editadas?")) return;
    fechar();
  }

  // Botão de seta no card
  document.addEventListener("click", function (event) {
    const botao = event.target.closest(".status-menu-toggle");
    if (!botao) return;
    const card = botao.closest(".task-card");
    if (card && card.dataset.codigo) abrir(card.dataset.codigo);
  });

  $("detFechar").addEventListener("click", tentarFechar);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && overlay.classList.contains("open")) tentarFechar();
  });


  /* =========================================================
     SALVAR AÇÃO
     ========================================================= */

  async function salvarAcao(botao) {
    const caixa = elAcao.querySelector(".det-erro");
    const ler = function (nome) { return elAcao.querySelector('[name="' + nome + '"]'); };

    elAcao.querySelectorAll(".invalido").forEach(function (c) { c.classList.remove("invalido"); });
    caixa.hidden = true;

    const vazios = ["prioridade", "custo", "data_inicio", "data_fim"].filter(function (nome) {
      return !ler(nome).value.trim();
    });
    vazios.forEach(function (nome) { ler(nome).classList.add("invalido"); });
    if (vazios.length) return mostrarErro(caixa, "Preencha os campos obrigatórios marcados com *.");

    if (ler("data_fim").value < ler("data_inicio").value) {
      ler("data_fim").classList.add("invalido");
      return mostrarErro(caixa, "A data de fim não pode ser anterior à data de início.");
    }

    const corpo = {
      prioridade: ler("prioridade").value,
      custo: ler("custo").value.replace(/\./g, "").replace(",", "."),
      data_inicio: ler("data_inicio").value,
      data_fim: ler("data_fim").value,
      observacoes: ler("observacoes").value.trim()
    };

    botao.disabled = true;
    try {
      const resposta = await pedir(urlDe(urls.editarAcao, codigoAberto), {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
        body: JSON.stringify(corpo)
      });
      estado.acao = resposta.acao;
      estado.editandoAcao = false;
      render();
    } catch (erro) {
      mostrarErro(caixa, erro.message);
      botao.disabled = false;
    }
  }


  /* =========================================================
     SALVAR ETAPA
     ========================================================= */

  async function salvarEtapa(id, botao) {
    const bloco = elEtapas.querySelector('.det-etapa[data-id="' + id + '"]');
    const caixa = bloco.querySelector(".det-erro");
    const ler = function (nome) { return bloco.querySelector('[name="' + nome + '"]'); };

    bloco.querySelectorAll(".invalido").forEach(function (c) { c.classList.remove("invalido"); });
    caixa.hidden = true;

    const vazios = ["nome", "cpf", "prioridade", "data_inicio", "data_fim"].filter(function (nome) {
      return !ler(nome).value.trim();
    });
    vazios.forEach(function (nome) { ler(nome).classList.add("invalido"); });
    if (vazios.length) return mostrarErro(caixa, "Preencha os campos obrigatórios marcados com *.");

    if (ler("cpf").value.replace(/\D/g, "").length !== 11) {
      ler("cpf").classList.add("invalido");
      return mostrarErro(caixa, "O CPF está incompleto.");
    }

    if (ler("data_fim").value < ler("data_inicio").value) {
      ler("data_fim").classList.add("invalido");
      return mostrarErro(caixa, "A data de fim não pode ser anterior à data de início.");
    }

    const corpo = {
      nome: ler("nome").value.trim(),
      cpf: ler("cpf").value,
      prioridade: ler("prioridade").value,
      data_inicio: ler("data_inicio").value,
      data_fim: ler("data_fim").value,
      observacoes: ler("observacoes").value.trim()
    };

    botao.disabled = true;
    try {
      const resposta = await pedir(urlDe(urls.editarEtapa, id), {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
        body: JSON.stringify(corpo)
      });
      estado.etapas = estado.etapas.map(function (e) { return e.id === id ? resposta.etapa : e; });
      estado.editandoEtapa = null;
      render();
    } catch (erro) {
      mostrarErro(caixa, erro.message);
      botao.disabled = false;
    }
  }


  /* =========================================================
     MOVER PARA OUTRO STATUS
     ========================================================= */

  function mudarStatus(statusId) {
    if (estado && (estado.editandoAcao || estado.editandoEtapa !== null) &&
        !confirm("Descartar as alterações que estão sendo editadas?")) return;

    const card = document.querySelector('.task-card[data-codigo="' + codigoAberto + '"]');
    const form = card && card.querySelector("form");
    const input = form && form.querySelector('input[name="status"]');
    if (!input) return;

    input.value = statusId;
    form.submit();
  }


  /* =========================================================
     EVENTOS DENTRO DO POP-UP
     ========================================================= */

  overlay.addEventListener("click", function (event) {
    // Clique no fundo desfocado fecha
    if (event.target === overlay) return tentarFechar();

    const botao = event.target.closest("[data-do]");
    if (!botao || !estado) return;

    const id = botao.dataset.id ? Number(botao.dataset.id) : null;

    switch (botao.dataset.do) {
      case "editar-acao":     estado.editandoAcao = true; render(); break;
      case "cancelar-acao":   estado.editandoAcao = false; render(); break;
      case "salvar-acao":     salvarAcao(botao); break;
      case "editar-etapa":    estado.editandoEtapa = id; render(); break;
      case "cancelar-etapa":  estado.editandoEtapa = null; render(); break;
      case "salvar-etapa":    salvarEtapa(id, botao); break;
      case "mudar-status":    mudarStatus(botao.dataset.status); break;
    }
  });

  // Marcar / desmarcar etapa como concluída
  overlay.addEventListener("change", async function (event) {
    const caixa = event.target.closest(".det-check-input");
    if (!caixa || !estado) return;

    const id = Number(caixa.dataset.id);
    caixa.disabled = true;

    try {
      const resposta = await pedir(urlDe(urls.concluirEtapa, id), {
        method: "POST",
        headers: { "X-CSRFToken": csrf() }
      });
      const etapa = estado.etapas.find(function (e) { return e.id === id; });
      if (etapa) etapa.concluida = resposta.concluida;
      render();
    } catch (erro) {
      caixa.checked = !caixa.checked;
      caixa.disabled = false;
      alert(erro.message);
    }
  });

  // Máscaras de CPF e custo, e tira o vermelho do campo em que a pessoa digita
  overlay.addEventListener("input", function (event) {
    const alvo = event.target;
    alvo.classList.remove("invalido");

    if (alvo.name === "cpf") alvo.value = mascaraCpf(alvo.value);
    if (alvo.name === "custo") alvo.value = mascaraCusto(alvo.value);
  });
  overlay.addEventListener("change", function (event) {
    event.target.classList.remove("invalido");
  });

});