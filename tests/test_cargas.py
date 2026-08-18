from datetime import date, timedelta

from app.models.cliente import Cliente
from app.models.item_carga import ItemCarga
from app.models.veiculo_carga import VeiculoCarga


def _cliente(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        codigo="000456",
        loja="01",
        nome="Cliente Exemplo Ltda",
    )
    dados.update(overrides)
    return Cliente(**dados)


def _veiculo(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        codigo="000001",
        sequencia_carga="001",
        caminhao="ABC1234",
        carreta="XYZ5678",
        valor="1500.00",
    )
    dados.update(overrides)
    return VeiculoCarga(**dados)


def _item(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        codigo="000001",
        sequencia_carga="001",
        sequencia="000001",
        data=date.today().strftime("%Y%m%d"),
        pedido="000123",
        cliente="000456",
        loja="01",
        peso="1000.0000",
        nota_fiscal="000789",
    )
    dados.update(overrides)
    return ItemCarga(**dados)


def test_requer_api_key(client):
    assert client.get("/cargas/").status_code == 401


def test_lista_com_join_de_veiculo_e_cliente(client, auth_headers, db_session):
    db_session.add_all([_cliente(), _veiculo(), _item()])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["total"] == 1
    item = dados["items"][0]
    assert item["codigo"] == "000001"
    assert item["nome_cliente"] == "Cliente Exemplo Ltda"
    assert item["caminhao"] == "ABC1234"
    assert item["carreta"] == "XYZ5678"
    assert item["valor"] == "1500.00"


def test_item_sem_veiculo_correspondente_e_ignorado(client, auth_headers, db_session):
    db_session.add_all([_cliente(), _item()])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    assert resposta.json()["total"] == 0


def test_item_sem_cliente_correspondente_e_ignorado(client, auth_headers, db_session):
    db_session.add_all([_veiculo(), _item()])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    assert resposta.json()["total"] == 0


def test_sequencia_cancelada_e_ignorada(client, auth_headers, db_session):
    db_session.add_all([_cliente(), _veiculo(), _item(sequencia="999999")])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    assert resposta.json()["total"] == 0


def test_registros_deletados_sao_ignorados(client, auth_headers, db_session):
    db_session.add_all([_cliente(), _veiculo(), _item(deletado="*")])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    assert resposta.json()["total"] == 0


def test_sem_filtro_assume_data_atual(client, auth_headers, db_session):
    hoje = date.today().strftime("%Y%m%d")
    ontem = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
    db_session.add_all(
        [
            _cliente(),
            _veiculo(codigo="000001", sequencia_carga="001"),
            _item(codigo="000001", sequencia_carga="001", data=ontem),
            _veiculo(codigo="000002", sequencia_carga="001"),
            _item(codigo="000002", sequencia_carga="001", data=hoje),
        ]
    )
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["codigo"] == "000002"


def test_filtro_data_inicial_via_query_string(client, auth_headers, db_session):
    db_session.add_all(
        [
            _cliente(),
            _veiculo(codigo="000001", sequencia_carga="001"),
            _item(codigo="000001", sequencia_carga="001", data="20260101"),
            _veiculo(codigo="000002", sequencia_carga="001"),
            _item(codigo="000002", sequencia_carga="001", data="20260801"),
        ]
    )
    db_session.commit()

    resposta = client.get("/cargas/?data_inicial=20260801", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["codigo"] == "000002"


def test_metodos_de_escrita_nao_existem(client, auth_headers):
    assert client.post("/cargas/", json={}, headers=auth_headers).status_code == 405
    assert client.put("/cargas/", json={}, headers=auth_headers).status_code == 405
    assert client.delete("/cargas/", headers=auth_headers).status_code == 405
