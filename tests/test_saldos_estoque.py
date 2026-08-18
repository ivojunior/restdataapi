from decimal import Decimal

from app.models.produto import Produto
from app.models.saldo_estoque import SaldoEstoque


def _produto(**overrides):
    dados = dict(
        deletado=" ",
        filial="  ",
        codigo="PROD001",
        descricao="Produto Exemplo",
        tipo="PA",
        conversao=Decimal("1.0000"),
    )
    dados.update(overrides)
    return Produto(**dados)


def _saldo(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        codigo_produto="PROD001",
        local="01",
        saldo_atual=Decimal("120.0000"),
        valor_atual=Decimal("3500.00"),
    )
    dados.update(overrides)
    return SaldoEstoque(**dados)


def test_requer_api_key(client):
    assert client.get("/saldos-estoque/").status_code == 401


def test_lista_com_join_de_produto_e_conversao(client, auth_headers, db_session):
    db_session.add_all([_produto(), _saldo()])
    db_session.commit()

    resposta = client.get("/saldos-estoque/", headers=auth_headers)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["total"] == 1
    item = dados["items"][0]
    assert item["codigo_produto"] == "PROD001"
    assert item["descricao_produto"] == "Produto Exemplo"
    assert item["quantidade"] == "120"
    assert item["valor_atual"] == "3500.00"


def test_quantidade_e_dividida_pela_conversao_do_produto(client, auth_headers, db_session):
    db_session.add_all([
        _produto(conversao=Decimal("2.0000")),
        _saldo(saldo_atual=Decimal("100.0000")),
    ])
    db_session.commit()

    resposta = client.get("/saldos-estoque/", headers=auth_headers)
    assert resposta.json()["items"][0]["quantidade"] == "50"


def test_saldo_sem_produto_correspondente_e_ignorado(client, auth_headers, db_session):
    db_session.add(_saldo())
    db_session.commit()

    resposta = client.get("/saldos-estoque/", headers=auth_headers)
    assert resposta.json()["total"] == 0


def test_sem_filtro_de_tipo_ou_local_traz_qualquer_combinacao(client, auth_headers, db_session):
    db_session.add_all([
        _produto(codigo="PROD001", tipo="PA"),
        _saldo(codigo_produto="PROD001", local="01"),
        _produto(codigo="PROD002", tipo="AM"),
        _saldo(codigo_produto="PROD002", local="20"),
    ])
    db_session.commit()

    resposta = client.get("/saldos-estoque/", headers=auth_headers)
    assert resposta.json()["total"] == 2


def test_filtro_tipo_produto_via_query_string(client, auth_headers, db_session):
    db_session.add_all([
        _produto(codigo="PROD001", tipo="PA"),
        _saldo(codigo_produto="PROD001", local="01"),
        _produto(codigo="PROD002", tipo="AM"),
        _saldo(codigo_produto="PROD002", local="20"),
    ])
    db_session.commit()

    resposta = client.get("/saldos-estoque/?tipo_produto=AM", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["codigo_produto"] == "PROD002"


def test_filtro_local_via_query_string(client, auth_headers, db_session):
    db_session.add_all([
        _produto(codigo="PROD001"),
        _saldo(codigo_produto="PROD001", local="01"),
        _produto(codigo="PROD002"),
        _saldo(codigo_produto="PROD002", local="20"),
    ])
    db_session.commit()

    resposta = client.get("/saldos-estoque/?local=20", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["codigo_produto"] == "PROD002"


def test_filtro_tipo_e_local_combinados(client, auth_headers, db_session):
    db_session.add_all([
        _produto(codigo="PROD001", tipo="PA"),
        _saldo(codigo_produto="PROD001", local="01"),
        _produto(codigo="PROD002", tipo="AM"),
        _saldo(codigo_produto="PROD002", local="20"),
        _produto(codigo="PROD003", tipo="PA"),
        _saldo(codigo_produto="PROD003", local="20"),
    ])
    db_session.commit()

    resposta = client.get(
        "/saldos-estoque/?tipo_produto=AM&local=20", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["codigo_produto"] == "PROD002"


def test_saldo_zerado_ou_negativo_e_ignorado(client, auth_headers, db_session):
    db_session.add_all([
        _produto(),
        _saldo(codigo_produto="PROD001", saldo_atual=Decimal("0.0000")),
    ])
    db_session.commit()

    resposta = client.get("/saldos-estoque/", headers=auth_headers)
    assert resposta.json()["total"] == 0


def test_registros_deletados_sao_ignorados(client, auth_headers, db_session):
    db_session.add_all([
        _produto(),
        _saldo(codigo_produto="PROD001"),
        _saldo(codigo_produto="PROD001", deletado="*"),
    ])
    db_session.commit()

    resposta = client.get("/saldos-estoque/", headers=auth_headers)
    assert resposta.json()["total"] == 1


def test_metodos_de_escrita_nao_existem(client, auth_headers):
    assert client.post("/saldos-estoque/", json={}, headers=auth_headers).status_code == 405
    assert client.put("/saldos-estoque/", json={}, headers=auth_headers).status_code == 405
    assert client.delete("/saldos-estoque/", headers=auth_headers).status_code == 405
