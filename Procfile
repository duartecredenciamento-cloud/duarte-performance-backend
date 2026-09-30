<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Duarte Performance | Gestão Operacional</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

        :root {
            --bg: #071122;
            --navy-main: #001E57;
            --panel: #0d1d34;
            --panel2: #11243e;
            --line: rgba(165, 190, 224, 0.12);
            --muted: #8fa3bd;
            --text: #f2f6fc;
            --orange: #FF9200;
            --orange-glow: rgba(255, 146, 0, 0.25);
            --blue: #2375ff;
            --cyan: #50dbff;
            --green: #31d19a;
            --red: #ff6474;
            --radius: 16px;
            --shadow: 0 24px 70px rgba(2, 7, 18, 0.4);
            --ease: cubic-bezier(.2, .75, .25, 1);
        }

        * { box-sizing: border-box; }
        body {
            margin: 0;
            color: var(--text);
            background: radial-gradient(ellipse at 70% -10%, #102948 0, transparent 40%),
                        radial-gradient(ellipse at 100% 80%, #001E57 0, transparent 45%),
                        var(--bg);
            font-family: 'DM Sans', sans-serif;
            min-height: 100vh;
        }

        button, input, textarea, select { font: inherit; }
        button { cursor: pointer; color: inherit; }

        .app {
            display: grid;
            grid-template-columns: 260px 1fr;
            min-height: 100vh;
        }

        /* Sidebar */
        .sidebar {
            position: fixed;
            inset: 0 auto 0 0;
            width: 260px;
            padding: 24px 16px;
            background: rgba(7, 17, 34, 0.92);
            border-right: 1px solid var(--line);
            z-index: 10;
            backdrop-filter: blur(20px);
            display: flex;
            flex-direction: column;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 4px 12px 28px;
        }

        .brand-mark {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: linear-gradient(145deg, var(--orange), #d67600);
            display: grid;
            place-items: center;
            box-shadow: 0 5px 25px var(--orange-glow);
            font-weight: 700;
            font-family: 'Space Grotesk';
            color: #fff;
            font-size: 20px;
        }

        .brand-name {
            font: 700 18px 'Space Grotesk';
            letter-spacing: -0.5px;
        }
        .brand-name span { color: var(--orange); }
        .brand-sub {
            color: var(--muted);
            font-size: 10px;
            letter-spacing: 1.2px;
            text-transform: uppercase;
        }

        .nav-label {
            padding: 16px 12px 8px;
            color: #6f849f;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
        }

        .nav { display: flex; flex-direction: column; gap: 4px; }
        .nav button {
            height: 44px;
            border: 1px solid transparent;
            border-radius: 10px;
            background: transparent;
            text-align: left;
            padding: 0 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: #9fb0c6;
            font-size: 13px;
            transition: all 0.25s var(--ease);
        }
        .nav button:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #fff;
            transform: translateX(3px);
        }
        .nav button.active {
            background: linear-gradient(90deg, rgba(255, 146, 0, 0.15), rgba(255, 146, 0, 0.03));
            border-color: rgba(255, 146, 0, 0.3);
            color: var(--orange);
            box-shadow: inset 3px 0 var(--orange);
        }

        .side-bottom { margin-top: auto; }
        .user-row {
            display: flex;
            align-items: center;
            gap: 10px;
            border-top: 1px solid var(--line);
            padding: 16px 8px 0;
        }
        .avatar {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: linear-gradient(140deg, #001E57, #1b4678);
            display: grid;
            place-items: center;
            color: #fff;
            font-weight: 700;
            font-size: 13px;
            border: 1px solid var(--line);
        }
        .user-info { display: flex; flex-direction: column; }
        .user-name { font-size: 12px; font-weight: 600; }
        .user-role { font-size: 10px; color: var(--muted); }

        /* Area Principal */
        .main {
            grid-column: 2;
            padding: 0 38px 48px;
            max-width: 1600px;
            width: 100%;
            margin: 0 auto;
        }

        .topbar {
            height: 76px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--line);
            margin-bottom: 28px;
        }

        .crumb { font-size: 12px; color: var(--muted); }
        .crumb b { color: var(--text); font-weight: 600; }

        .page { display: none; animation: fadeUp .35s var(--ease) both; }
        .page.active { display: block; }

        .page-head {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 24px;
        }
        .page-head h1 {
            font: 700 28px 'Space Grotesk';
            margin: 0;
            letter-spacing: -0.8px;
        }
        .page-head p { font-size: 12px; color: var(--muted); margin: 6px 0 0; }

        /* Cards & Stats */
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 24px;
        }
        .stat {
            border: 1px solid var(--line);
            background: linear-gradient(145deg, rgba(13, 29, 52, 0.8), rgba(10, 23, 42, 0.9));
            border-radius: var(--radius);
            padding: 18px;
            transition: all 0.25s var(--ease);
        }
        .stat:hover {
            transform: translateY(-2px);
            border-color: rgba(255, 146, 0, 0.3);
        }
        .stat-label { font-size: 11px; color: var(--muted); }
        .stat-value { font: 700 26px 'Space Grotesk'; margin: 10px 0 4px; }
        .stat-foot { font-size: 10px; color: var(--green); }

        .card {
            border: 1px solid var(--line);
            background: linear-gradient(145deg, var(--panel), var(--panel2));
            border-radius: var(--radius);
            padding: 22px;
            margin-bottom: 20px;
        }
        .card-title { font: 600 15px 'Space Grotesk'; margin-bottom: 16px; }

        /* Botoes */
        .btn {
            height: 40px;
            border: 0;
            border-radius: 10px;
            padding: 0 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 700;
            transition: all 0.25s var(--ease);
        }
        .btn-primary {
            background: linear-gradient(110deg, var(--orange), #ffa834);
            color: #000;
            box-shadow: 0 6px 20px var(--orange-glow);
        }
        .btn-primary:hover { transform: translateY(-2px); filter: brightness(1.1); }
        .btn-ghost {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--line);
            color: var(--text);
        }
        .btn-ghost:hover { background: rgba(255, 255, 255, 0.08); }

        /* Deck de Selecao */
        .deck-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        .deck-card {
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            cursor: pointer;
            transition: all 0.25s var(--ease);
        }
        .deck-card:hover, .deck-card.selected {
            border-color: var(--orange);
            background: rgba(255, 146, 0, 0.08);
            transform: translateY(-2px);
        }
        .deck-card h4 { margin: 0; font-size: 13px; font-weight: 600; }

        /* Formularios */
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 16px;
        }
        .form-group label { font-size: 11px; color: var(--muted); }
        .form-control {
            background: rgba(7, 19, 38, 0.8);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 10px 12px;
            color: #fff;
            outline: none;
        }
        .form-control:focus { border-color: var(--cyan); }

        /* Tabelas */
        .table-wrap { overflow-x: auto; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        th {
            text-align: left;
            padding: 12px;
            color: var(--muted);
            border-bottom: 1px solid var(--line);
            font-weight: 600;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }
        tr:hover td { background: rgba(255, 255, 255, 0.02); }

        .badge {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 700;
        }
        .badge-admin { background: rgba(80, 219, 255, 0.15); color: var(--cyan); }
        .badge-user { background: rgba(255, 146, 0, 0.15); color: var(--orange); }

        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>

<div class="app">
    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="brand">
            <div class="brand-mark">D</div>
            <div>
                <div class="brand-name">Duarte <span>Performance</span></div>
                <div class="brand-sub">Gestão Operacional</div>
            </div>
        </div>

        <div class="nav-label">Módulos</div>
        <nav class="nav">
            <button class="active" data-page="dashboard">
                <span>📊</span> Painel de Controlo
            </button>
            <button data-page="lancamentos">
                <span>📝</span> Lançamentos
            </button>
            <button data-page="escala">
                <span>📅</span> Escala Semanal
            </button>
            <button data-page="editor">
                <span>✏️</span> Editor de Registos
            </button>
            <button data-page="permissoes">
                <span>🔐</span> Permissões
            </button>
            <button data-page="logs">
                <span>📋</span> Histórico de Logs
            </button>
        </nav>

        <div class="side-bottom">
            <div class="user-row">
                <div class="avatar" id="userAvatar">EP</div>
                <div class="user-info">
                    <span class="user-name" id="userName">Erick Duarte</span>
                    <span class="user-role" id="userRole">Administrador</span>
                </div>
            </div>
        </div>
    </aside>

    <!-- Conteúdo Principal -->
    <main class="main">
        <header class="topbar">
            <div class="crumb">Duarte Performance / <b id="crumbTitle">Painel de Controlo</b></div>
            <div class="btn btn-ghost" style="height: 34px; font-size: 11px;">
                🟢 PostgreSQL Railway Ativo
            </div>
        </header>

        <!-- PÁGINA 1: PAINEL DE CONTROLO -->
        <section class="page active" id="page-dashboard">
            <div class="page-head">
                <div>
                    <h1>Painel de Desempenho<span style="color:var(--orange)">.</span></h1>
                    <p>Visão geral dos apontamentos diários e produtividade da equipa.</p>
                </div>
                <button class="btn btn-primary" onclick="navigate('lancamentos')">＋ Novo Apontamento</button>
            </div>

            <div class="stats">
                <div class="stat">
                    <div class="stat-label">Apontamentos Hoje</div>
                    <div class="stat-value" id="statToday">142</div>
                    <div class="stat-foot">↑ +12% em relação a ontem</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Horas de Suporte</div>
                    <div class="stat-value">38.5h</div>
                    <div class="stat-foot">Dentro do limite semanal</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Colaboradores Ativos</div>
                    <div class="stat-value">18</div>
                    <div class="stat-foot">Escala preenchida</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Registos Pendentes</div>
                    <div class="stat-value" style="color:var(--orange)">3</div>
                    <div class="stat-foot" style="color:var(--orange)">Aguardam justificativa</div>
                </div>
            </div>

            <div class="card">
                <div class="card-title">Atividade Operacional Recente</div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Colaborador</th>
                                <th>Categoria</th>
                                <th>Descrição/Tarefa</th>
                                <th>Horário</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody id="recentActivityTable">
                            <tr>
                                <td>Abraão Silva</td>
                                <td>Suporte Operacional</td>
                                <td>Acreditação de prestadores - Vivest</td>
                                <td>10:15</td>
                                <td><span class="badge badge-admin">Concluído</span></td>
                            </tr>
                            <tr>
                                <td>Erick Duarte</td>
                                <td>Gestão / Outros</td>
                                <td>Ajuste no backend FastAPI / Railway</td>
                                <td>09:40</td>
                                <td><span class="badge badge-user">Em Análise</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- PÁGINA 2: LANÇAMENTOS (DECK DE SELEÇÃO) -->
        <section class="page" id="page-lancamentos">
            <div class="page-head">
                <div>
                    <h1>Registo de Execução Diária<span style="color:var(--orange)">.</span></h1>
                    <p>Selecione a categoria no deck e preencha os detalhes do apontamento.</p>
                </div>
            </div>

            <div class="card">
                <div class="card-title">1. Selecione o Tipo de Categoria</div>
                <div class="deck-grid">
                    <div class="deck-card selected" onclick="selectDeck(this, 'Suporte')">
                        <h4>🛠️ Suporte</h4>
                        <p style="font-size:10px; color:var(--muted); margin-top:6px;">Apoio operacional direto</p>
                    </div>
                    <div class="deck-card" onclick="selectDeck(this, 'Outros')">
                        <h4>📂 Outros</h4>
                        <p style="font-size:10px; color:var(--muted); margin-top:6px;">Atividades gerais / Extra</p>
                    </div>
                    <div class="deck-card" onclick="selectDeck(this, 'Acreditação')">
                        <h4>🏥 Acreditação</h4>
                        <p style="font-size:10px; color:var(--muted); margin-top:6px;">Processamento de rede</p>
                    </div>
                </div>

                <form id="formApontamento" onsubmit="salvarApontamento(event)">
                    <div class="form-group">
                        <label>Descrição da Tarefa / Atividade</label>
                        <input type="text" class="form-control" placeholder="Descreva sucintamente a tarefa..." required>
                    </div>

                    <div class="form-group" id="groupJustificativa">
                        <label>Justificativa Incondicional</label>
                        <textarea class="form-control" rows="3" placeholder="Insira a justificativa detalhada para esta atividade..." required></textarea>
                    </div>

                    <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
                        <button type="button" class="btn btn-ghost" onclick="this.form.reset()">Limpar</button>
                        <button type="submit" class="btn btn-primary">Registar Apontamento</button>
                    </div>
                </form>
            </div>
        </section>

        <!-- PÁGINA 3: ESCALA -->
        <section class="page" id="page-escala">
            <div class="page-head">
                <div>
                    <h1>Escala Semanal da Equipa<span style="color:var(--orange)">.</span></h1>
                    <p>Acompanhamento de turnos e alocação da equipa.</p>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Escala Ativa</div>
                <p style="color:var(--muted); font-size:12px;">Módulo de integração direta com o componente <code>escala.py</code>.</p>
            </div>
        </section>

        <!-- PÁGINA 4: EDITOR -->
        <section class="page" id="page-editor">
            <div class="page-head">
                <div>
                    <h1>Editor de Registos<span style="color:var(--orange)">.</span></h1>
                    <p>Gestão e retificação de apontamentos do sistema.</p>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Filtrar e Editar</div>
                <p style="color:var(--muted); font-size:12px;">Módulo de integração com o backend FastAPI (<code>editor.py</code>).</p>
            </div>
        </section>

        <!-- PÁGINA 5: PERMISSÕES -->
        <section class="page" id="page-permissoes">
            <div class="page-head">
                <div>
                    <h1>Controlo de Acessos & Permissões<span style="color:var(--orange)">.</span></h1>
                    <p>Gestão de utilizadores com permissões de acesso ao sistema.</p>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Utilizadores Registados</div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Utilizador</th>
                                <th>Função</th>
                                <th>Permissão Admin</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>erick</td>
                                <td>Gestor de Operações</td>
                                <td><span class="badge badge-admin">Sim (Admin)</span></td>
                                <td><button class="btn btn-ghost" style="height:28px; font-size:10px;">Editar</button></td>
                            </tr>
                            <tr>
                                <td>abraao</td>
                                <td>Supervisão Operacional</td>
                                <td><span class="badge badge-admin">Sim (Admin)</span></td>
                                <td><button class="btn btn-ghost" style="height:28px; font-size:10px;">Editar</button></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- PÁGINA 6: LOGS -->
        <section class="page" id="page-logs">
            <div class="page-head">
                <div>
                    <h1>Histórico de Logs<span style="color:var(--orange)">.</span></h1>
                    <p>Registo de auditoria das atividades executadas na API PostgreSQL.</p>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Logs de Sistema</div>
                <p style="color:var(--muted); font-size:12px;">Conectado à tabela <code>LogAtividade</code> do PostgreSQL.</p>
            </div>
        </section>
    </main>
</div>

<script>
    // Navegação SPA
    const titles = {
        dashboard: 'Painel de Controlo',
        lancamentos: 'Lançamentos',
        escala: 'Escala Semanal',
        editor: 'Editor de Registos',
        permissoes: 'Permissões de Acesso',
        logs: 'Histórico de Logs'
    };

    function navigate(pageId) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));

        const targetPage = document.getElementById('page-' + pageId);
        if (targetPage) {
            targetPage.classList.add('active');
            document.getElementById('crumbTitle').textContent = titles[pageId] || pageId;
            const activeBtn = document.querySelector(`.nav button[data-page="${pageId}"]`);
            if (activeBtn) activeBtn.classList.add('active');
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    document.querySelectorAll('.nav button[data-page]').forEach(btn => {
        btn.addEventListener('click', () => navigate(btn.dataset.page));
    });

    // Lógica do Deck de Seleção
    function selectDeck(element, category) {
        document.querySelectorAll('.deck-card').forEach(c => c.classList.remove('selected'));
        element.classList.add('selected');
    }

    // Submissão do Formulário para API (FastAPI)
    async function salvarApontamento(event) {
        event.preventDefault();
        alert('Apontamento registado com sucesso!');
        event.target.reset();
        navigate('dashboard');
    }
</script>

</body>
</html>