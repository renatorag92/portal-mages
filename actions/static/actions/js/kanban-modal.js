/*
 * Pop-up de cadastro de ação e etapas (Kanban)
 *
 * Esquerda: dados da ação. Direita: etapas, cada uma em um cartão.
 */
document.addEventListener("DOMContentLoaded", function () {

  const overlay = document.getElementById("acaoModalOverlay");
  const form = document.getElementById("formCadastroAcao");
  if (!overlay || !form) return;

  // Move o pop-up para o <body>, assim nenhum container do layout limita o position: fixed
  document.body.appendChild(overlay);

  const $ = function (id) { return document.getElementById(id); };

  const selEixo = $("eixo");
  const acaoTexto = $("acaoTexto");
  const lista = $("customAcoesList");
  const hidAcao = $("acao");
  const hidNova = $("novaAcao");
  const hidStatus = $("acaoStatus");
  const badge = $("acaoStatusBadge");
  const etapasList = $("etapasList");
  const etapasVazio = $("etapasVazio");
  const etapasContagem = $("etapasContagem");
  const tplEtapa = $("etapaTemplate");
  const erroBox = $("acaoFormErro");
  const btnSalvar = $("salvarAcaoBtn");

  const catalogoEl = $("dados-catalogo");
  const catalogo = catalogoEl ? JSON.parse(catalogoEl.textContent) : [];

  let dirty = false; // true quando o usuário já mexeu em algum campo
  let contadorEtapas = 0; // usado para dar ids únicos aos campos de cada etapa

  // Tempo da animação de fechar (igual ao do CSS). Sem animação para quem prefere menos movimento.
  const DURACAO_SAIDA = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 150;
  let timerFechar = null;

  function norm(texto) {
    return String(texto || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }


  /* ---------- Cor do texto: cinza quando vazio, escuro quando preenchido ---------- */

  function atualizarCor(campo) {
    if (campo.tagName === "SELECT") {
      campo.classList.toggle("placeholder-ativo", campo.value === "");
    } else if (campo.type === "date") {
      campo.style.color = campo.value ? "" : "#999";
    }
  }

  function atualizarTodasAsCores() {
    form.querySelectorAll('select, input[type="date"]').forEach(atualizarCor);
  }


  /* ---------- Etapas: cartões ---------- */

  // Renumera os cartões, atualiza o contador e mostra o aviso de lista vazia
  function atualizarEtapas() {
    const cartoes = etapasList.querySelectorAll(".etapa-card");

    cartoes.forEach(function (cartao, i) {
      cartao.querySelector(".etapa-num").textContent = "Etapa " + (i + 1);
    });

    etapasContagem.textContent = cartoes.length ? "(" + cartoes.length + ")" : "";
    etapasVazio.hidden = cartoes.length > 0;
  }

  // Cria um cartão de etapa novo a partir do modelo do HTML
  function novaEtapa(focar) {
    const cartao = tplEtapa.content.firstElementChild.cloneNode(true);
    contadorEtapas++;

    // Liga cada rótulo ao seu campo (ids únicos por cartão)
    cartao.querySelectorAll(".form-group").forEach(function (grupo, i) {
      const controle = grupo.querySelector("input, select");
      const rotulo = grupo.querySelector("label");
      if (!controle || !rotulo) return;
      controle.id = "etapa" + contadorEtapas + "-" + i;
      rotulo.htmlFor = controle.id;
    });

    cartao.querySelectorAll('select, input[type="date"]').forEach(atualizarCor);
    etapasList.appendChild(cartao);
    atualizarEtapas();

    if (focar) {
      cartao.scrollIntoView({ behavior: "smooth", block: "nearest" });
      cartao.querySelector("input").focus({ preventScroll: true });
    }
  }

  $("adicionarEtapaBtn").addEventListener("click", function () { novaEtapa(true); });

  etapasList.addEventListener("click", function (event) {
    const remover = event.target.closest(".etapa-remove");
    if (!remover) return;
    remover.closest(".etapa-card").remove();
    atualizarEtapas();
  });


  /* ---------- Abrir / fechar ---------- */

  function mostrarErro(mensagem) {
    erroBox.textContent = mensagem;
    erroBox.hidden = false;
    erroBox.scrollIntoView({ block: "nearest" });
  }

  function limparFormulario() {
    form.reset();
    etapasList.innerHTML = "";
    contadorEtapas = 0;
    novaEtapa(false); // começa com uma etapa em branco (se ficar vazia, é ignorada ao salvar)
    hidAcao.value = "";
    hidNova.value = "";
    lista.style.display = "none";
    erroBox.hidden = true;
    erroBox.textContent = "";
    atualizarTodasAsCores();
    dirty = false;
  }

  // Mostra no cabeçalho a coluna onde a ação será criada, com a cor dela
  function mostrarStatus(botao) {
    const coluna = botao.closest(".column");
    const cabecalho = coluna && coluna.querySelector(".column-header");
    const titulo = coluna && coluna.querySelector(".column-header .title");
    const cor = cabecalho ? getComputedStyle(cabecalho).backgroundColor : "";

    badge.textContent = titulo ? titulo.textContent.trim() : "";
    badge.style.backgroundColor = cor;
    overlay.style.setProperty("--acao-cor", cor || "#3e4a89");
  }

  function abrir(botao) {
    clearTimeout(timerFechar);
    overlay.classList.remove("closing");

    limparFormulario();
    hidStatus.value = botao.dataset.status;
    mostrarStatus(botao);

    overlay.classList.add("open");
    overlay.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    selEixo.focus();
  }

  // Aviso do site (definido no kanban-detalhes.js). Se não estiver disponível, usa o do navegador.
  function confirmarCancelamento() {
    if (typeof window.confirmarSite !== "function") {
      return Promise.resolve(confirm("Pretende cancelar o cadastro da ação?"));
    }
    return window.confirmarSite({
      titulo: "Cancelar o cadastro?",
      texto: "Os dados preenchidos ainda não foram salvos. Se continuar, eles serão perdidos.",
      sim: "Descartar",
      nao: "Continuar preenchendo"
    });
  }

    function confirmarCriacao(nome, totalEtapas) {
    if (typeof window.confirmarSite !== "function") {
      return Promise.resolve(confirm("Confirma o cadastro da ação?"));
    }

    const coluna = badge.textContent.trim();
    const etapas = totalEtapas
      ? " com " + totalEtapas + (totalEtapas === 1 ? " etapa" : " etapas")
      : " sem etapas";

    return window.confirmarSite({
      titulo: "Cadastrar a ação?",
      texto: "A ação \"" + nome + "\" será criada" + (coluna ? " na coluna \"" + coluna + "\"" : "") + etapas + ".",
      sim: "Cadastrar",
      nao: "Voltar",
      perigo: false
    });
  }

  async function fechar(forcar) {
    if (overlay.classList.contains("closing")) return;
    if (!forcar && dirty && !(await confirmarCancelamento())) return;

    overlay.classList.add("closing");
    timerFechar = setTimeout(function () {
      overlay.classList.remove("open", "closing");
      overlay.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
    }, DURACAO_SAIDA);
  }

  document.addEventListener("click", function (event) {
    const botao = event.target.closest(".add-action-btn");
    if (botao) abrir(botao);
  });

  $("cancelarBtn").addEventListener("click", function () { fechar(false); });
  $("acaoFechar").addEventListener("click", function () { fechar(false); });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && overlay.classList.contains("open")) fechar(false);
  });

  // Clique no fundo desfocado fecha o cadastro. Só vale se o clique começou e terminou
  // no fundo, para não fechar quando a pessoa arrasta o mouse para selecionar texto de um campo.
  let cliqueComecouNoFundo = false;

  overlay.addEventListener("mousedown", function (event) {
    cliqueComecouNoFundo = event.target === overlay;
  });

  overlay.addEventListener("click", function (event) {
    if (event.target === overlay && cliqueComecouNoFundo) fechar(false);
  });

  form.addEventListener("input", function () { dirty = true; });
  form.addEventListener("change", function (event) {
    dirty = true;
    atualizarCor(event.target);
  });


  /* ---------- Eixo → ação (pesquisa e lista suspensa) ---------- */

  // Se o texto bate com uma ação do catálogo daquele eixo, usa o id; senão é uma ação nova
  function sincronizarAcao() {
    const texto = acaoTexto.value.trim();
    const encontrada = catalogo.find(function (a) {
      return String(a.eixo_id) === selEixo.value && norm(a.nome) === norm(texto);
    });
    hidAcao.value = encontrada ? encontrada.id : "";
    hidNova.value = encontrada ? "" : texto;
  }

  function mostrarLista(filtro) {
    lista.innerHTML = "";

    if (!selEixo.value) {
      const aviso = document.createElement("li");
      aviso.className = "dropdown-hint";
      aviso.textContent = "⚠️ Selecione um Eixo primeiro";
      lista.appendChild(aviso);
      lista.style.display = "block";
      return;
    }

    const termo = norm(filtro);
    const itens = catalogo.filter(function (a) {
      return String(a.eixo_id) === selEixo.value && norm(a.nome).includes(termo);
    });

    itens.forEach(function (a) {
      const li = document.createElement("li");
      li.textContent = a.nome;
      li.addEventListener("click", function () {
        acaoTexto.value = a.nome;
        sincronizarAcao();
        lista.style.display = "none";
      });
      lista.appendChild(li);
    });

    lista.style.display = itens.length ? "block" : "none";
  }

  selEixo.addEventListener("change", function () {
    acaoTexto.value = "";
    sincronizarAcao();
    lista.style.display = "none";
  });

  acaoTexto.addEventListener("click", function () { mostrarLista(acaoTexto.value); });

  acaoTexto.addEventListener("input", function () {
    sincronizarAcao();
    mostrarLista(acaoTexto.value);
  });

  document.addEventListener("click", function (event) {
    if (!acaoTexto.contains(event.target) && !lista.contains(event.target)) {
      lista.style.display = "none";
    }
  });


  /* ---------- Máscaras: CPF e custo ---------- */

  etapasList.addEventListener("input", function (event) {
    if (event.target.name !== "etapaResponsavelCpf[]") return;

    event.target.value = event.target.value
      .replace(/\D/g, "")
      .slice(0, 11)
      .replace(/^(\d{3})(\d)/, "$1.$2")
      .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1-$2");
  });

  $("custo").addEventListener("input", function (event) {
    const digitos = event.target.value.replace(/\D/g, "");
    if (!digitos) {
      event.target.value = "";
      return;
    }

    const partes = (parseInt(digitos, 10) / 100).toFixed(2).split(".");
    event.target.value = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + partes[1];
  });


  /* ---------- Enviar ---------- */

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    erroBox.hidden = true;

    const valor = function (id) { return $(id).value.trim(); };

    if (!valor("eixo") || !valor("acaoTexto") || !valor("prioridade") ||
        !valor("custo") || !valor("dataInicio") || !valor("dataFim")) {
      return mostrarErro("Preencha todos os campos obrigatórios marcados com asterisco (*).");
    }

    if (valor("dataFim") < valor("dataInicio")) {
      return mostrarErro("A data de fim não pode ser anterior à data de início.");
    }

    const etapas = [];
    const cartoes = etapasList.querySelectorAll(".etapa-card");

    for (let i = 0; i < cartoes.length; i++) {
      const campo = function (nome) {
        return cartoes[i].querySelector('[name="' + nome + '[]"]').value.trim();
      };

      const etapa = {
        nome: campo("etapaNome"),
        cpf: campo("etapaResponsavelCpf"),
        inicio: campo("etapaInicio"),
        fim: campo("etapaFim"),
        prioridade: campo("etapaPrioridade"),
        observacoes: campo("etapaObservacoes")
      };

      // Etapa totalmente vazia é ignorada
      if (!Object.values(etapa).some(Boolean)) continue;

      if (!etapa.nome || !etapa.cpf || !etapa.inicio || !etapa.fim || !etapa.prioridade) {
        return mostrarErro("Preencha todos os campos obrigatórios da etapa " + (i + 1) + ".");
      }
      if (etapa.cpf.replace(/\D/g, "").length !== 11) {
        return mostrarErro("O CPF da etapa \"" + etapa.nome + "\" está incompleto.");
      }
      if (etapa.fim < etapa.inicio) {
        return mostrarErro("Na etapa \"" + etapa.nome + "\", a data de fim não pode ser anterior à de início.");
      }

      etapas.push(etapa);
    }

    const dados = {
      status: hidStatus.value,
      eixo: valor("eixo"),
      acao: hidAcao.value,
      novaAcao: hidNova.value,
      prioridade: valor("prioridade"),
      custo: valor("custo").replace(/\./g, "").replace(",", "."),
      dataInicio: valor("dataInicio"),
      dataFim: valor("dataFim"),
      observacoes: valor("observacoes"),
      etapas: etapas
    };

    const confirmado = await confirmarCriacao(valor("acaoTexto"), etapas.length);
    if (!confirmado) return;

    btnSalvar.disabled = true;

    try {
      const resposta = await fetch(form.dataset.url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": form.querySelector('[name="csrfmiddlewaretoken"]').value
        },
        body: JSON.stringify(dados)
      });

      const json = await resposta.json().catch(function () { return null; });

      if (!resposta.ok || !json || !json.success) {
        return mostrarErro((json && json.error) || "Não foi possível salvar a ação. Verifique os dados e tente novamente.");
      }

      // Atualiza a página automaticamente após criar a ação
      window.location.reload();

    } catch (erro) {
      mostrarErro("Erro de conexão com o servidor. Tente novamente.");
    } finally {
      btnSalvar.disabled = false;
    }
  });

  atualizarTodasAsCores();

});