from tkinter import EW
from fastapi import FastAPI, HTTPException, params
import requests
from services.cliente_service import validar_cliente
from services.conta_service import verificacao_conta
from services.database import create_tables
from services.score_credito import calcular_score
from models.schemas import ClienteIn, InvestidorIn
from services.cliente_investidor_service import validar_investidor, validar_cliente_conta
from models.schemas import PerfilEnum
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title = 'PyInvest')

URL_CORE_BANCO = "http://localhost:8001"


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, coloque o endereço do seu front
    allow_methods=["*"],
    allow_headers=["*"],
)


#cadastrar cliente
@app.post('/clientes')
def cadastrar_cliente(nome: str, telefone: str, documento: str, correntista: bool, investidor: bool, email: Optional[str] = None, patrimonio: Optional[float] = None, perfil: Optional[PerfilEnum] = None):
    cliente_salvo = None
    investidor_salvo = None

    try:
        validar_cliente(nome, telefone, documento, correntista, investidor)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Erro ao cadastrar cliente: {e}')
    
    try:
        checagem = requests.get(f'{URL_CORE_BANCO}/clientes/{documento}')
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code = 503, detail = f'Erro desconhecido: {e}')

    if checagem.status_code == 200:
        raise HTTPException(status_code = 409, detail = 'Cliente já cadastrado.')
    
    params_cliente = {
        "nome": nome,
        "telefone": telefone,
        "documento": documento,
        "correntista": correntista,
        "investidor": investidor
    }

    try:    
        resposta = requests.post(f'{URL_CORE_BANCO}/clientes', params=params_cliente, timeout=8)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f'Erro ao cadastrar cliente: {e}')

    if resposta.status_code not in (200, 201):
        try:
            detalhe = resposta.json()
        except Exception:
            detalhe = resposta.text
        raise HTTPException(status_code=resposta.status_code, detail=f'Erro ao cadastrar cliente: {detalhe}')

    cliente_salvo = resposta.json()

    if correntista:
        params_conta = {
            "id_cliente": cliente_salvo['documento'],
            "saldo_cc": 0.0
        }
        try:
            resposta_conta = requests.post(f'{URL_CORE_BANCO}/contas', params=params_conta, timeout=5)
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f'Erro ao criar conta: {e}')

        if resposta_conta.status_code not in (200, 201):
            try:
                detalhe = resposta_conta.json()
            except Exception:
                detalhe = resposta_conta.text
            raise HTTPException(status_code=500, detail=f'Erro ao criar cona: {detalhe}')
        
    if investidor:
        try:
            checagem_investidor = requests.get(f'{URL_CORE_BANCO}/clientes/investidor/{documento}')
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f'Erro ao buscar investidor: {e}')

        if checagem_investidor.status_code == 200:
            investidor_salvo = checagem_investidor.json()
        else:
            params_investidor = {
                "id_cliente": documento,
                "nome": nome,
                "telefone": telefone,
                "email": email,
                "patrimonio": patrimonio,
                "perfil": (perfil.value if hasattr(perfil, "value") else str(perfil).upper()) if perfil is not None else None
            }
            resposta_investidor = requests.post(f'{URL_CORE_BANCO}/investidor', params=params_investidor, timeout=8)

            if resposta_investidor.status_code in (200, 201):
                investidor_salvo = resposta_investidor.json()
            else:
                try:
                    detalhe = resposta_investidor.json().get('detail', 'Erro desconhecido')
                except:
                    detalhe = f'Erro desconhecido: {resposta_investidor.status_code}'
                raise HTTPException(status_code = 500, detail = f'Erro ao salvar investidor: {detalhe}')
    return{"Investidor" : investidor_salvo, "Cliente" : cliente_salvo}



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
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code = 503, detail = 'Erro ao atualizar seu saldo.')
    
#atualizar dados do cliente
@app.patch('/clientes/atualizar/{documento}')
def atualizar_cliente_app(documento: str, nome: str, telefone: str):
    params_update_cliente = {
        "nome": nome,
        "telefone": telefone
    }
    try:
        resposta = requests.patch(f'{URL_CORE_BANCO}/clientes/{documento}', params = params_update_cliente)
        if resposta.status_code != 200:
            raise HTTPException(status_code = resposta.status_code, detail = 'Erro ao atualizar cliente.')
        return resposta.json()
    except requests.exceptions.ConnectionError: 
        raise HTTPException(status_code=503, detail='Erro de conexão.')
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f'Erro: {e}')

#busca cliente pelo doc
@app.get('/score/{documento}')
def calcular_score_app(documento: str):
    try:
        resposta = requests.get(f'{URL_CORE_BANCO}/contas/{documento}', timeout=5)
        
        if resposta.status_code == 404:
            raise HTTPException(status_code=404, detail='Nenhuma conta vinculada ao cliente informado.')
        
        resposta.raise_for_status()
        dados_conta = resposta.json()
        
        saldo = dados_conta.get('saldo_cc', 0)
        score = calcular_score(saldo)
        
        return {
            "documento": documento, 
            "score_credito": score
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Erro de conexão com o banco: {e}")


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

#buscar inestidor
@app.get('/investidor/{id_cliente}')
def busca_investidor(id_cliente: str):
    try:
        resposta = requests.get(f'{URL_CORE_BANCO}/clientes/investidor/{id_cliente}')
        if resposta.status_code == 404:
            raise HTTPException(status_code = 404, detail = 'Nenhum investidor encontrado.')
        return resposta.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code = 503, detail = f'Erro ao buscar investidor: {e}')
    




if __name__ == '__main__':
    create_tables()


