
import sqlite3
from pathlib import Path
from typing import Dict, Optional, Any
import uuid

ROOT_DIR = Path(__file__).resolve().parent
DB_FILE = ROOT_DIR / 'db_banco.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS "clientes" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT NOT NULL,
                documento TEXT UNIQUE NOT NULL,
                correntista INTEGER NOT NULL CHECK (correntista IN (0,1))
            );
            '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS "contas" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL,
                numero_conta TEXT NOT NULL UNIQUE,
                saldo_cc REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (id_cliente) REFERENCES clientes(documento) ON DELETE CASCADE
            );
            '''
        )
        conn.commit()

#cadastrar cliente novo
def inserir_cliente(nome: str, telefone: str, documento: str, correntista: bool) -> Dict[str, Any]:
    # sqlite não tem bool: converter para int
    correntista_int = 1 if correntista else 0
    
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO "clientes" (nome, telefone, documento, correntista) VALUES (?, ?, ?, ?)',
                (nome, telefone, documento, correntista_int)
            )
            conn.commit()
            cliente_id = cursor.lastrowid
            cursor.execute('SELECT * FROM "clientes" WHERE id = ?', (cliente_id,))
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
def atualiza_cliente_db(id_cliente: int, nome: str, telefone: str, correntista: bool) -> Dict[str, Any]:
    correntista_int = 1 if correntista else 0
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE "clientes" SET nome = ?, telefone = ?, correntista = ? WHERE id = ?',
            (nome, telefone, correntista_int, id_cliente)
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f'Nenhum cliente encontrado com o CPF {id_cliente}')
        return dict(row)

#exclui cliente
def deletar_cliente(documento: str):
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
            'SELECT * FROM "contas" WHERE id = ?',
            (conta_id,)
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
        
if __name__ == "__main__":
    create_tables()
