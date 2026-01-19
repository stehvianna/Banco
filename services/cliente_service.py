from services.database import busca_cliente, inserir_cliente

def validar_cliente(nome: str, telefone: str, documento: str, correntista: bool) -> bool:
    if not nome or len(nome) < 3:
        raise ValueError('Insira um nome válido.')
    if not telefone or len(telefone) != 11:
        raise ValueError('Insira um telefone válido.')
    if not documento or len(documento) != 11:
        raise ValueError('Insira um CPF válido. Insira somente números.')
    
    return True

def validacao_cadastro(nome: str, telefone: str, documento: str, correntista: bool):
    if validar_cliente(nome, telefone, documento, correntista):
        inserir_cliente(nome, telefone, documento, correntista)
    else:
        raise ValueError('Dados do cliente inválidos.')