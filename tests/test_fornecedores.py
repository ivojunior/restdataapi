from app.models.fornecedor import Fornecedor


def _fornecedor(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        codigo="000123",
        loja="01",
        nome="Fornecedor Exemplo Ltda",
        nome_reduzido="Fornecedor Ex.",
        cnpj_cpf="12345678000199",
        estado="SP",
        municipio="São Paulo",
        tipo="J",
        bloqueado="2",
    )
    dados.update(overrides)
    return Fornecedor(**dados)


def test_requer_api_key(client):
    assert client.get("/fornecedores/").status_code == 401


def test_listar_e_obter_fornecedor(client, auth_headers, db_session):
    fornecedor = _fornecedor()
    db_session.add(fornecedor)
    db_session.commit()
    db_session.refresh(fornecedor)

    resposta_lista = client.get("/fornecedores/", headers=auth_headers)
    assert resposta_lista.status_code == 200
    assert resposta_lista.json()["total"] == 1

    resposta = client.get(f"/fornecedores/{fornecedor.rec_no}", headers=auth_headers)
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Fornecedor Exemplo Ltda"


def test_fornecedores_deletados_sao_ignorados(client, auth_headers, db_session):
    db_session.add_all(
        [
            _fornecedor(codigo="000123"),
            _fornecedor(codigo="000456", deletado="*"),
        ]
    )
    db_session.commit()

    resposta = client.get("/fornecedores/", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["codigo"] == "000123"


def test_filtro_por_cnpj_cpf(client, auth_headers, db_session):
    db_session.add_all(
        [
            _fornecedor(codigo="000123", cnpj_cpf="11111111000191"),
            _fornecedor(codigo="000456", cnpj_cpf="22222222000192"),
        ]
    )
    db_session.commit()

    resposta = client.get("/fornecedores/?cnpj_cpf=22222222000192", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["codigo"] == "000456"


def test_metodos_de_escrita_nao_existem(client, auth_headers):
    assert client.post("/fornecedores/", json={}, headers=auth_headers).status_code == 405
    assert client.put("/fornecedores/1", json={}, headers=auth_headers).status_code == 405
    assert client.delete("/fornecedores/1", headers=auth_headers).status_code == 405
