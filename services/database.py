
from multiprocessing import Value
import sqlite3
from pathlib import Path
from typing import Dict, Optional, Any
import uuid

from models.schemas import TipoEnum

ROOT_DIR = Path(__file__).resolve().parent
DB_FILE = ROOT_DIR / 'db_banco.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables() -> None:
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS "clientes" (
                documento TEXT PRIMARY KEY UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                telefone TEXT NOT NULL,
                correntista INTEGER NOT NULL CHECK (correntista IN (0,1)),
                investidor INTEGER NOT NULL CHECK (investidor IN (0,1))
            );
            '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS "contas" (
                id_cliente TEXT NOT NULL,
                numero_conta TEXT PRIMARY KEY NOT NULL UNIQUE,
                saldo_cc REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (id_cliente) REFERENCES clientes(documento) ON DELETE CASCADE
            );
            '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS "investidor" (
                id_cliente TEXT PRIMARY KEY NOT NULL,
                nome TEXT NOT NULL,
                telefone TEXT NOT NULL,
                perfil TEXT NOT NULL,
                email TEXT NOT NULL,
                patrimonio REAL NOT NULL DEFAULT 0.0,
                data_cadastro TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                CONSTRAINT perfil_valido CHECK (perfil IN ('CONSERVADOR', 'MODERADO', 'ARROJADO')),
                FOREIGN KEY (id_cliente) REFERENCES clientes(documento) ON DELETE CASCADE
            );
            '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS "investimento" (
                id_investimento TEXT PRIMARY KEY NOT NULL UNIQUE,
                id_cliente TEXT NOT NULL,
                tipo TEXT NOT NULL,
                valor_investido REAL NOT NULL DEFAULT 0.0,
                data_aplicacao TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                rentabilidade DECIMAL NOT NULL,
                ativo INTEGER NOT NULL CHECK(ativo IN (0,1)),
                CONSTRAINT tipo_valido CHECK (tipo IN ('RENDA FIXA', 'ACOES', 'FUNDOS', 'CRIPTO'))
            )
            '''
        )
        conn.commit()





#cadastrar cliente novo
def inserir_cliente(nome: str, telefone: str, documento: str, correntista: bool, investidor: bool) -> Dict[str, Any]:
    # sqlite não tem bool: converter para int
    correntista_int = 1 if correntista else 0
    investidor_int = 1 if investidor else 0
    
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO "clientes" (nome, telefone, documento, correntista, investidor) VALUES (?, ?, ?, ?, ?)',
                (nome, telefone, documento, correntista_int, investidor_int)
            )
            conn.commit()
            cursor.execute('SELECT * FROM "clientes" WHERE documento = ?', (documento,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            else:
                return None
        except sqlite3.IntegrityError:
            raise ValueError(f'O documento {documento} já está cadastrado.')
    

#busca o cliente por CPF
def busca_cliente(documento: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM "clientes" WHERE documento = ?',
            (documento,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

#buscar cliente por nome
def busca_cliente_por_nome(nome: str) -> list[Dict[str, Any]]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        #collate nocase ignora letras maiusculas e minusculas
        cursor.execute(
            'SELECT * FROM "clientes" WHERE nome LIKE ? COLLATE NOCASE',
            (f"%{nome}%",)
        )
        rows = cursor.fetchall()
        print(f'Linhas encontradas{len(rows)}')
        return [dict(r) for r in rows]
    
#atualiza cadastro do client    
def atualiza_cliente_db(documento: str, nome: str, telefone: str) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE "clientes" SET nome = ?, telefone = ? WHERE documento = ?',
            (nome, telefone, documento)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None
        return (f'Cliente atualizado: \n Documento: {documento},\n Nome: {nome}, \n Telefone: {telefone}\n')

#exclui cliente
def deletar_cliente(documento: str):
    saldo = busca_conta(documento).get('saldo')
    if saldo != 0:
        raise Exception('Impossível excluir uma conta com saldo.')
    else:
        with get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM "clientes" WHERE documento = ?', (documento,)
            )
            if cursor.rowcount == 0:
                raise ValueError(f'Cliente com o CPF {documento} não encontrado.')
            else:
                return 'Cliente excluído com sucesso.'
            return True
        conn.commit()


#cria conta
def nova_conta(id_cliente: str, saldo_cc: float) -> Dict[str, Any]:
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        #verificar se o cliente está cadastrado
        cursor.execute(
                'SELECT 1 FROM "clientes" WHERE documento = ?',
                (id_cliente,)
        )

        if cursor.fetchone() is None:
            raise ValueError(f'Nenhum cliente cadastrado com o CPF: {id_cliente}')
        numero_conta = str(int(uuid.uuid4().int % 10 ** 8)).zfill(8)
        try:
            cursor.execute(
                'INSERT INTO "contas" (id_cliente, numero_conta, saldo_cc) VALUES (?,?,?)',
                (id_cliente, numero_conta, saldo_cc)
            )
        except sqlite3.IntegrityError as e:
            raise ValueError(f'Impossível criar conta: {e}')
        
        conta_id = cursor.lastrowid
        cursor.execute(
            'SELECT * FROM "contas" WHERE numero_conta = ?',
            (numero_conta,)
        )

        row = cursor.fetchone()
        return dict(row)
    
#busca conta pelo cpf do cliente
def busca_conta(documento: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM "contas" WHERE id_cliente = ?',
            (documento,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        else:
            return None
        
#atualizar saldo da conta
def atualizar_saldo_db(numero_conta: str, novo_saldo: float) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE "contas" SET saldo_cc = ? WHERE numero_conta = ?',
            (novo_saldo, numero_conta,)
        )
        conn.commit()
        cursor.execute(
            'SELECT * FROM "contas" WHERE numero_conta = ?',
            (numero_conta,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        else:
            raise ValueError(f'Conta não encontrada.')
        
#cadastro do investidor
def cadastrar_investidor_db(id_cliente: str, nome: str, telefone: str, email: str, patrimonio: float, perfil: str):
    with get_connection() as conn:
        cursor = conn.cursor() 
        try:
            cursor.execute(
                'INSERT INTO "investidor" (id_cliente, nome, telefone, email, patrimonio, perfil) VALUES (?, ?, ?, ?, ?, ?)',
                (id_cliente, nome, telefone, email, patrimonio, perfil)
            )
            conn.commit()
            cursor.execute('SELECT * FROM "investidor" WHERE id_cliente = ?', (id_cliente,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            else:
                return None
        except sqlite3.IntegrityError:
            raise ValueError(f'O investidor com CPF {id_cliente} já possui cadastro.')


#atualizar dados do investidor
def atualiza_investidor_db(id_cliente: str, telefone: str, email: str, patrimonio: float, perfil: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE "investidor" SET telefone = ?, email = ?, patrimonio = ?, perfil = ? WHERE id_cliente = ?',
            (telefone, email, patrimonio, perfil, id_cliente)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None
        return(f'Cliente atualizado: \n CPF: {id_cliente}, \n Email: {email}, \n Telefone: {telefone}, \n Patrimônio: {patrimonio}, \n Perfil: {perfil}')

#excluir cadastro do investidor
def excluir_investidor_db(id_cliente: str):
    saldo = busca_conta(id_cliente).get('saldo')
    if saldo != 0:
        raise Exception('Impossível excluir cadastro com saldo na conta.')
    else:
        with get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM "investidor" WHERE id_cliente = ?', (id_cliente)
            )
            if cursor.rowcount == 0:
                raise ValueError('Cliente não encontrado.')
            else:
                return 'Cliente excluído com sucesso.'
            return True
        conn.commit()
       
#buscar cadastro do investidor pelo documento
def busca_investidor_db(id_cliente: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id_cliente, nome, telefone, email, perfil FROM "investidor" WHERE id_cliente = ?', (id_cliente,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        else:
            return None
        

#criar novo investimento
def novo_investimento_db(id_cliente: str, tipo: TipoEnum, valor_investido: float, rentabilidade: float, ativo: bool):
    ativo = 1 if ativo else 0
    id_investimento = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        #antes de criar o investimento, verificar se o cliente existe e se é investidor
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM "investidor" WHERE id_cliente = ?', (id_cliente,))
        if cursor.fetchone() is None:
            raise ValueError(f'O CPF {id_cliente} não está associado à nenhum investidor.')
        #verificar se o cliente tem saldo disponível para investir
        try:
            saldo = cursor.execute('SELECT saldo_cc FROM "contas" WHERE id_cliente = ?', (id_cliente,))
            if valor_investido > saldo:
                raise ValueError('Saldo insuficiente para realizar o investimento.')
            else:
                saldo -= valor_investido
        except sqlite3.IntegrityError as e:
            raise Exception(f'Erro ao verificar o saldo da conta: {e}')


        try:
            cursor.execute(
                'INSERT INTO "investimento" (id_investimento, id_cliente, tipo, valor_investido, rentabilidade, ativo) VALUES (?,?,?,?,?,?)', 
                (id_investimento, id_cliente, tipo, valor_investido, rentabilidade, ativo) 
            )
        except sqlite3.IntegrityError as e:
            raise ValueError(f'Impossível criar investimento: {e}')
        
        investimento_salvo = cursor.lastrowid
        cursor.execute('SELECT * FROM "investimento" WHERE id_investimento = ?', (id_investimento,))
        row = cursor.fetchone()

        patrimonio += valor_investido
        if row:
            cursor.execute('UPDATE 1 FROM "contas" set saldo_cc = ? WHERE id_cliente = ?', (saldo, id_cliente,))
            cursor.execute('UPDATE 1 FROM "investidor" SET patrimonio = ? WHERE id_cliente = ?', (patrimonio, id_cliente,))
            conn.commit()

        return dict(row)
    
#buscar investimento pelo ID
def busca_investimento_db(id_investimento: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id_investimento, id_cliente, valor_investido, rentabilidade, data_aplicacao, tipo, ativo FROM "investimento" where id_investimento = ?', (id_investimento,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        else:
            return None
        
#buscar investimento pelo doc do cliente
def busca_investimento_doc(id_cliente: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM "investimento" WHERE id_cliente = ?', (id_cliente,)
        )
        row = cursor.fetchall()
        if row:
            return dict(row)
        else:
            return None

#atualizar dados do investimentoados do investimento
def atualiza_investimento_db(id_investimento: str,  novo_valor: float, ativo: bool, tipo: TipoEnum, id_cliente: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        patrimonio = cursor.execute('SELECT patrimonio from "investidor" WHERE id_cliente = ?', (id_cliente,))
        valor_investido = cursor.execute('SELECT valor_investido from "investimento" WHERE id_investimento = ?', (id_investimento,))
        novo_valor += valor_investido

        if tipo == 'RENDA FIXA':
            try:
                saldo = cursor.execute('SELECT saldo_cc FROM "contas" WHERE id_cliente = ?', (id_cliente,))
                if novo_valor > saldo:
                    raise ValueError('Saldo insuficiente para realizar o investimento.')
            except sqlite3.IntegrityError as e:
                raise Exception(f'Erro ao verificar o saldo da conta: {e}')
            cursor.execute('UPDATE "investimento" SET valor_investido = ?, ativo = ? WHERE id_investimento = ?', (novo_valor, ativo, id_investimento))
            conn.commit()
            if cursor.rowcount == 0:
                return None
        
        return (f'Investimento atualizado: \n ID: {id_investimento}, \n Valor investido: R${novo_valor}, \n Tipo: {tipo}, \n Status: {ativo}')
    
    
# #excluir investimento
def retirada_investimento_db(id_investimento: str, valor_retirada: float, id_cliente: str):
    valor = busca_investimento_db(id_investimento).get('valor_investido')
    #verifica se a retirada é maior do que o valor investido
    if valor < valor_retirada:
        raise Exception('Saldo insuficiente para retirada.')
    else:
        with get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM "investimento" WHERE id_investimento = ?', (id_investimento)
            )
            conn.commit()
        return (f'Investimento {id_investimento} excluído com sucesso!')


if __name__ == "__main__":
    create_tables()
