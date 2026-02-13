from sys import exception
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from contextlib import asynccontextmanager

from pydantic import BaseModel
from app import URL_CORE_BANCO, busca_investidor
from services.cliente_investidor_service import validar_cliente_conta, validar_investidor
from models.schemas import RENTABILIDADE_PERFIL, InvestidorIn, PerfilEnum, TipoEnum
import requests
from services.database import busca_investidor_db, cadastrar_investidor_db, atualiza_investidor_db, create_tables
from services.investimento_service import validacao_investimento
from fastapi.middleware.cors import CORSMiddleware
from services.market_service import validar_ticker


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(title= 'PyInvest', lifespan= lifespan)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

def login_investimentos(documento: str):
    url = f'{URL_CORE_BANCO}/clientes/investidor/{documento}'
    resposta = requests.get(url)

    if resposta.status_code != 200:
        raise HTTPException(status_code = 403, detail = 'Investidor não encontrado')
    return documento


#mecanismo de busca dos tickers
@app.get('/investimento/busca/{ticker}')
def consulta_ticker(ticker: str):
    try:
        dados_ativo = validar_ticker(ticker)

        if not dados_ativo:
            raise HTTPException(status_code = 404, detail = 'Ativo não localizado em Yahoo Finance.')
        return dados_ativo
    except Exception as e:
        raise HTTPException(status_code = 400, detail = f'Erro inesperado: {e}')
    

#rota usada pelo front para validar o login
@app.get('/investimentos/acesso/{documento}')
def acesso_investidor(documento: str):
    url = f'{URL_CORE_BANCO}/clientes/investidor/{documento}'
    resposta = requests.get(url)

    if resposta.status_code == 200:
        return {"documento" : documento}
    
    raise HTTPException(status_code = 403, detail = f'Erro no core: {resposta.status_code}')


#cadastrar investimento
@app.post('/investimento/novo')
def criar_investimento(documento: str, tipo: str, valor_investido: float, ativo: bool, ticker: Optional[str] = None):
    try:
        ticker_valido = ticker.strip() if ticker else None
        # print(f"DEBUG: Tipo={tipo}, Ticker={ticker}")
        dados_validados = validacao_investimento(documento, tipo, valor_investido, ativo, ticker)
        if not dados_validados:
            raise ValueError('Dados de investimento inválidos')
        resposta = requests.post(f'{URL_CORE_BANCO}/investimento/novo', params = dados_validados)

        if resposta.status_code != 200:
            raise Exception(resposta.json().get('detail'))
        
        return resposta.json()
    except Exception as e:
        raise HTTPException(status_code = 400, detail = str(e))
    
        
    
#buscar investimento pelo id do cliente
@app.get('/investimento/{documento}')
def busca_investimento_pelo_doc(documento: str, id_investidor = Depends(login_investimentos)):
    resposta = requests.get(f'{URL_CORE_BANCO}/investimento/{documento}')
    if resposta.status_code != 200:
        raise HTTPException(status_code = 404, detail = 'Investimento não encontrado.')
    
    return resposta.json()

#rota para buscar um investidor
@app.get('/investimentos/buscar-perfil/{documento}')
def buscar_investidor_api(documento: str):
    try:
        url = f'{URL_CORE_BANCO}/clientes/investidor/{documento}'
        resposta = requests.get(url)

        if resposta.status_code == 200:
            dados_investidor = resposta.json()
            return{
                "documento" : dados_investidor.get('documento'),
                "nome" : dados_investidor.get('nome')
            }
        raise HTTPException(status_code = 404, detail = 'Investidor não cadastrado.')
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code = 503, detail = f'Erro de conexão: {e}')
    

@app.delete('/investimento/excluir/{id_investimento}')
def deletar_investimento(id_investimento: str, valor_investido: float, id_investidor = Depends(login_investimentos)):
    resposta = requests.delete(f'{URL_CORE_BANCO}/investimento/excluir/id_investimento')
    if resposta.status_code in (200, 204):
        return 'Investimento excluído com sucesso.'
    try:
        detail = resposta.json().get('detail', 'Erro ao excluir investimento.')
    except Exception as e:
        raise HTTPException(f'Erro inesperado: {e}')