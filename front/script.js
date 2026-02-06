const API_BASE = "http://localhost:8000";

// --- CONTROLE DE INTERFACE ---
function abrirModal(id) {
    document.getElementById(id).style.display = "block";
}

function fecharModal(id) {
    document.getElementById(id).style.display = "none";
    // Limpa os campos de resultado ao fechar
    const results = document.querySelectorAll('.result-area');
    results.forEach(res => {
        res.style.display = 'none';
        res.innerText = '';
        res.style.color = ""; // Reseta a cor para o padrão
    });
}

window.onclick = (e) => {
    if (e.target.className === "modal") fecharModal(e.target.id);
};

// Exibição condicional de campos no cadastro
document.getElementById("is_correntista").onchange = function() {
    document.getElementById("extra_banco").style.display = this.checked ? "block" : "none";
};
document.getElementById("is_investidor").onchange = function() {
    document.getElementById("extra_investimento").style.display = this.checked ? "block" : "none";
};

// --- 1. BUSCA POR NOME ---
const btnNome = document.getElementById("btnBuscarClientePorNome");
if (btnNome) {
    btnNome.onclick = async () => {
        const nome = document.getElementById("busca_nome").value.trim();
        const resDiv = document.getElementById("output");
        resDiv.style.display = "block";
        resDiv.innerText = "Buscando...";

        try {
            const response = await fetch(`${API_BASE}/clientes/busca/nome?nome=${encodeURIComponent(nome)}`);
            const data = await response.json();
            resDiv.innerText = response.ok ? JSON.stringify(data, null, 2) : "Erro: " + data.detail;
        } catch (err) {
            resDiv.innerText = "Erro de conexão com o servidor.";
        }
    };
}

// --- 2. CÁLCULO DE SCORE ---
document.getElementById("formScore").onsubmit = async (e) => {
    e.preventDefault();
    const documento = document.getElementById("score_input").value.trim();
    const resDiv = document.getElementById("resScore");
    resDiv.style.display = "block";
    resDiv.innerText = "Calculando...";

    try {
        const response = await fetch(`${API_BASE}/contas/score/${documento}`);
        const data = await response.json();
        if (response.ok) {
            resDiv.innerText = `Pontuação de Crédito: ${data.score_credito}`;
        } else {
            resDiv.innerText = "Erro: " + data.detail;
        }
    } catch (err) {
        resDiv.innerText = "Erro de conexão.";
    }
};

// --- 3. EXCLUIR CADASTRO ---
document.getElementById("formExcluir").onsubmit = async (e) => {
    e.preventDefault();
    const documento = document.getElementById("excluir_doc").value.trim();
    const resDiv = document.getElementById("resExcluir");
    resDiv.style.display = "block";
    resDiv.innerText = "Processando exclusão...";

    try {
        const response = await fetch(`${API_BASE}/clientes/excluir/${documento}`, { method: 'DELETE' });
        const data = await response.json();

        if (response.ok) {
            resDiv.style.color = "#2ecc71";
            resDiv.innerText = typeof data === 'string' ? data : "Cadastro encerrado com sucesso!";
            e.target.reset();
        } else {
            resDiv.style.color = "#e74c3c";
            resDiv.innerText = "Erro: " + (data.detail || "Falha na exclusão.");
        }
    } catch (err) {
        resDiv.style.color = "#e74c3c";
        resDiv.innerText = "Erro de conexão ao servidor.";
    }
};

// --- 4. ATUALIZAR SALDO ---
document.getElementById("formSaldo").onsubmit = async (e) => {
    e.preventDefault();
    const conta = document.getElementById("s_conta").value.trim();
    const valor = document.getElementById("s_valor").value;
    const resDiv = document.getElementById("resSaldo");
    resDiv.style.display = "block";

    try {
        const res = await fetch(`${API_BASE}/contas/atualizar-saldo/${conta}?novo_saldo=${valor}`, { method: 'PATCH' });
        const data = await res.json();
        resDiv.innerText = res.ok ? "Saldo atualizado!" : "Erro: " + data.detail;
    } catch (err) {
        resDiv.innerText = "Erro de conexão.";
    }
};

// --- 5. CADASTRO DE CLIENTE (CORRIGIDO) ---
document.getElementById("formCadastro").onsubmit = async (e) => {
    e.preventDefault();
    const resDiv = document.getElementById("resCadastro");
    resDiv.style.display = "block";
    resDiv.style.color = ""; // Reseta cor
    resDiv.innerText = "Cadastrando...";

    const isCorrentista = document.getElementById("is_correntista").checked;
    const isInvestidor = document.getElementById("is_investidor").checked;

    // Criamos o objeto de parâmetros base
    const paramsObj = {
        nome: document.getElementById("reg_nome").value,
        telefone: document.getElementById("reg_tel").value,
        documento: document.getElementById("reg_doc").value,
        correntista: isCorrentista,
        investidor: isInvestidor
    };

    // Adiciona opcionais se for investidor para evitar erro 422 no FastAPI
    if (isInvestidor) {
        paramsObj.email = document.getElementById("reg_email")?.value || "";
        paramsObj.patrimonio = document.getElementById("reg_patrimonio")?.value || 0;
        paramsObj.perfil = document.getElementById("reg_perfil")?.value || "CONSERVADOR";
    }

    const params = new URLSearchParams(paramsObj);

    try {
        // Como o app.py espera Query Params no @app.post('/clientes'), enviamos na URL
        const res = await fetch(`${API_BASE}/clientes?${params.toString()}`, { 
            method: 'POST',
            headers: { 'Accept': 'application/json' }
        });
        
        const data = await res.json();

        if (res.ok) {
            resDiv.style.color = "#2ecc71";
            resDiv.innerText = "Sucesso! Cliente cadastrado.";
            e.target.reset(); // Limpa o form
            setTimeout(() => fecharModal("modalCadastro"), 2000);
        } else {
            resDiv.style.color = "#e74c3c";
            resDiv.innerText = "Erro: " + (data.detail || "Erro no cadastro.");
        }
    } catch (err) {
        resDiv.style.color = "#e74c3c";
        resDiv.innerText = "Erro de conexão.";
    }
};

// --- 6. BUSCA DOCUMENTO & CONTA ---
document.getElementById("formBuscaDoc").onsubmit = async (e) => {
    e.preventDefault();
    const doc = document.getElementById("b_doc").value.trim();
    const resDiv = document.getElementById("resBusca");
    resDiv.style.display = "block";
    try {
        const res = await fetch(`${API_BASE}/clientes/${doc}`);
        const data = await res.json();
        resDiv.innerText = res.ok ? JSON.stringify(data, null, 2) : "Não encontrado.";
    } catch (err) { resDiv.innerText = "Erro de conexão."; }
};

document.getElementById("formConta").onsubmit = async (e) => {
    e.preventDefault();
    const doc = document.getElementById("c_doc").value.trim();
    const resDiv = document.getElementById("resConta");
    resDiv.style.display = "block";
    try {
        const res = await fetch(`${API_BASE}/contas/numero/${doc}`);
        const data = await res.json();
        // Ajuste para bater com o retorno {'Conta: ': valor} do app.py
        resDiv.innerText = data['Conta: '] ? `Conta: ${data['Conta: ']}` : "Não localizada.";
    } catch (err) { resDiv.innerText = "Erro de conexão."; }
};