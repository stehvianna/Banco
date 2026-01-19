from fastapi import FastAPI, HTTPException, params
import requests
from services.cliente_service import validar_cliente
from services.conta_service import verificacao_conta
from services.score_credito import calcular_score

app = FastAPI(title='Banco Javer')

URL_CORE_BANCO = "http://localhost:8001"


#cadastrar cliente
@app.post('/clientes')
def cadastrar_cliente(nome: str, telefone: str, documento: str, correntista: bool):
    try:
        validar_cliente(nome, telefone, documento, correntista)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Erro ao cadastrar cliente: {e}')
    
    checagem = requests.get(f'{URL_CORE_BANCO}/clientes/{documento}')

    if checagem.status_code == 200:
        raise HTTPException(status_code=409, detail='Cliente já cadastrado.')
    
    params_cliente = {
        "nome": nome,
        "telefone": telefone,
        "documento": documento,
        "correntista": correntista,
    }

    resposta = requests.post(f'{URL_CORE_BANCO}/clientes', params = params_cliente)

    if resposta.status_code != 200 and resposta.status_code != 201:
        raise HTTPException(status_code=500, detail='Erro ao salvar os dados do cliente.')
    
    cliente_salvo = resposta.json()

    if correntista:
        params_conta = {
            "id_cliente": cliente_salvo['documento'],
            "saldo_cc": 0.0
        }
        try:
            resposta_conta = requests.post(f'{URL_CORE_BANCO}/contas', params = params_conta)
            if resposta_conta.status_code != 200 and resposta_conta.status_code != 201:
                raise HTTPException(status_code = 500, detail = 'Erro ao criar conta.')
        except Exception as e:
            raise HTTPException(status_code = 500, detail = f'Erro ao criar conta: {e}')

    return cliente_salvo


#criar contas
@app.post('/contas/criar_conta')
def criar_nova_conta(id_cliente: str, saldo_cc: float = 0.0):
    params_conta = {
        "id_cliente": id_cliente,
        "saldo_cc": saldo_cc
    }
    resposta = requests.post(f'{URL_CORE_BANCO}/contas', params = params_conta)

    if resposta.status_code != 200 and resposta.status_code != 201:
        raise HTTPException(status_code=500, detail='Erro ao criar conta.')
    
    return resposta.json()
    

#busca cliente por documento
@app.get('/clientes/{documento}')
def buscar_cliente_app(documento: str):
        resposta = requests.get(f'{URL_CORE_BANCO}/clientes/{documento}')
        if resposta.status_code != 200:
            raise HTTPException(status_code=404, detail='Cliente não encontrado.')
        return resposta.json()

#busca cliente por nome
@app.get('/clientes/busca/nome')
def buscar_cliente_nome(nome: str):
    resposta = requests.get(f'{URL_CORE_BANCO}/clientes/busca/nome', params={"nome": nome})
    
    if resposta.status_code != 200:
        raise HTTPException(status_code=404, detail='Cliente não encontrado.')
    
    return resposta.json()


#atualiza dados do cliente
@app.put('/clientes/{documento}')
def atualizar_cliente_app(documento: str, nome: str, telefone: str):
    params_update_cliente = {
        "nome": nome,
        "telefone": telefone
    }
    resposta = requests.put(f'{URL_CORE_BANCO}/clientes/{documento}', params = params_update_cliente)
    if resposta.status_code != 200:
        raise HTTPException(status_code=resposta.status_code, detail='Erro ao atualizar dados.')
    return resposta.json()

#atualiza saldo da conta
@app.patch('/contas/atualizar-saldo/{numero_conta}')
def atualizar_saldo_app(numero_conta: str, novo_saldo: float):
    params_saldo = {
        "novo_saldo": novo_saldo
    }
    try:
        resposta = requests.patch(f'{URL_CORE_BANCO}/contas/{numero_conta}/saldo', params = params_saldo)
        if resposta.status_code != 200:
            raise HTTPException(status_code = resposta.status_code, detail = 'Erro ao atualizar saldo.')
        return resposta.json()
    except requests.exceptios.ConnectionError:
        raise HTTPException(status_code = 503, detail = 'Erro ao atualizar seu saldo.')


#cálculo do score
@app.get('/score/{documento}')
def calcular_score_app(documento: str):
    resposta = requests.get(f'{URL_CORE_BANCO}/contas/{documento}')
    if resposta.status_code != 200:
        raise HTTPException(status_code=404, detail='Nenhuma conta vinculada ao cliente informado.')

    dados_conta = resposta.json()
    score = calcular_score(dados_conta['saldo_cc'])
    return {'CPF: ': documento, " Score de crédito: ": score}


#excluir cadastro
@app.delete('/clientes/excluir/{documento}')
def delete_cliente(documento: str):
    resposta = requests.delete(f'{URL_CORE_BANCO}/clientes/{documento}')
    if resposta.status_code == 200 or resposta.status_code == 204:
        return 'Cadastro excluído com sucesso.'
    try:
        detail = resposta.json().get('detail', 'Erro ao excluir cadastro.')
    except Exception as e:
        raise Exception(f'Erro inesperado: {e}')
    
#buscar número da conta pelo doc do cliente
@app.get('/contas/numero/{documento}')
def buscar_numero_conta(documento: str):    
    resposta = requests.get(f'{URL_CORE_BANCO}/contas/{documento}')
    if resposta.status_code != 200:
        raise HTTPException(status_code = 404, detail = 'Nenhuma conta vinculada ao cliente informado.')
    dados_conta = resposta.json()
    return {'Conta: ': dados_conta['numero_conta']}