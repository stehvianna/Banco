from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from app import URL_CORE_BANCO, busca_investidor
from services.cliente_investidor_service import validar_cliente_conta, validar_investidor
from models.schemas import RENTABILIDADE_PERFIL, InvestidorIn, PerfilEnum, TipoEnum
import requests
from services.database import busca_investidor_db, cadastrar_investidor_db, atualiza_investidor_db, excluir_investidor_db, create_tables
from services.investimento_service import validacao_investimento

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(title= 'PyInvest', lifespan= lifespan)

def login_investimentos(id_cliente: str):
    try: 
        autorizado = busca_investidor_db(id_cliente)
        if not autorizado:
            raise HTTPException(status_code = 404, detail = 'Acesso não autorizado.')
    except Exception as e: 
        raise Exception(f'Erro ao autenticar: {e}')
    return id_cliente

#cadastrar investimento
@app.post('/investimento/novo')
def criar_investimento(id_cliente: str, tipo: TipoEnum, valor_investido: float, ativo: bool, id_investidor = Depends(login_investimentos)):
    rentabilidade = RENTABILIDADE_PERFIL.get(busca_investidor(id_cliente).get('perfil'))
    try: 
        validacao_investimento(id_cliente, tipo, valor_investido, ativo)
    except Exception as e:
        raise HTTPException(status_code = 400, detail = f'Erro ao criar investimento: {e}')
    
    try:
        checagem = requests.post(f'{URL_CORE_BANCO}/investimento/novo')
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code = 503, detail = f'Erro ao salvar investimento: {e}')
    
    if checagem.status_code == 200:
        raise HTTPException(status_code = 409, detali = 'Investimento já cadastrado.')
    
    params_investimento = {
        "id_cliente" : id_cliente,
        "tipo" : tipo,
        "valor_investido" : valor_investido,
        "rentabilidade" : rentabilidade,
        "ativo" : ativo
    }

    try: 
        resposta = requests.post(f'{URL_CORE_BANCO}/investimento/novo', params = params_investimento)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code = resposta.status_code, detail = f'Erro ao criar investimento: {e}')
    
    if resposta.status_code not in (200, 201):
        try:
            detalhe = resposta.json()
        except Exception as e:
            raise HTTPException(status_code = resposta.status_code, detail = f'Erro ao criar investimento {resposta.text}')
        
    investimento_salvo = resposta.json()
    return investimento_salvo

#buscar investimento pelo id do cliente
@app.get('/investimento/{id_cliente}')
def busca_investimento_pelo_doc(id_cliente: str, id_investidor = Depends(login_investimentos)):
    resposta = requests.get(f'{URL_CORE_BANCO}/investimento/{id_cliente}')
    if resposta.status_code != 200:
        raise HTTPException(status_code = 404, detail = 'Inestimento não encontrado.')
    
    return resposta.json()

@app.patch('{URL_CORE_BANCO}/investimento/atualizar/{id_investimento}')
def atualizar_inv(id_investimento: str, valor_investido: str, ativo: bool, tipo: TipoEnum, id_investidor = Depends(login_investimentos)):
    params_update_investimento = {
        "id_investimento" : id_investimento,
        "valor_investido" : valor_investido,
        "ativo" : ativo,
        "tipo" : tipo
    }
    try:
        resposta = requests.patch(f'{URL_CORE_BANCO}/investimento/atualizar/{id_investimento}', params = params_update_investimento)
        if resposta.status_code != 200:
            raise HTTPException(status_code = resposta.status_code, detail = 'Erro ao atualizar dados do investidor. Tente novamente.')
        return resposta.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code = 503, detail = 'Erro ao salvar novos dados.')
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f'Erro desconhecido: {e}')
    

@app.delete('/investimento/excluir/{id_investimento}')
def deletar_investimento(id_investimento: str, valor_investido: float, id_investidor = Depends(login_investimentos)):
    resposta = requests.delete(f'{URL_CORE_BANCO}/investimento/excluir/id_investimento')
    if resposta.status_code in (200, 204):
        return 'Investimento excluído com sucesso.'
    try:
        detail = resposta.json().get('detail', 'Erro ao excluir investimento.')
    except Exception as e:
        raise HTTPException(f'Erro inesperado: {e}')