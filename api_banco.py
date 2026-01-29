from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from services.database import (
    atualiza_cliente_db,
    atualiza_investimento_db, 
    atualizar_saldo_db,
    busca_investimento_db,
    busca_investimento_doc, 
    deletar_cliente, 
    busca_conta, 
    create_tables, 
    busca_cliente, 
    busca_cliente_por_nome,
    retirada_investimento_db,
    inserir_cliente as inserir_cliente_db, 
    nova_conta, 
    cadastrar_investidor_db, 
    excluir_investidor_db, 
    atualiza_investidor_db, 
    busca_investidor_db,
    novo_investimento_db
)
from services.cliente_service import validar_cliente
from services.conta_service import verificacao_conta
from services.cliente_investidor_service import validar_cliente_conta, validar_investidor
from models.schemas import ClienteIn, PerfilEnum, InvestidorIn, TipoEnum
from services.investimento_service import validacao_investimento


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(title = 'Banco Javer', lifespan = lifespan) # ADICIONE O LIFESPAN AQUI


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
def cadastro_cliente(nome: str, telefone: str, documento: str, correntista: bool, investidor: bool):
    try:
        #usar a funçao da regra de negócio
        cliente = validar_cliente(nome, telefone, documento, correntista, investidor)
        if cliente:
            cliente = inserir_cliente_db(nome, telefone, documento, correntista, investidor)
        return cliente
    except Exception as e:
        raise HTTPException(status_code= 400, detail= f'Impossível cadastrar cliente. Erro: {e}')

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
    

#criar investidor
@app.post('/investidor')
def cadastro_investidor(id_cliente: str, nome: str, telefone: str, email: str, patrimonio: float, perfil: PerfilEnum):
    try:
        investidor = cadastrar_investidor_db(id_cliente, nome, telefone, email, patrimonio, perfil.value)
        return investidor
    except ValueError as e:
        raise HTTPException(status_code = 500, detail = f'Erro ao cadastrar investidor: {e}')
    
#atualizar dados do investidor
@app.patch('/investidor/{id_cliente}')
def atualizar_investidor_banco(id_cliente: str, nome: str, telefone: str, email: str, patrimonio: float, perfil: PerfilEnum):
    try:
        investidor = atualiza_investidor_db(id_cliente, nome, telefone, email, patrimonio, perfil.value)
        if not investidor:
            raise HTTPException(status_code = 404, detail = 'Cadastro não encontrado.')
    except ValueError as e:
        raise HTTPException(status_code = 500, detail = 'Cadastro não encontrado')
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f'Erro ao atualizar cliente: {e}')
    
#buscar investidor
@app.get('/clientes/investidor/{id_cliente}')
def procurar_investidor(id_cliente: str):
    investidor = busca_investidor_db(id_cliente)
    if not investidor:
        raise HTTPException(status_code = 404, detail = 'Investidor não encontrado.')
    return investidor


#excluir cadastro do investidor
@app.delete('/clientes/investidor/{id_cliente}')
def deletar_investidor(id_cliente: str):
    try:
        investidor = busca_investidor_db(id_cliente)
        if not investidor:
            raise HTTPException(status_code = 404, detail = 'Investidor não encontrado.')
        excluir_investidor_db(id_cliente)
        return('Investidor excluído com sucesso.')
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f'Erro ao excluir investidor: {e}')

#novo investimento
@app.post('/investimento/novo')
def novo_investimento(id_cliente: str, tipo: TipoEnum, valor_investido: float, rentabilidade: float, ativo: bool):
    try:
        investimento = validacao_investimento(id_cliente, tipo, valor_investido, ativo)
        if investimento:
            investimento = novo_investimento_db(id_cliente, tipo, valor_investido, rentabilidade, ativo)
        return investimento
    except Exception as e:
        raise HTTPException(status_code = 400, detail = f'Erro ao criar investimento: {e}')

#atualizar investimento
@app.patch('investimento/atualizar/{id_investimento}')
def atualizar_investimento(id_investimento: str, tipo: TipoEnum, valor_investido: float, ativo: bool):
    try:
        investimento_atualizado = atualiza_investimento_db(id_investimento, tipo, valor_investido, ativo)

        if investimento_atualizado:
            return{
                "id_investimento" : id_investimento,
                "tipo" : tipo,
                "valor_investido" : valor_investido,
                "ativo" : ativo
            }

        else:
            raise HTTPException(status_code = 404, detail = 'Investimento não encontrado.')

    except Exception as e:
        raise HTTPException(status_code = 500, detail = f'Erro ao atualizar investimento: {e}')


#deletar investimento
@app.delete('/investimento/excluir/{id_investimento}')
def deletar_investimento(id_investimento: str, id_cliente: str, valor_investido: float):
    try:
        investimento = busca_investimento_db(id_investimento)
        if not investimento:
            raise HTTPException(status_code = 404, detail = 'Investimento não encontrado.')
        retirada_investimento_db(id_investimento, valor_investido, id_cliente)
        return ('Investimento excluído com sucesso.')
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f'Erro ao excluir investimento: {e}')
    
#listar investimentos do cliente
@app.get('/investimento/{id_cliente}')
def investimentos_por_cliente(id_cliente: str):
    try:
        lista_inv = busca_investimento_doc(id_cliente)
    except Exception as e:
        raise HTTPException(status_code = 404, detail = f'Nenhum investimento encontrado para o CPF {id_cliente}')
    return lista_inv





    
    
if __name__ == "__main__":
    uvicorn.run("api_banco:app", host="127.0.0.1", port=8001, reload=True)