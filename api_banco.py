from fastapi import FastAPI, HTTPException, Response
from services.database import (atualiza_cliente_db, atualizar_saldo_db, deletar_cliente, busca_conta, create_tables, busca_cliente, busca_cliente_por_nome, inserir_cliente as inserir_cliente_db, nova_conta)
from contextlib import asynccontextmanager
from services.cliente_service import validar_cliente
from services.conta_service import verificacao_conta
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(title= 'Banco Javer', lifespan= lifespan)

#buscar cliente pelo nome
@app.get('/clientes/busca/nome')
def busca_cliente_nome(nome:str):
    cliente = busca_cliente_por_nome(nome)
    if not cliente:
        raise HTTPException(status_code= 404, detail= 'Cliente não encontrado.')
    return cliente

#buscar cliente pelo documento
@app.get('/clientes/{documento}')
def busca_cliente_documento(documento: str):
    cliente = busca_cliente(documento)
    if not cliente:
        raise HTTPException(status_code= 404, detail = 'Cliente não encontrado.')
    return cliente

#cadastrar cliente
@app.post('/clientes')
def cadastro_cliente(nome: str, telefone: str, documento: str, correntista: bool):
    try:
        #usar a funçao da regra de negócio
        cliente = validar_cliente(nome, telefone, documento, correntista)
        if cliente:
            cliente = inserir_cliente_db(nome, telefone, documento, correntista)
        return cliente
    except Exception as e:
        raise HTTPException(status_code= 400, detail= 'Impossível cadastrar cliente. Dados inválidos.')

#excluir cliente
@app.delete('/clientes/{documento}')
def excluir_cliente(documento: str):
    try:
        resultado = deletar_cliente(documento)
        return 'Cadastro excluído com sucesso.'
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail='Não foi possível deletar o cadastro.')

    
#criar contas
@app.post('/contas')
def criar_conta(id_cliente: str, saldo_cc: float = 0.0):
    try:
        return verificacao_conta(id_cliente, saldo_cc)
    except Exception as e:
        raise HTTPException(status_code= 404, detail= f'Impossível criar conta. Erro: {e}')

#buscar contas
@app.get('/contas/{documento}')
def buscar_contas(documento: str):
    try: 
        conta = busca_conta(documento)
    except Exception as e:
        raise HTTPException(status_code= 404, detail= 'Nenhuma conta encontrada.')
    return conta

#atualizar cadastro
@app.patch('/clientes/{documento}')
def atualizar_cliente(documento: str, nome: str, telefone: str):
    try:
        cliente_atualizado = atualiza_cliente_db(documento, nome, telefone)

        if cliente_atualizado:
            return {
                "documento": documento,
                "nome": nome,
                "telefone": telefone,
            }
        else:
            # Caso o documento não exista no banco
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")
            
    except Exception as e:
        # Erros de conexão ou SQL
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {str(e)}")

    
#atualizar saldo da conta
@app.patch('/contas/{numero_conta}/saldo')
def atualizar_saldo(numero_conta: str, novo_saldo: float):
    try:
        return atualizar_saldo_db(numero_conta, novo_saldo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar saldo: {e}")

if __name__ == "__main__":
    uvicorn.run("api_banco:app", host="127.0.0.1", port=8001, reload=True)