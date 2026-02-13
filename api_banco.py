from contextlib import asynccontextmanager
from multiprocessing import Value
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
    atualiza_investidor_db, 
    busca_investidor_db,
    novo_investimento_db
)
from services.cliente_service import validar_cliente
from services.conta_service import verificacao_conta
from services.cliente_investidor_service import validar_cliente_conta, validar_investidor
from models.schemas import RENTABILIDADE_PERFIL, ClienteIn, PerfilEnum, InvestidorIn, TipoEnum
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
def excluir_cliente_api(documento: str):
    try:
        deletar_cliente(documento)
        return 'Cadastro excluído com sucesso.'
    except ValueError as e:
        raise HTTPException(status_code = 400, detail = str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail= f'Erro ao excluir cadastro: {e}')

    
#criar contas
@app.post('/contas')
def criar_conta(documento: str, saldo_cc: float = 0.0):
    try:
        return verificacao_conta(documento, saldo_cc)
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
@app.patch('/contas/{documento}/atualizar_saldo')
def atualizar_saldo(documento: str, novo_saldo: float):
    try:
        conta = busca_conta(documento)
        if not conta:
            raise ValueError(f'Nenhuma conta vinculada ao CPF {documento}')
        elif conta:
            numero_conta = conta.get('numero_conta')
            atualizar_saldo_db(numero_conta, novo_saldo)
        return(f'Saldo atualizado: R${novo_saldo}')
    except Exception as e:
        raise e

    

#criar investidor
@app.post('/investidor')
def cadastro_investidor(documento: str, nome: str, telefone: str, email: str, patrimonio: float, perfil: PerfilEnum):
    try:
        investidor = cadastrar_investidor_db(documento, nome, telefone, email, patrimonio, perfil.value)
        return investidor
    except ValueError as e:
        raise HTTPException(status_code = 500, detail = f'Erro ao cadastrar investidor: {e}')
    
#atualizar dados do investidor
@app.patch('/investidor/{documento}')
def atualizar_investidor_banco(documento: str, nome: str, telefone: str, email: str, patrimonio: float, perfil: PerfilEnum):
    try:
        investidor = atualiza_investidor_db(documento, nome, telefone, email, patrimonio, perfil.value)
        if not investidor:
            raise HTTPException(status_code = 404, detail = 'Cadastro não encontrado.')
    except ValueError as e:
        raise HTTPException(status_code = 500, detail = 'Cadastro não encontrado')
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f'Erro ao atualizar cliente: {e}')
    
#buscar investidor
@app.get('/clientes/investidor/{documento}')
def procurar_investidor(documento: str):
    investidor = busca_investidor_db(documento)
    if not investidor:
        raise HTTPException(status_code = 404, detail = 'Investidor não encontrado.')
    return investidor

#novo investimento
@app.post('/investimento/novo')
def novo_investimento(documento: str, tipo: str, valor_investido: float, ativo: bool, ticker: str = None):
    if tipo == 'RENDA FIXA':
        rentabilidade = RENTABILIDADE_PERFIL.get(busca_investidor_db(documento).get('perfil'))
    else:
        rentabilidade = 0.0
    try:
        resultado = novo_investimento_db(documento, tipo, valor_investido, rentabilidade, ativo, ticker)
        return resultado
    except Exception as e:
        raise HTTPException(status_code = 400, detail = f'Erro ao salvar investimento: {e}')
    #     investidor = busca_investidor_db(documento)
    #     if not investidor:
    #         raise Exception("Investidor não encontrado")

    #     valor_perfil = investidor.get('perfil')
    #     perfil = str(valor_perfil).strip().upper()


    #     if validacao_investimento(documento, tipo, valor_investido, ativo, ticker):
    #         resultado = novo_investimento_db(documento, tipo, valor_investido, rentabilidade, ativo)
    #         return resultado
            
    # except Exception as e:
    #     raise HTTPException(status_code=400, detail=f'Erro ao criar investimento: {e}')

#atualizar investimento
@app.patch('investimento/atualizar/{id_investimento}')
def atualizar_investimento(id_investimento: str, tipo: str, valor_investido: float, ativo: bool):
    tipo_investimento = busca_investimento_db(id_investimento).get('tipo')
    if tipo_investimento != 'RENDA_FIXA':
        raise ValueError('Impossível alterar investimentos em renda variável. Tente vender os ativos.')
    else: 
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
def deletar_investimento(id_investimento: str, documento: str, valor_investido: float):
    try:
        investimento = busca_investimento_db(id_investimento)
        if not investimento:
            raise HTTPException(status_code = 404, detail = 'Investimento não encontrado.')
        retirada_investimento_db(id_investimento, valor_investido, documento)
        return ('Investimento excluído com sucesso.')
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f'Erro ao excluir investimento: {e}')
    
#listar investimentos do cliente
@app.get('/investimento/{documento}')
def investimentos_por_cliente(documento: str):
    try:
        lista_inv = busca_investimento_doc(documento)
    except Exception as e:
        raise HTTPException(status_code = 404, detail = f'Nenhum investimento encontrado para o CPF {documento}')
    return lista_inv





    
    
if __name__ == "__main__":
    uvicorn.run("api_banco:app", host="127.0.0.1", port=8001, reload=True)