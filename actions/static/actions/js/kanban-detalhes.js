/*
 * Pop-up de detalhes da ação (Kanban)
 *
 * Esquerda: dados da ação (botão "Editar ação").
 * Direita:  etapas da ação (botão "Adicionar etapa", botão "Editar etapa" em cada uma
 *           e caixa de concluída).
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
    concluirEtapa: overlay.dataset.urlConcluirEtapa,
    adicionarEtapa: overlay.dataset.urlAdicionarEtapa,
    excluirAcao: overlay.dataset.urlExcluirAcao,
    excluirEtapa: overlay.dataset.urlExcluirEtapa
  };

  // Tempo da animação de fechar (igual ao do CSS). Sem animação para quem prefere menos movimento.
  const DURACAO_SAIDA = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 150;
  let timerFechar = null;

  let codigoAberto = null;
  // estado = { acao, etapas, prioridades, editandoAcao, editandoEtapa, novaEtapa }
  let estado = null;

  // Largura (em %) que a barra de progresso tinha no último desenho.
  // Como o pop-up é redesenhado a cada mudança, usamos este valor para a barra
  // nascer na largura antiga e deslizar até a nova.
  let ultimoPorcento = null;


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

    // Escolhe texto escuro ou branco conforme o brilho da cor de fundo, para o texto sempre ficar legível
  function corDoTexto(hex) {
    const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(String(hex || "").trim());
    if (!m) return "#fff";
    const brilho = (parseInt(m[1], 16) * 299 + parseInt(m[2], 16) * 587 + parseInt(m[3], 16) * 114) / 1000;
    return brilho > 150 ? "#2b2b2b" : "#fff";
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

  // Tem alguma ação, etapa ou etapa nova sendo editada?
  function emEdicao() {
    return !!estado && (estado.editandoAcao || estado.editandoEtapa !== null || estado.novaEtapa);
  }


  /* =========================================================
     PEÇAS DE HTML
     ========================================================= */

  // "classe" é opcional e vai no <dd> (usada nas observações, que têm limite de altura)
  function item(rotulo, valor, cheio, classe) {
    return '<div class="det-item' + (cheio ? " full" : "") + '"><dt>' + rotulo + "</dt>" +
      "<dd" + (classe ? ' class="' + classe + '"' : "") + ">" + valor + "</dd></div>";
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

  function botaoSecundario(acao, id, texto, desabilitado, icone) {
    return '<button type="button" class="det-btn det-btn-sec" data-do="' + acao + '"' +
      (id != null ? ' data-id="' + id + '"' : "") + (desabilitado ? " disabled" : "") +
      '><i class="bi bi-' + (icone || "pencil") + '"></i> ' + texto + "</button>";
  }

  function botaoExcluirEtapa(id, desabilitado) {
    return '<button type="button" class="det-btn det-btn-perigo" data-do="excluir-etapa" data-id="' + id + '"' +
      (desabilitado ? " disabled" : "") + '><i class="bi bi-trash3"></i> Excluir</button>';
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
    elBadge.style.color = corDoTexto(a.status.cor);
    overlay.style.setProperty("--det-cor", a.status.cor);
  }

  function renderAcao() {
    const a = estado.acao;
    const editando = estado.editandoAcao;
    const bloqueado = estado.editandoEtapa !== null || estado.novaEtapa;
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
        item("Observações", a.observacoes ? esc(a.observacoes) : vazio("Nenhuma observação informada."), true, "det-obs det-obs-acao");
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
          '<textarea class="det-input" id="detf-observacoes" name="observacoes" rows="4">' + esc(a.observacoes) + "</textarea>", true);
    }

    const botaoEditar = (!a.somente_leitura && !editando)
      ? botaoSecundario("editar-acao", null, "Editar ação", bloqueado)
      : "";

    const aviso = a.somente_leitura
      ? '<p class="det-aviso"><i class="bi bi-slash-circle"></i> Ação cancelada: não pode mais ser editada.</p>'
      : "";

    elAcao.innerHTML =
      '<div class="det-card det-card-acao">' +
      '<div class="det-card-head"><h3><i class="bi bi-card-text"></i> Dados da ação</h3>' + botaoEditar + "</div>" +
      aviso +
      '<dl class="det-grid">' + conteudo + "</dl>" +
      (editando ? rodapeEdicao("salvar-acao", "cancelar-acao") : "") +
      "</div>";

  }

  // Formulário de etapa. Com id = edita a etapa; com id = null é o formulário de etapa nova.
  function formEtapaHtml(e, id) {
    const nova = id == null;
    const p = "detf-e" + (nova ? "nova" : id) + "-";

    return '<article class="det-etapa editando' + (nova ? " nova" : "") + '"' + (nova ? "" : ' data-id="' + id + '"') + ">" +
      '<div class="det-etapa-topo"><span class="det-etapa-titulo">' +
      '<i class="bi bi-' + (nova ? "plus-circle" : "pencil-square") + '"></i> ' + (nova ? "Nova etapa" : "Editando etapa") +
      "</span></div>" +
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
      rodapeEdicao(nova ? "salvar-nova-etapa" : "salvar-etapa", nova ? "cancelar-nova-etapa" : "cancelar-etapa", id) +
      "</article>";
  }

  function etapaHtml(e) {
    const algumaEdicao = emEdicao();
    const somenteLeitura = estado.acao.somente_leitura;

    if (estado.editandoEtapa === e.id) return formEtapaHtml(e, e.id);

      const botoes = somenteLeitura ? "" :
      '<div class="det-etapa-botoes">' +
      botaoSecundario("editar-etapa", e.id, "Editar etapa", algumaEdicao) +
      botaoExcluirEtapa(e.id, algumaEdicao) +
      "</div>";
          
    return '<article class="det-etapa' + (e.concluida ? " concluida" : "") + '" data-id="' + e.id + '">' +
      '<div class="det-etapa-topo">' +
      '<label class="det-check">' +
      '<input type="checkbox" class="det-check-input" data-id="' + e.id + '"' +
      (e.concluida ? " checked" : "") + (somenteLeitura || algumaEdicao ? " disabled" : "") + ">" +
      '<span class="det-etapa-nome">' + esc(e.nome) + "</span>" +
      "</label>" + botoes +
      "</div>" +
      '<dl class="det-grid">' +
      item("Responsável", esc(e.responsavel) + ' <span class="det-cpf">' + esc(mascaraCpf(e.cpf)) + "</span>", true) +
      item("Prioridade", chipPrioridade(e.prioridade)) +
      item("Período", esc(fmtData(e.data_inicio)) + " até " + esc(fmtData(e.data_fim))) +
      item("Observações", e.observacoes ? esc(e.observacoes) : vazio("Sem observações."), true, "det-obs") +
      "</dl>" +
      "</article>";
  }

  function renderEtapas() {
    const lista = estado.etapas;
    const feitas = lista.filter(function (e) { return e.concluida; }).length;
    const porcento = lista.length ? Math.round((feitas / lista.length) * 100) : 0;

    // Guarda a rolagem da lista, porque o HTML é refeito do zero
    const listaAntiga = elEtapas.querySelector(".det-etapas-lista");
    const rolagem = listaAntiga ? listaAntiga.scrollTop : 0;

    // Na primeira vez a barra já nasce na largura certa; depois ela parte da largura antiga
    const larguraInicial = ultimoPorcento == null ? porcento : ultimoPorcento;

    let progresso = "";
    if (lista.length) {
      progresso =
        '<div class="det-progresso">' +
        '<div class="det-progresso-texto">' + feitas + " de " + lista.length +
        (lista.length === 1 ? " concluída" : " concluídas") + "</div>" +
        '<div class="det-progresso-barra"><div class="det-progresso-preenchido" style="width:' + larguraInicial + '%"></div></div>' +
        "</div>";
    }

    const formNova = estado.novaEtapa ? formEtapaHtml({}, null) : "";

    const corpo = (lista.length || estado.novaEtapa)
      ? '<div class="det-etapas-lista">' + lista.map(etapaHtml).join("") + formNova + "</div>"
      : '<p class="det-vazio">Nenhuma etapa cadastrada para esta ação.</p>';

    const botaoAdicionar = estado.acao.somente_leitura
      ? ""
      : botaoSecundario("adicionar-etapa", null, "Adicionar etapa", emEdicao(), "plus-lg");

    elEtapas.innerHTML =
      '<div class="det-card det-card-etapas">' +
      '<div class="det-card-head"><h3><i class="bi bi-list-check"></i> Etapas da ação</h3>' + botaoAdicionar + "</div>" +
      progresso + corpo +
      "</div>";

    const novaLista = elEtapas.querySelector(".det-etapas-lista");
    if (novaLista) novaLista.scrollTop = rolagem;

    // Força o navegador a "ver" a largura antiga e só então muda para a nova: é isso que anima
    const barra = elEtapas.querySelector(".det-progresso-preenchido");
    if (barra) {
      void barra.offsetWidth;
      barra.style.width = porcento + "%";
    }
    ultimoPorcento = porcento;
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

  // Rola até o formulário da etapa nova e coloca o cursor no primeiro campo
  function focarNovaEtapa() {
    const form = elEtapas.querySelector(".det-etapa.nova");
    if (!form) return;
    form.scrollIntoView({ behavior: "smooth", block: "nearest" });
    const primeiro = form.querySelector("input");
    if (primeiro) primeiro.focus({ preventScroll: true });
  }

    /* =========================================================
     AVISO DE CONFIRMAÇÃO (no lugar do confirm/alert do navegador)
     ========================================================= */

  const dlgConfirma = document.createElement("div");
  dlgConfirma.className = "det-confirma-overlay";
  dlgConfirma.setAttribute("aria-hidden", "true");
  dlgConfirma.innerHTML =
    '<div class="det-confirma" role="alertdialog" aria-modal="true" ' +
    'aria-labelledby="detConfirmaTitulo" aria-describedby="detConfirmaTexto">' +
    '<h3 id="detConfirmaTitulo"></h3>' +
    '<p id="detConfirmaTexto"></p>' +
    '<div class="det-confirma-acoes">' +
    '<button type="button" class="det-btn det-btn-sec" data-resp="nao"></button>' +
    '<button type="button" class="det-btn det-btn-cancelar" data-resp="sim"></button>' +
    "</div></div>";
  document.body.appendChild(dlgConfirma);

  // Mostra o aviso e devolve uma Promise: true se a pessoa confirmou, false se cancelou.
  // Com nao: null vira um aviso simples, só com o botão de confirmar.
  function confirmar(opcoes) {
    return new Promise(function (resolve) {
      const botaoSim = dlgConfirma.querySelector('[data-resp="sim"]');
      const botaoNao = dlgConfirma.querySelector('[data-resp="nao"]');

      dlgConfirma.querySelector("#detConfirmaTitulo").textContent = opcoes.titulo;
      dlgConfirma.querySelector("#detConfirmaTexto").textContent = opcoes.texto;
      botaoSim.textContent = opcoes.sim || "OK";
      botaoNao.textContent = opcoes.nao || "Cancelar";
      botaoNao.hidden = opcoes.nao === null;
      dlgConfirma.classList.toggle("neutro", opcoes.perigo === false);

      dlgConfirma.classList.add("open");
      dlgConfirma.setAttribute("aria-hidden", "false");
      // O foco começa na opção segura (a que não descarta nada)
      (botaoNao.hidden ? botaoSim : botaoNao).focus();

      function responder(resposta) {
        dlgConfirma.classList.remove("open");
        dlgConfirma.setAttribute("aria-hidden", "true");
        dlgConfirma.removeEventListener("click", aoClicar);
        document.removeEventListener("keydown", aoTeclar, true);
        resolve(resposta);
      }

      function aoClicar(event) {
        if (event.target === dlgConfirma) return responder(false); // clique no fundo
        const botao = event.target.closest("[data-resp]");
        if (botao) responder(botao.dataset.resp === "sim");
      }

      // Esc fecha só o aviso, sem fechar o pop-up de trás
      function aoTeclar(event) {
        if (event.key !== "Escape") return;
        event.preventDefault();
        event.stopPropagation();
        responder(false);
      }

      dlgConfirma.addEventListener("click", aoClicar);
      document.addEventListener("keydown", aoTeclar, true);
    });
  }

  function confirmarDescarte() {
    return confirmar({
      titulo: "Descartar alterações?",
      texto: "Você tem alterações que ainda não foram salvas. Se continuar, elas serão perdidas.",
      sim: "Descartar",
      nao: "Continuar editando"
    });
  }

    // Deixa o aviso disponível para o pop-up de cadastro (kanban-modal.js)
    window.confirmarSite = confirmar;

  /* =========================================================
     ABRIR E FECHAR
     ========================================================= */

  async function abrir(codigo) {
    clearTimeout(timerFechar);
    overlay.classList.remove("closing");
    codigoAberto = codigo;
    estado = null;
    ultimoPorcento = null;

    elTitulo.textContent = "AÇÃO " + codigo;
    elSubtitulo.textContent = "";
    elBadge.textContent = "";
    elBadge.style.backgroundColor = "";
    elBadge.style.color = "";
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
        editandoEtapa: null,
        novaEtapa: false
      };
      render();
    } catch (erro) {
      elAcao.innerHTML = '<div class="det-card"><p class="det-vazio">' + esc(erro.message) + "</p></div>";
    }
  }

  function fechar() {
    if (overlay.classList.contains("closing")) return;

    estado = null;
    codigoAberto = null;
    ultimoPorcento = null;

    overlay.classList.add("closing");
    timerFechar = setTimeout(function () {
      overlay.classList.remove("open", "closing");
      overlay.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
    }, DURACAO_SAIDA);
  }

    async function tentarFechar() {
    if (emEdicao() && !(await confirmarDescarte())) return;
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
    if (event.key === "Escape" && overlay.classList.contains("open") && !overlay.classList.contains("closing")) {
      tentarFechar();
    }
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
     SALVAR ETAPA (editar uma existente ou criar uma nova)
     ========================================================= */

  // id = número da etapa para editar, ou null para criar uma etapa nova
  async function salvarEtapa(id, botao) {
    const nova = id == null;
    const bloco = nova
      ? elEtapas.querySelector(".det-etapa.nova")
      : elEtapas.querySelector('.det-etapa[data-id="' + id + '"]');
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

    const url = nova ? urlDe(urls.adicionarEtapa, codigoAberto) : urlDe(urls.editarEtapa, id);

    botao.disabled = true;
    try {
      const resposta = await pedir(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
        body: JSON.stringify(corpo)
      });

      if (nova) {
        estado.etapas.push(resposta.etapa);
        estado.novaEtapa = false;
      } else {
        estado.etapas = estado.etapas.map(function (e) { return e.id === id ? resposta.etapa : e; });
        estado.editandoEtapa = null;
      }
      render();

      // A etapa nova entra no fim da lista: rola até ela
      if (nova) {
        const lista = elEtapas.querySelector(".det-etapas-lista");
        if (lista) lista.scrollTo({ top: lista.scrollHeight, behavior: "smooth" });
      }
    } catch (erro) {
      mostrarErro(caixa, erro.message);
      botao.disabled = false;
    }
  }


  /* =========================================================
     MOVER PARA OUTRO STATUS
     ========================================================= */

   async function mudarStatus(statusId) {
    if (emEdicao() && !(await confirmarDescarte())) return;

    const card = document.querySelector('.task-card[data-codigo="' + codigoAberto + '"]');
    const form = card && card.querySelector("form");
    const input = form && form.querySelector('input[name="status"]');
    if (!input) return;

    input.value = statusId;
    form.submit();
  }

  async function excluirAcao(botao) {
    const confirmado = await confirmar({
      titulo: "Excluir a ação " + estado.acao.codigo + "?",
      texto: "A ação e todas as suas etapas serão excluídas de forma permanente. Essa operação não pode ser desfeita.",
      sim: "Excluir",
      nao: "Cancelar"
    });
    if (!confirmado) return;

    botao.disabled = true;
    try {
      await pedir(urlDe(urls.excluirAcao, codigoAberto), {
        method: "POST",
        headers: { "X-CSRFToken": csrf() }
      });
      window.location.reload();
    } catch (erro) {
      botao.disabled = false;
      confirmar({ titulo: "Não foi possível excluir", texto: erro.message, sim: "OK", nao: null });
    }
  }

  async function excluirEtapa(id, botao) {
    const etapa = estado.etapas.find(function (e) { return e.id === id; });
    if (!etapa) return;

    const confirmado = await confirmar({
      titulo: "Excluir a etapa?",
      texto: "A etapa \"" + etapa.nome + "\" será excluída de forma permanente. Essa operação não pode ser desfeita.",
      sim: "Excluir",
      nao: "Cancelar"
    });
    if (!confirmado) return;

    botao.disabled = true;
    try {
      await pedir(urlDe(urls.excluirEtapa, id), {
        method: "POST",
        headers: { "X-CSRFToken": csrf() }
      });
      if (!estado) return;
      estado.etapas = estado.etapas.filter(function (e) { return e.id !== id; });
      render();
    } catch (erro) {
      botao.disabled = false;
      confirmar({ titulo: "Não foi possível excluir", texto: erro.message, sim: "OK", nao: null });
    }
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
      case "editar-acao":        estado.editandoAcao = true; render(); break;
      case "cancelar-acao":      estado.editandoAcao = false; render(); break;
      case "salvar-acao":        salvarAcao(botao); break;
      case "editar-etapa":       estado.editandoEtapa = id; render(); break;
      case "cancelar-etapa":     estado.editandoEtapa = null; render(); break;
      case "salvar-etapa":       salvarEtapa(id, botao); break;
      case "adicionar-etapa":    estado.novaEtapa = true; render(); focarNovaEtapa(); break;
      case "cancelar-nova-etapa": estado.novaEtapa = false; render(); break;
      case "salvar-nova-etapa":  salvarEtapa(null, botao); break;
      case "mudar-status":       mudarStatus(botao.dataset.status); break;
      case "excluir-acao":       excluirAcao(botao); break;
      case "excluir-etapa":      excluirEtapa(id, botao); break;
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
      confirmar({ titulo: "Não foi possível concluir", texto: erro.message, sim: "OK", nao: null });
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