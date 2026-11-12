document.addEventListener("DOMContentLoaded", function () {
    const painel = document.getElementById("notificationPanel");
    const sino = document.getElementById("notificationToggle");
    if (!painel || !sino) {
        return;
    }

    const lista = document.getElementById("notificationList");
    const contador = document.getElementById("notificationUnreadCount");
    const filtros = painel.querySelector(".notification-filters");
    const estadoVazio = document.getElementById("notificationEmpty");
    const status = document.getElementById("notificationActionStatus");
    const avisos = document.getElementById("notificationToasts");
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content
        || document.querySelector('input[name="csrfmiddlewaretoken"]')?.value
        || "";
    const grupos = new Map(
        Array.from(painel.querySelectorAll("[data-group]")).map(function (grupo) {
            return [grupo.dataset.group, grupo];
        }),
    );
    const idsConhecidos = new Set(
        Array.from(lista.querySelectorAll("[data-id]")).map(function (item) {
            return item.dataset.id;
        }),
    );
    let filtroAtivo = "todas";
    let consultaEmAndamento = false;
    let primeiraConsulta = true;
    let estadoAnterior = "";

    /* Converte uma data ISO em um rótulo curto e acessível para a interface. */
    function formatarDataRelativa(isoString) {
        const data = new Date(isoString);
        if (Number.isNaN(data.getTime())) {
            return "";
        }

        const agora = new Date();
        const diferencaMinutos = Math.floor((agora - data) / 60000);
        if (diferencaMinutos < 1) {
            return "agora";
        }
        if (diferencaMinutos < 60) {
            return `há ${diferencaMinutos} min`;
        }
        const diferencaHoras = Math.floor(diferencaMinutos / 60);
        if (diferencaHoras < 24 && data.toDateString() === agora.toDateString()) {
            return `há ${diferencaHoras} h`;
        }

        const ontem = new Date(agora);
        ontem.setDate(agora.getDate() - 1);
        if (data.toDateString() === ontem.toDateString()) {
            return "ontem";
        }
        return data.toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
        });
    }

    /* Coloca os cartões em Hoje, Ontem ou Mais antigas e esconde grupos vazios. */
    function agruparPorData() {
        const agora = new Date();
        const hoje = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate());
        const ontem = new Date(hoje);
        ontem.setDate(hoje.getDate() - 1);
        const destino = {hoje: [], ontem: [], antigas: []};

        lista.querySelectorAll("[data-id]").forEach(function (item) {
            const data = new Date(item.dataset.data);
            const dia = new Date(data.getFullYear(), data.getMonth(), data.getDate());
            const chave = dia.getTime() === hoje.getTime()
                ? "hoje"
                : dia.getTime() === ontem.getTime()
                    ? "ontem"
                    : "antigas";
            destino[chave].push(item);

            const elementoData = item.querySelector("[data-relative-time]");
            if (elementoData) {
                elementoData.textContent = formatarDataRelativa(item.dataset.data);
                elementoData.title = data.toLocaleString("pt-BR", {
                    timeZone: "America/Sao_Paulo",
                    dateStyle: "full",
                    timeStyle: "short",
                });
            }
            atualizarBadgePrazo(item);
        });

        Object.entries(destino).forEach(function ([chave, itens]) {
            const grupo = grupos.get(chave);
            const listaGrupo = grupo?.querySelector("[data-group-list]");
            if (!grupo || !listaGrupo) {
                return;
            }
            itens.forEach(function (item) {
                listaGrupo.appendChild(item);
            });
            grupo.hidden = itens.every(function (item) {
                return item.hidden;
            });
        });
    }

    /* Mostra o contador de não lidas no cabeçalho e no sino. */
    function atualizarContadorNaoLidas() {
        const naoLidas = lista.querySelectorAll('[data-lida="false"]').length;
        contador.textContent = String(naoLidas);
        sino.dataset.unreadCount = String(naoLidas);
        sino.setAttribute("aria-label", `Notificações: ${naoLidas} não lidas`);

        let badge = sino.querySelector(".notification-badge");
        if (naoLidas > 0) {
            if (!badge) {
                badge = document.createElement("span");
                badge.className = "notification-badge";
                badge.setAttribute("aria-hidden", "true");
                sino.appendChild(badge);
            }
            badge.textContent = String(naoLidas);
        } else {
            badge?.remove();
        }
    }

    /* Persiste a alternância do estado e atualiza o cartão e seus contadores. */
    async function alternarLida(id, estadoForcado) {
        const item = lista.querySelector(`[data-id="${CSS.escape(id)}"]`);
        if (!item) {
            return;
        }
        const novaLida = estadoForcado ?? item.dataset.lida !== "true";
        if (novaLida === (item.dataset.lida === "true")) {
            return;
        }
        const url = novaLida ? item.dataset.urlLida : item.dataset.urlNaoLida;
        if (url) {
            const resposta = await enviarPost(url);
            if (!resposta.ok) {
                throw new Error("Não foi possível atualizar o estado da notificação.");
            }
        }

        definirEstadoLido(item, novaLida);
        atualizarContadorNaoLidas();
        mostrarEstadoVazio();
    }

    /* Define estado, rótulos e aparência do cartão sem tocar nos seus dados. */
    function definirEstadoLido(item, lida) {
        item.dataset.lida = String(lida);
        item.classList.toggle("is-read", lida);
        item.querySelectorAll('[data-notification-action="toggle-read"]').forEach(function (botao) {
            const acao = lida ? "Marcar como não lida" : "Marcar como lida";
            botao.setAttribute("aria-label", acao);
            botao.title = acao;
            if (botao.matches(".notification-action-button")) {
                botao.innerHTML = lida
                    ? '<i class="bi bi-circle" aria-hidden="true"></i>'
                    : '<i class="bi bi-check2" aria-hidden="true"></i>';
            } else {
                botao.textContent = acao;
            }
        });
    }

    /* Marca como lidas todas as notificações atualmente visíveis no filtro ativo. */
    async function marcarTodasComoLidas() {
        const itens = Array.from(lista.querySelectorAll('[data-id][data-lida="false"]'))
            .filter(function (item) { return !item.hidden; });
        try {
            for (const item of itens) {
                if (!item.dataset.urlLida) {
                    continue;
                }
                const resposta = await enviarPost(item.dataset.urlLida);
                if (!resposta.ok) {
                    throw new Error("Não foi possível marcar todas como lidas.");
                }
                definirEstadoLido(item, true);
            }
            atualizarContadorNaoLidas();
            filtrarNotificacoes(filtroAtivo);
        } catch (erro) {
            mostrarStatus(erro.message);
        }
    }

    /* Remove um cartão depois de confirmar a exclusão no endpoint existente. */
    async function excluirNotificacao(id) {
        const item = lista.querySelector(`[data-id="${CSS.escape(id)}"]`);
        if (!item || !item.dataset.urlExcluir) {
            return;
        }
        try {
            const resposta = await enviarPost(item.dataset.urlExcluir, true);
            const resultado = await resposta.json();
            if (!resposta.ok || !resultado.success) {
                throw new Error("Não foi possível excluir esta notificação.");
            }
            item.classList.add("is-removing");
            window.setTimeout(function () {
                item.remove();
                agruparPorData();
                atualizarContadorNaoLidas();
                mostrarEstadoVazio();
            }, 180);
        } catch (erro) {
            mostrarStatus(erro.message);
        }
    }

    /* Aplica o filtro ativo pelos atributos data-tipo e data-lida. */
    function filtrarNotificacoes(filtro) {
        filtroAtivo = filtro;
        filtros.querySelectorAll("[data-filter]").forEach(function (botao) {
            const ativo = botao.dataset.filter === filtro;
            botao.classList.toggle("is-active", ativo);
            botao.setAttribute("aria-pressed", String(ativo));
        });

        lista.querySelectorAll("[data-id]").forEach(function (item) {
            const tipo = item.dataset.tipo;
            const corresponde = filtro === "todas"
                || (filtro === "nao-lidas" && item.dataset.lida === "false")
                || (filtro === "acoes" && ["acao", "etapa"].includes(tipo))
                || (filtro === "sistema" && tipo === "senha");
            item.hidden = !corresponde;
        });
        agruparPorData();
        mostrarEstadoVazio();
    }

    /* Exibe o estado vazio somente quando não há itens no filtro selecionado. */
    function mostrarEstadoVazio() {
        const visiveis = Array.from(lista.querySelectorAll("[data-id]"))
            .some(function (item) { return !item.hidden; });
        estadoVazio.hidden = visiveis;
        lista.hidden = !visiveis;
    }

    /* Marca a notificação como lida antes de navegar ao seu destino. */
    async function tratarCliqueNoItem(evento) {
        if (evento.target.closest("[data-notification-action], .notification-mobile-menu")) {
            return;
        }
        const link = evento.target.closest("[data-item-link]");
        const item = link?.closest("[data-id]");
        if (!link || !item) {
            return;
        }

        evento.preventDefault();
        try {
            if (item.dataset.lida !== "true") {
                await alternarLida(item.dataset.id, true);
            }
            window.location.assign(link.href);
        } catch (erro) {
            mostrarStatus(erro.message);
        }
    }

    /* Atualiza um aviso de erro/resultado sem depender de alertas do navegador. */
    function mostrarStatus(mensagem) {
        status.textContent = mensagem;
        status.hidden = !mensagem;
    }

    /* Padroniza requisições POST com CSRF e informa o modo AJAX quando necessário. */
    function enviarPost(url, esperaJson = false) {
        const cabecalhos = {"X-CSRFToken": csrfToken};
        if (esperaJson) {
            cabecalhos["X-Requested-With"] = "XMLHttpRequest";
        }
        return fetch(url, {
            method: "POST",
            credentials: "same-origin",
            headers: cabecalhos,
        });
    }

    /* Calcula e colore o pill conforme a data-limite da ação ou etapa. */
    function atualizarBadgePrazo(item) {
        const badge = item.querySelector("[data-deadline-badge]");
        if (!badge || !item.dataset.prazo) {
            return;
        }
        const [ano, mes, dia] = item.dataset.prazo.split("-").map(Number);
        const vencimento = new Date(ano, mes - 1, dia);
        const hoje = new Date();
        const hojeLocal = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
        const dias = Math.round((vencimento - hojeLocal) / 86400000);
        item.classList.toggle("is-due-tomorrow", dias === 1);
        if (dias < 0) {
            badge.textContent = `Atrasado ${Math.abs(dias)}d`;
        } else if (dias === 0) {
            badge.textContent = "Vence hoje";
        } else if (dias === 1) {
            badge.textContent = "Vence amanhã";
        } else {
            badge.textContent = `Vence em ${dias}d`;
        }
    }

    /* Cria elementos de notificação usando textContent para evitar HTML não confiável. */
    function criarItemNotificacao(notificacao) {
        const tipo = notificacao.alvo_tipo === "solicitacao_senha"
            ? "senha"
            : notificacao.alvo_tipo;
        const urgencia = tipo === "senha"
            ? "seguranca"
            : notificacao.urgencia;
        const item = document.createElement("li");
        item.className = `notification-card${notificacao.lida ? " is-read" : ""}`;
        item.setAttribute("role", "listitem");
        Object.assign(item.dataset, {
            id: notificacao.id,
            notificationId: notificacao.id,
            lida: String(notificacao.lida),
            tipo: tipo,
            urgencia: urgencia,
            data: notificacao.criado_em,
            prazo: notificacao.prazo || "",
            urlLida: notificacao.url || "",
            urlNaoLida: notificacao.url_nao_lida || "",
            urlExcluir: notificacao.remover_url || "",
            urlDestino: notificacao.destino_url || "",
        });

        const link = document.createElement("a");
        link.className = "notification-main-link";
        link.href = notificacao.destino_url || "#";
        link.dataset.itemLink = "";
        const icone = document.createElement("span");
        icone.className = `notification-icon notification-icon-${urgencia}`;
        icone.setAttribute("aria-hidden", "true");
        const glyph = document.createElement("i");
        glyph.className = tipo === "senha"
            ? "bi bi-key-fill"
            : urgencia === "atrasado"
                ? "bi bi-calendar-x-fill"
                : tipo === "acao" ? "bi bi-flag-fill" : "bi bi-list-check";
        icone.appendChild(glyph);

        const conteudo = document.createElement("span");
        conteudo.className = "notification-content";
        const titulo = document.createElement("strong");
        titulo.className = "notification-title";
        titulo.textContent = notificacao.titulo;
        const descricao = document.createElement("span");
        descricao.className = "notification-description";
        descricao.textContent = notificacao.mensagem;
        const meta = document.createElement("span");
        meta.className = "notification-meta";
        const data = document.createElement("time");
        data.className = "notification-relative-date";
        data.dataset.relativeTime = "";
        data.dateTime = notificacao.criado_em;
        meta.appendChild(data);
        if (tipo !== "senha") {
            const prazo = document.createElement("span");
            prazo.className = "notification-deadline-badge";
            prazo.dataset.deadlineBadge = "";
            meta.appendChild(prazo);
        }
        conteudo.append(titulo, descricao, meta);
        link.append(icone, conteudo);
        item.appendChild(link);

        const ponto = document.createElement("span");
        ponto.className = "notification-unread-dot";
        ponto.setAttribute("aria-label", "Não lida");
        item.appendChild(ponto);
        const acoes = document.createElement("div");
        acoes.className = "notification-item-actions";
        acoes.setAttribute("aria-label", "Ações da notificação");
        acoes.appendChild(criarBotaoAcao(
            notificacao.lida ? "toggle-read" : "toggle-read",
            notificacao.lida ? "Marcar como não lida" : "Marcar como lida",
            notificacao.lida ? "bi-circle" : "bi-check2",
        ));
        if (tipo !== "senha") {
            acoes.appendChild(criarBotaoAcao("excluir", "Excluir", "bi-trash3"));
        }
        item.appendChild(acoes);

        const menu = document.createElement("details");
        menu.className = "notification-mobile-menu";
        const resumo = document.createElement("summary");
        resumo.setAttribute("aria-label", "Abrir ações da notificação");
        resumo.innerHTML = '<i class="bi bi-three-dots" aria-hidden="true"></i>';
        const menuAcoes = document.createElement("div");
        menuAcoes.className = "notification-mobile-menu-actions";
        menuAcoes.appendChild(criarBotaoAcao(
            "toggle-read",
            notificacao.lida ? "Marcar como não lida" : "Marcar como lida",
            notificacao.lida ? "bi-circle" : "bi-check2",
        ));
        if (tipo !== "senha") {
            menuAcoes.appendChild(criarBotaoAcao("excluir", "Excluir", "bi-trash3"));
        }
        menu.append(resumo, menuAcoes);
        item.appendChild(menu);

        return item;
    }

    /* Constrói botões de ação sem listeners individuais. */
    function criarBotaoAcao(acao, rotulo, icone) {
        const botao = document.createElement("button");
        botao.type = "button";
        botao.className = "notification-action-button";
        botao.dataset.notificationAction = acao;
        botao.setAttribute("aria-label", rotulo);
        botao.title = rotulo;
        botao.innerHTML = `<i class="bi ${icone}" aria-hidden="true"></i>`;
        return botao;
    }

    /* Atualiza a lista após polling e agrupa os itens no contêiner correto. */
    function renderizarNotificacoes(notificacoes) {
        const fragmento = document.createDocumentFragment();
        notificacoes.forEach(function (notificacao) {
            fragmento.appendChild(criarItemNotificacao(notificacao));
        });
        lista.querySelectorAll("[data-id]").forEach(function (item) { item.remove(); });
        grupos.forEach(function (grupo) {
            grupo.querySelector("[data-group-list]")?.replaceChildren();
        });
        lista.appendChild(fragmento);
        agruparPorData();
        filtrarNotificacoes(filtroAtivo);
        atualizarContadorNaoLidas();
        mostrarEstadoVazio();
    }

    /* Mostra um aviso animado quando o polling encontra uma nova notificação. */
    function mostrarAviso(notificacao) {
        const urgencia = notificacao.urgencia || "info";
        const aviso = document.createElement("article");
        aviso.className = `notification-toast notification-toast-${urgencia}`;
        aviso.setAttribute("role", "status");
        const icone = document.createElement("span");
        icone.className = "notification-toast-icon";
        const glyph = document.createElement("i");
        glyph.className = notificacao.alvo_tipo === "solicitacao_senha"
            ? "bi bi-key-fill"
            : urgencia === "atrasado"
                ? "bi bi-calendar-x-fill"
                : "bi bi-bell-fill";
        glyph.setAttribute("aria-hidden", "true");
        icone.appendChild(glyph);
        const conteudo = document.createElement("span");
        conteudo.className = "notification-toast-copy";
        const titulo = document.createElement("strong");
        titulo.textContent = notificacao.titulo;
        const descricao = document.createElement("span");
        descricao.textContent = notificacao.mensagem;
        conteudo.append(titulo, descricao);
        const fechar = document.createElement("button");
        fechar.type = "button";
        fechar.className = "notification-toast-close";
        fechar.setAttribute("aria-label", "Fechar notificação");
        fechar.innerHTML = '<i class="bi bi-x-lg" aria-hidden="true"></i>';
        aviso.append(icone, conteudo, fechar);
        avisos.appendChild(aviso);

        const dispensar = function () {
            if (!aviso.isConnected) {
                return;
            }
            aviso.classList.add("notification-toast-leaving");
            aviso.addEventListener("animationend", function () { aviso.remove(); }, {once: true});
        };
        fechar.addEventListener("click", dispensar);
        window.setTimeout(dispensar, 6500);
        sino.classList.remove("notification-toggle-new");
        void sino.offsetWidth;
        sino.classList.add("notification-toggle-new");
        window.setTimeout(function () {
            sino.classList.remove("notification-toggle-new");
        }, 700);
    }

    /* Busca todas as notificações e atualiza o popover sem recarregar a página. */
    async function atualizarNotificacoes() {
        if (consultaEmAndamento || document.visibilityState === "hidden") {
            return;
        }
        consultaEmAndamento = true;
        try {
            const resposta = await fetch(painel.dataset.refreshUrl, {
                credentials: "same-origin",
                headers: {"X-Requested-With": "XMLHttpRequest"},
            });
            if (!resposta.ok) {
                throw new Error("Não foi possível atualizar as notificações.");
            }
            const dados = await resposta.json();
            if (!Array.isArray(dados.notifications)) {
                throw new Error("A resposta de notificações é inválida.");
            }

            const estado = JSON.stringify(dados.notifications);
            if (!primeiraConsulta) {
                dados.notifications.forEach(function (notificacao) {
                    if (!idsConhecidos.has(notificacao.id) && !notificacao.lida) {
                        mostrarAviso(notificacao);
                    }
                });
            }
            idsConhecidos.clear();
            dados.notifications.forEach(function (notificacao) {
                idsConhecidos.add(notificacao.id);
            });
            primeiraConsulta = false;
            if (estado !== estadoAnterior) {
                renderizarNotificacoes(dados.notifications);
                estadoAnterior = estado;
            }
        } catch (erro) {
            console.error(erro);
            mostrarStatus("Não foi possível atualizar as notificações.");
        } finally {
            consultaEmAndamento = false;
        }
    }

    /* Roteia cliques nos cartões e suas ações por delegação no container da lista. */
    function delegarCliqueNaLista(evento) {
        const botao = evento.target.closest("[data-notification-action]");
        const item = evento.target.closest("[data-id]");
        if (botao && item) {
            evento.preventDefault();
            const acao = botao.dataset.notificationAction;
            if (acao === "toggle-read") {
                alternarLida(item.dataset.id).catch(function (erro) {
                    mostrarStatus(erro.message);
                });
            } else if (acao === "excluir") {
                excluirNotificacao(item.dataset.id);
            }
            botao.closest("details")?.removeAttribute("open");
            return;
        }
        tratarCliqueNoItem(evento);
    }

    /* Liga filtros, leitura em lote, navegação, polling e acessibilidade por teclado. */
    function inicializar() {
        lista.addEventListener("click", delegarCliqueNaLista);
        filtros.addEventListener("click", function (evento) {
            const botao = evento.target.closest("[data-filter]");
            if (botao) {
                filtrarNotificacoes(botao.dataset.filter);
            }
        });
        document.getElementById("notificationMarkAll")
            .addEventListener("click", marcarTodasComoLidas);
        document.getElementById("notificationShowAll")
            .addEventListener("click", function () {
                filtrarNotificacoes("todas");
                document.querySelector(".notification-scroll-area")
                    ?.scrollTo({top: 0, behavior: "smooth"});
                lista.querySelector("[data-id] a")?.focus({preventScroll: true});
            });

        sino.addEventListener("click", function () {
            const aberto = sino.getAttribute("aria-expanded") === "true";
            painel.hidden = aberto;
            sino.setAttribute("aria-expanded", String(!aberto));
            if (!aberto) {
                atualizarNotificacoes();
            }
        });
        document.addEventListener("click", function (evento) {
            if (!painel.contains(evento.target) && !sino.contains(evento.target)) {
                painel.hidden = true;
                sino.setAttribute("aria-expanded", "false");
            }
        });
        document.addEventListener("keydown", function (evento) {
            if (evento.key === "Escape" && !painel.hidden) {
                painel.hidden = true;
                sino.setAttribute("aria-expanded", "false");
                sino.focus();
            }
        });

        agruparPorData();
        filtrarNotificacoes("todas");
        atualizarContadorNaoLidas();
        atualizarNotificacoes();
        window.setInterval(atualizarNotificacoes, 10000);
    }

    inicializar();
});
