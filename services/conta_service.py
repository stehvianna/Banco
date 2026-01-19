from .database import nova_conta, busca_conta
from .score_credito import calcular_score

def verificacao_conta(id_cliente: str, saldo_cc: float = 0.0):
    if saldo_cc <0:
        raise ValueError('Saldo da conta não pode ser negativo.')
    try:
        conta = nova_conta(id_cliente, saldo_cc)
        return conta
    except Exception as e:
        raise Exception(f'Impossível criar conta. Erro: {e}')
    