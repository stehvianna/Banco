
from models.schemas import TipoEnum, RENTABILIDADE_PERFIL
from .cliente_investidor_service import validar_investidor
from .market_service import validar_ticker
from.database import busca_investidor_db, busca_conta, novo_investimento_db, busca_investimento_db, atualiza_investidor_db

def validar_investimento(documento: str, tipo: TipoEnum, valor_investido: float, ticker: str = None):
    if not documento or len(documento) != 11:
        raise ValueError('Insira um CPF válido.')
    if not tipo or tipo not in TipoEnum:
        raise ValueError('Tipo de investimento inválido.')
    if not valor_investido or valor_investido < 0:
        raise ValueError('Insira um valor válido.')
    #se o investimento NÃO for renda fixa, o ticker é obrigatório
    if tipo != TipoEnum.RENDA_FIXA:
        if not ticker:
            raise ValueError(f'O campo "ticker" é obrigatório para investimentos do tipo {tipo}.')
        if not validar_ticker(ticker):
            raise ValueError('Erro ao validar ticker. Verifique os dados informados.')
    #validar se o cliente tem saldo para investir o valor
    if busca_conta(documento).get('saldo_cc') < valor_investido:
        raise ValueError('Saldo insuficiente para realizar o investimento.')
    

    return True
    
def validacao_investimento(documento: str, tipo: TipoEnum, valor_investido: float, ativo: bool, ticker: str = None):

    if validar_investimento(documento, tipo, valor_investido, ticker):
        investidor = busca_investidor_db(documento)
        if not investidor:
            raise ValueError('Investidor não encontrado.')
        
        if tipo == TipoEnum.RENDA_FIXA:
            rentabilidade = RENTABILIDADE_PERFIL.get(investidor.get('perfil'))
            if rentabilidade is None: 
                raise ValueError('Rentabilidade não configurada para este perfil de Renda Fixa.')
        else:
            rentabilidade = None
        

        
        return {
            "documento" : documento,
            "tipo" : tipo,
            "valor_investido" : valor_investido,
            "rentabilidade" : rentabilidade,
            "ativo" : ativo,
            "ticker" : ticker
        }
