
from .cliente_service import validar_cliente, busca_cliente
from .conta_service import verificacao_conta, busca_conta
from email_validator import validate_email, EmailNotValidError

perfis = ['CONSERVADOR', 'MODERADO', 'ARROJADO']

def validar_cliente_conta(id_cliente: str,):    
    if id_cliente and len(id_cliente) == 11:
        if not busca_cliente(id_cliente):
            raise ValueError('Nenhum cliente encontrado com o CPF informado.')
        if not busca_conta(id_cliente):
            raise ValueError('Nenhuma conta informada para o cliente cadastrado.')
    else:
        raise ValueError('Dados do cliente inválidos.')
    return True
    
def validar_investidor(id_cliente: str, email: str, perfil: str):
    if validar_cliente_conta(id_cliente):
        if not validate_email(email):
            raise ValueError('Insira um endereço de email válido.')
        if not perfil or perfil not in perfis:
            raise ValueError('Informe um perfil de investidor válido.')


    
    


    
            
