from decimal import Decimal

from app.models.saldo_estoque import SaldoEstoque


def _saldo(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        codigo_produto="PROD001",
        local="01",
        saldo_atual=Decimal("120.0000"),
        quantidade_empenhada=Decimal("10.0000"),
        quantidade_reservada=Decimal("0.0000"),
        quantidade_pedido_venda=Decimal("5.0000"),
        quantidade_pedido_compra=Decimal("0.0000"),
        custo_medio=Decimal("35.5000"),
    )
    dados.update(overrides)
    return SaldoEstoque(**dados)


def test_requer_api_key(client):
    assert client.get("/saldos-estoque/").status_code == 401


def test_listar_e_obter_saldo(client, auth_headers, db_session):
    saldo = _saldo()
    db_session.add(saldo)
    db_session.commit()
    db_session.refresh(saldo)

    resposta_lista = client.get("/saldos-estoque/", headers=auth_headers)
    assert resposta_lista.status_code == 200
    assert resposta_lista.json()["total"] == 1

    resposta = client.get(f"/saldos-estoque/{saldo.rec_no}", headers=auth_headers)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["codigo_produto"] == "PROD001"
    assert dados["saldo_atual"] == "120.0000"


def test_saldos_deletados_sao_ignorados(client, auth_headers, db_session):
    db_session.add_all(
        [
            _saldo(codigo_produto="PROD001"),
            _saldo(codigo_produto="PROD002", deletado="*"),
        ]
    )
    db_session.commit()

    resposta = client.get("/saldos-estoque/", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["codigo_produto"] == "PROD001"


def test_filtro_por_codigo_produto(client, auth_headers, db_session):
    db_session.add_all(
        [
            _saldo(codigo_produto="PROD001", local="01"),
            _saldo(codigo_produto="PROD002", local="01"),
        ]
    )
    db_session.commit()

    resposta = client.get("/saldos-estoque/?codigo_produto=PROD002", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["codigo_produto"] == "PROD002"


def test_metodos_de_escrita_nao_existem(client, auth_headers):
    assert client.post("/saldos-estoque/", json={}, headers=auth_headers).status_code == 405
    assert client.put("/saldos-estoque/1", json={}, headers=auth_headers).status_code == 405
    assert client.delete("/saldos-estoque/1", headers=auth_headers).status_code == 405
