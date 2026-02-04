from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class PerfilEnum(str, Enum):
    conservador = 'CONSERVADOR'
    moderado = 'MODERADO'
    arrojado = 'ARROJADO'

RENTABILIDADE_PERFIL = {
    PerfilEnum.conservador: 0.08,
    PerfilEnum.moderado: 0.12,
    PerfilEnum.arrojado: 0.18
}

class TipoEnum(str, Enum):
    renda_fixa = 'RENDA FIXA'
    acoes = 'ACOES'
    fundos = 'FUNDOS'
    cripto = 'CRIPTO'

#sufixo IN: modelo p/ entrada dos dados
class ClienteIn(BaseModel):
    nome: str = Field(..., min_length= 1)
    telefone: str = Field(..., min_length= 11, max_length= 11)
    documento: str = Field(..., min_length= 11, max_length= 11)
    correntista: bool = Field(False)

#sufixo OUT: como o programa vai liberar os dados

class ClienteOut(BaseModel):
    nome: str
    telefone: str
    documento: str
    correntista: bool

class ContaIn(BaseModel):
    #ge: greater than or equal to, garante que o campo não está vazio
    id_cliente: str = Field(..., ge=1)
    saldo: float = Field(0.0, ge = 0.0)

class ContaOut(BaseModel):
    id_cliente: int
    numero_conta: str
    saldo_cc: float
    

class InvestidorIn(BaseModel):
    id_cliente: str
    nome: str
    telefone: str
    email: str
    patrimonio: float
    perfil: PerfilEnum


class InvestimentoIn(BaseModel):
    id: str
    id_cliente: str
    tipo: TipoEnum
    valor_investido: float
    rentabilidade: float
    ativo: bool
    ticker: Optional[str] = None