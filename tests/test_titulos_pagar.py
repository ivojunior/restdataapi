from decimal import Decimal

from app.models.titulo_pagar import TituloPagar


def _titulo(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        prefixo="PAG",
        numero="000001",
        parcela="01",
        tipo="NF",
        fornecedor="000123",
        loja="01",
        emissao="20260101",
        vencimento_original="20260201",
        vencimento="20260201",
        valor=Decimal("1500.00"),
        saldo=Decimal("1500.00"),
        moeda="01",
        historico="Compra de material",
        data_baixa="",
    )
    dados.update(overrides)
    return TituloPagar(**dados)


def test_requer_api_key(client):
    assert client.get("/titulos-pagar/").status_code == 401


def test_listar_e_obter_titulo(client, auth_headers, db_session):
    titulo = _titulo()
    db_session.add(titulo)
    db_session.commit()
    db_session.refresh(titulo)

    resposta_lista = client.get("/titulos-pagar/", headers=auth_headers)
    assert resposta_lista.status_code == 200
    assert resposta_lista.json()["total"] == 1

    resposta = client.get(f"/titulos-pagar/{titulo.rec_no}", headers=auth_headers)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["fornecedor"] == "000123"
    assert dados["valor"] == "1500.00"


def test_titulos_deletados_sao_ignorados(client, auth_headers, db_session):
    db_session.add_all(
        [
            _titulo(numero="000001"),
            _titulo(numero="000002", deletado="*"),
        ]
    )
    db_session.commit()

    resposta = client.get("/titulos-pagar/", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["numero"] == "000001"


def test_obter_titulo_deletado_retorna_404(client, auth_headers, db_session):
    titulo = _titulo(deletado="*")
    db_session.add(titulo)
    db_session.commit()
    db_session.refresh(titulo)

    resposta = client.get(f"/titulos-pagar/{titulo.rec_no}", headers=auth_headers)
    assert resposta.status_code == 404


def test_filtro_por_fornecedor(client, auth_headers, db_session):
    db_session.add_all(
        [
            _titulo(numero="000001", fornecedor="000123"),
            _titulo(numero="000002", fornecedor="000456"),
        ]
    )
    db_session.commit()

    resposta = client.get("/titulos-pagar/?fornecedor=000456", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["fornecedor"] == "000456"


def test_metodos_de_escrita_nao_existem(client, auth_headers):
    assert client.post("/titulos-pagar/", json={}, headers=auth_headers).status_code == 405
    assert client.put("/titulos-pagar/1", json={}, headers=auth_headers).status_code == 405
    assert client.delete("/titulos-pagar/1", headers=auth_headers).status_code == 405
