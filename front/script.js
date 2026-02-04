const API_BASE = "http://localhost:8000";

// Funções de Controle de Interface
function abrirModal(id) {
    document.getElementById(id).style.display = "block";
}

function fecharModal(id) {
    document.getElementById(id).style.display = "none";
    const resultArea = document.getElementById(id).querySelector('.result-area');
    if (resultArea) resultArea.style.display = 'none';
}

// Fecha o modal ao clicar fora dele
window.onclick = (e) => {
    if (e.target.className === "modal") fecharModal(e.target.id);
};

// Exibição condicional de campos no cadastro
const checkCorrentista = document.getElementById("is_correntista");
const checkInvestidor = document.getElementById("is_investidor");

if (checkCorrentista) {
    checkCorrentista.onchange = function() {
        document.getElementById("extra_banco").style.display = this.checked ? "block" : "none";
    };
}

if (checkInvestidor) {
    checkInvestidor.onchange = function() {
        document.getElementById("extra_investimento").style.display = this.checked ? "block" : "none";
    };
}

// --- FUNÇÃO DE SCORE (AJUSTADA PARA A NOVA ROTA) ---
document.getElementById("formScore").onsubmit = async (e) => {
    e.preventDefault();
    const identificador = document.getElementById("score_input").value;
    const resDiv = document.getElementById("resScore");

    resDiv.style.display = "block";
    resDiv.innerText = "Processando consulta...";

    try {
        // AJUSTE AQUI: Mudamos de /score/id para /contas/score?id_cliente=...
        // Ou se você definiu como /contas/score/{id}, use: `${API_BASE}/contas/score/${identificador}`
        const response = await fetch(`${API_BASE}/contas/score?id_cliente=${identificador}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok) {
            const pontuacao = data.score_credito || data.score || "Não retornado";
            resDiv.innerText = `Resultado: ${pontuacao}`;
        } else {
            resDiv.innerText = "Erro: " + (data.detail || "Informação não localizada.");
        }
    } catch (err) {
        console.error("Erro na requisição:", err);
        resDiv.innerText = "Erro de conexão. Verifique o servidor e o CORS.";
    }
};

// --- CADASTRO DE CLIENTE ---
document.getElementById("formCadastro").onsubmit = async (e) => {
    e.preventDefault();
    const params = new URLSearchParams({
        nome: document.getElementById("reg_nome").value,
        telefone: document.getElementById("reg_tel").value,
        documento: document.getElementById("reg_doc").value,
        correntista: document.getElementById("is_correntista").checked,
        investidor: document.getElementById("is_investidor").checked
    });

    if (document.getElementById("is_investidor").checked) {
        params.append('email', document.getElementById("reg_email").value);
        params.append('patrimonio', document.getElementById("reg_patrimonio").value);
        params.append('perfil', document.getElementById("reg_perfil").value);
    }

    try {
        const res = await fetch(`${API_BASE}/clientes?${params.toString()}`, { method: 'POST' });
        if (res.ok) {
            alert("Cadastro realizado com sucesso.");
            fecharModal("modalCadastro");
            e.target.reset();
        } else {
            const errorData = await res.json();
            alert("Erro: " + errorData.detail);
        }
    } catch (err) {
        alert("Erro de conexão ao tentar cadastrar.");
    }
};

// --- BUSCA POR DOCUMENTO ---
document.getElementById("formBuscaDoc").onsubmit = async (e) => {
    e.preventDefault();
    const doc = document.getElementById("b_doc").value;
    const resDiv = document.getElementById("resBusca");

    try {
        const res = await fetch(`${API_BASE}/clientes/${doc}`);
        const data = await res.json();
        resDiv.style.display = "block";
        resDiv.innerText = res.ok ? JSON.stringify(data, null, 2) : "Cliente não encontrado.";
    } catch (err) {
        alert("Erro de conexão ao buscar documento.");
    }
};

// --- ATUALIZAR SALDO ---
document.getElementById("formSaldo").onsubmit = async (e) => {
    e.preventDefault();
    const conta = document.getElementById("s_conta").value;
    const valor = document.getElementById("s_valor").value;

    try {
        const res = await fetch(`${API_BASE}/contas/atualizar-saldo/${conta}?novo_saldo=${valor}`, { 
            method: 'PATCH' 
        });
        if (res.ok) {
            alert("Saldo atualizado com sucesso.");
            fecharModal("modalSaldo");
        } else {
            const d = await res.json();
            alert("Erro: " + d.detail);
        }
    } catch (err) {
        alert("Erro de conexão ao atualizar saldo.");
    }
};

// --- CONSULTAR NÚMERO DA CONTA ---
document.getElementById("formConta").onsubmit = async (e) => {
    e.preventDefault();
    const doc = document.getElementById("c_doc").value;
    const resDiv = document.getElementById("resConta");

    try {
        const res = await fetch(`${API_BASE}/contas/numero/${doc}`);
        const data = await res.json();
        resDiv.style.display = "block";
        resDiv.innerText = data['Conta: '] ? `Conta localizada: ${data['Conta: ']}` : "Conta não encontrada para este documento.";
    } catch (err) {
        alert("Erro de conexão ao localizar conta.");
    }
};