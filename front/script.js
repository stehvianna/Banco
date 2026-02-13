const API_CORE = "http://localhost:8000";
const API_INVEST = "http://localhost:8002";

// --- CONTROLE DE INTERFACE ---
function abrirModal(id) {
    const m = document.getElementById(id);
    if(m) m.style.display = "block";
}

function fecharModal(id) {
    const m = document.getElementById(id);
    if(m) {
        m.style.display = "none";
        const results = m.querySelectorAll('.result-area');
        results.forEach(res => {
            res.style.display = 'none';
            res.innerText = '';
        });
    }
}

function gerenciarCampoTicker() {
    const tipo = document.getElementById("inv_tipo").value;
    const container = document.getElementById("container_ticker");
    const inputTicker = document.getElementById("inv_ticker");

    if (tipo !== "RENDA FIXA" && tipo !== "") {
        container.style.display = "block";
        inputTicker.required = true;
    } else {
        container.style.display = "none";
        inputTicker.required = false;
        inputTicker.value = "";
    }
}

window.onclick = (e) => {
    if (e.target.className === "modal") fecharModal(e.target.id);
};

// --- CONFIGURAÇÃO DE EVENTOS ---
const checkCorr = document.getElementById("is_correntista");
if(checkCorr) {
    checkCorr.onchange = function() {
        document.getElementById("extra_banco").style.display = this.checked ? "block" : "none";
    };
}

const checkInv = document.getElementById("is_investidor");
if(checkInv) {
    checkInv.onchange = function() {
        document.getElementById("extra_investimento").style.display = this.checked ? "block" : "none";
    };
}

// --- ACESSO AO PORTAL ---
async function validarAcessoInvestidor() {
    const docInput = document.getElementById("login_doc_invest").value.trim().replace(/\D/g, "");
    const resDiv = document.getElementById("resLoginInvest");
    
    if(!docInput) return alert("Digite o CPF");

    try {
        const res = await fetch(`${API_INVEST}/investimentos/acesso/${docInput}`);
        const data = await res.json();

        if (res.ok) {
            sessionStorage.setItem("doc_investidor", docInput);
            window.location.href = 'investimentos.html';
        } else {
            resDiv.style.display = "block";
            resDiv.style.color = "#e74c3c";
            resDiv.innerText = data.detail || "Investidor não encontrado.";
        }
    } catch (err) {
        alert("Erro ao conectar com a API de Investimentos (Porta 8002).");
    }
}
// --- NOVO INVESTIMENTO ---
const formInvest = document.getElementById("formNovoInvest");
if (formInvest) {
    formInvest.addEventListener('submit', async function(e) {
        e.preventDefault(); 
        
        const resDiv = document.getElementById("resNovoInvest");
        const docAtivo = sessionStorage.getItem("doc_investidor");
        
        const tipoSelecionado = document.getElementById("inv_tipo").value;
        const valorInserido = document.getElementById("inv_valor").value;

        const inputTicker = document.getElementById("inv_ticker");
        const tickerInserido = inputTicker ? inputTicker.value.trim().toUpperCase() : "";

        const params = {
            documento: docAtivo,
            tipo: tipoSelecionado,
            valor_investido: valorInserido,
            ativo: "true" 
        };

        if (tipoSelecionado !== "RENDA FIXA" && tickerInserido) {
            params.ticker = tickerInserido;
        }
        else{
            resDiv.style.display = "block";
            resDiv.style.color = "#e74c3c";
            resDiv.innerText = "❌ Erro: Ticker é obrigatório para este tipo de ativo.";
            return
        }

        const queryParams = new URLSearchParams(params);

        resDiv.style.display = "block";
        resDiv.style.color = "blue";
        resDiv.innerText = "Processando aplicação...";

        try {
            
            const response = await fetch(`${API_INVEST}/investimento/novo?${queryParams.toString()}`, {
                method: 'POST',
                headers: { 'Accept': 'application/json' }
            });

            const data = await response.json();

            if (response.ok) {
                resDiv.style.color = "#2ecc71";
                resDiv.innerText = "✅ Investimento realizado com sucesso!";
                formInvest.reset();
                gerenciarCampoTicker(); 
            } else {
                resDiv.style.color = "#e74c3c";
                resDiv.innerText = "❌ Erro: " + (data.detail || "Falha na operação.");
            }
        } catch (err) {
            resDiv.style.color = "#e74c3c";
            resDiv.innerText = "🚨 Erro: O servidor não respondeu.";
        }
    });
}
// --- CADASTRO DE CLIENTE ---
const formCad = document.getElementById("formCadastro");
if(formCad) {
    formCad.onsubmit = async (e) => {
        e.preventDefault();
        const resDiv = document.getElementById("resCadastro");
        const isInvestidor = document.getElementById("is_investidor").checked;
        
        const params = new URLSearchParams({
            nome: document.getElementById("reg_nome").value,
            documento: document.getElementById("reg_doc").value.replace(/\D/g, ""),
            telefone: document.getElementById("reg_tel").value,
            correntista: document.getElementById("is_correntista").checked,
            investidor: isInvestidor
        });

        if (isInvestidor) {
            const perfilRaw = document.getElementById("reg_perfil").value;
            params.append("perfil", perfilRaw.toUpperCase()); 
            params.append("patrimonio", document.getElementById("reg_patrimonio").value || 0);
        }

        try {
            const res = await fetch(`${API_CORE}/clientes?${params.toString()}`, { method: 'POST' });
            if (res.ok) {
                resDiv.style.display = "block";
                resDiv.style.color = "#2ecc71";
                resDiv.innerText = "Cliente cadastrado com sucesso!";
                setTimeout(() => fecharModal("modalCadastro"), 2000);
            } else {
                const errorData = await res.json();
                alert("Erro no cadastro: " + (errorData.detail || "Verifique os dados."));
            }
        } catch (err) { 
            alert("Erro ao conectar com o servidor Core."); 
        }
    };
}