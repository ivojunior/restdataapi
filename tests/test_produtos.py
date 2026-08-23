from decimal import Decimal

from app.models.produto import Produto


def _produto(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        codigo="PROD001",
        descricao="Produto de Exemplo",
        tipo="PA",
        unidade_medida="UN",
        grupo="0001",
        local_padrao="01",
        preco_venda=Decimal("99.90"),
        bloqueado="2",
    )
    dados.update(overrides)
    return Produto(**dados)


def test_requer_api_key(client):
    assert client.get("/produtos/").status_code == 401


def test_listar_e_obter_produto(client, auth_headers, db_session):
    produto = _produto()
    db_session.add(produto)
    db_session.commit()
    db_session.refresh(produto)

    resposta_lista = client.get("/produtos/", headers=auth_headers)
    assert resposta_lista.status_code == 200
    assert len(resposta_lista.json()["items"]) == 1

    resposta = client.get(f"/produtos/{produto.rec_no}", headers=auth_headers)
    assert resposta.status_code == 200
    assert resposta.json()["descricao"] == "Produto de Exemplo"


def test_produtos_deletados_sao_ignorados(client, auth_headers, db_session):
    db_session.add_all(
        [
            _produto(codigo="PROD001"),
            _produto(codigo="PROD002", deletado="*"),
        ]
    )
    db_session.commit()

    resposta = client.get("/produtos/", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["codigo"] == "PROD001"


def test_filtro_por_grupo(client, auth_headers, db_session):
    db_session.add_all(
        [
            _produto(codigo="PROD001", grupo="0001"),
            _produto(codigo="PROD002", grupo="0002"),
        ]
    )
    db_session.commit()

    resposta = client.get("/produtos/?grupo=0002", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["codigo"] == "PROD002"


def test_metodos_de_escrita_nao_existem(client, auth_headers):
    assert client.post("/produtos/", json={}, headers=auth_headers).status_code == 405
    assert client.put("/produtos/1", json={}, headers=auth_headers).status_code == 405
    assert client.delete("/produtos/1", headers=auth_headers).status_code == 405
