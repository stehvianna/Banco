from pydantic import BaseModel, Field
from typing import List

#sufixo IN: modelo p/ entrada dos dados
class ClienteIn(BaseModel):
    nome: str = Field(..., min_length= 1)
    telefone: str = Field(..., min_length= 11, max_length= 11)
    documento: str = Field(..., min_length= 11, max_length= 11)
    correntista: bool = Field(False)

#sufixo OUT: como o programa vai liberar os dados

class ClienteOut(BaseModel):
    id: int
    nome: str
    telefone: str
    documento: str
    correntista: bool

class ContaIn(BaseModel):
    #ge: greater than or equal to, garante que o campo não está vazio
    id_cliente: int = Field(..., ge=1)
    saldo: float = Field(0.0, ge = 0.0)

class ContaOut(BaseModel):
    id: int
    id_cliente: int
    numero_conta: str
    saldo_cc: float
    