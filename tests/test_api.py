import pytest
from fastapi.testclient import TestClient
from api_banco import app
import random

client = TestClient(app)



def test_busca_cliente_inexistente():
    response = client.get("/clientes/00000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Cliente não encontrado."

def test_busca_por_nome_inexistente():
    response = client.get("/clientes/busca/nome", params={"nome": "NomeInexistente123"})
    assert response.status_code == 404


def test_fluxo_cadastro_e_exclusao():
    doc_valido = "11200099921"
    tel_valido = "11988887777" 
    
    params = {
        "nome": "Stephanie Teste",
        "telefone": tel_valido,
        "documento": doc_valido,
        "correntista": True
    }

    response_post = client.post("/clientes", params=params)
    
    assert response_post.status_code == 200, f"Erro no cadastro: {response_post.json()}"
    assert response_post.json()["documento"] == doc_valido

    response_del = client.delete(f"/clientes/{doc_valido}")
    
    assert response_del.status_code == 200
    assert response_del.json() == "Cadastro excluído com sucesso."


def test_erro_validacao_nome_curto():
    params = {
        "nome": "Ab",
        "telefone": "11999998888",
        "documento": "12345678901",
        "correntista": True
    }
    response = client.post("/clientes", params=params)
    
    assert response.status_code == 400
    assert "Dados inválidos" in response.json()["detail"]

def test_erro_validacao_documento_invalido():
    params = {
        "nome": "Cliente Erro",
        "telefone": "11999998888",
        "documento": "123",
        "correntista": True
    }
    response = client.post("/clientes", params=params)
    assert response.status_code == 400