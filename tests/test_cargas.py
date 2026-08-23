from datetime import date, timedelta

from app.models.cliente import Cliente
from app.models.item_carga import ItemCarga
from app.models.nota_fiscal_saida import NotaFiscalSaida
from app.models.percurso import Percurso
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
        status="1",
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
        percurso="0001",
        pedido="000123",
        cliente="000456",
        loja="01",
        peso="1000.0000",
        nota_fiscal="000789",
        serie="1",
    )
    dados.update(overrides)
    return ItemCarga(**dados)


def _percurso(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        codigo="0001",
        descricao="Rota Padrão",
    )
    dados.update(overrides)
    return Percurso(**dados)


def _nota_fiscal(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        prefixo="1",
        numero="000789",
        cliente="000456",
        loja="01",
        valor="1500.00",
        parcela="  ",
        tipo="NF ",
        carga="000001",
        sequencia_carga="001",
    )
    dados.update(overrides)
    return NotaFiscalSaida(**dados)


def test_requer_api_key(client):
    assert client.get("/cargas/").status_code == 401


def test_lista_com_join_de_veiculo_e_cliente(client, auth_headers, db_session):
    db_session.add_all([_cliente(), _veiculo(), _item(), _nota_fiscal(), _percurso()])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert len(dados["items"]) == 1
    item = dados["items"][0]
    assert item["codigo"] == "000001"
    assert item["nome_cliente"] == "Cliente Exemplo Ltda"
    assert item["caminhao"] == "ABC1234"
    # status "1" não está em ("7","8") -> case() do SQLAlchemy classifica como "Aberta".
    assert item["status_carga"] == "Aberta"
    assert item["valor"] == "1500.00"
    assert item["percurso"] == "0001"
    assert item["descricao_percurso"] == "Rota Padrão"


def test_caminhao_placa_cliente_e_status_fechada_sao_formatados(client, auth_headers, db_session):
    # select_cargas.sql calcula CAMINHAO ("Cliente" no lugar da placa
    # KHA0902) e STATUS ("Fechada"/"Aberta") com CASE — replicado em
    # app/routers/cargas.py com case() do SQLAlchemy.
    db_session.add_all(
        [
            _cliente(),
            _veiculo(caminhao="KHA0902", status="8"),
            _item(),
            _percurso(),
        ]
    )
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["caminhao"] == "Cliente"
    assert dados["items"][0]["status_carga"] == "Fechada"


def test_item_sem_percurso_correspondente_e_ignorado(client, auth_headers, db_session):
    db_session.add_all([_cliente(), _veiculo(), _item()])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    assert len(resposta.json()["items"]) == 0


def test_valor_vem_da_nota_fiscal_nao_do_veiculo(client, auth_headers, db_session):
    # select_cargas.sql busca o valor em SE1070 (nota fiscal), casando
    # filial/série/número/cliente/loja — não é um campo de DAK070.
    db_session.add_all(
        [
            _cliente(),
            _veiculo(),
            _item(serie="2", nota_fiscal="000999"),
            _nota_fiscal(prefixo="2", numero="000999", valor="777.77"),
            _nota_fiscal(prefixo="1", numero="000789", valor="1500.00"),  # não deve casar
            _percurso(),
        ]
    )
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["valor"] == "777.77"


def test_valor_e_zero_sem_nota_fiscal_correspondente(client, auth_headers, db_session):
    db_session.add_all([_cliente(), _veiculo(), _item(), _percurso()])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["valor"] == "0.00"


def test_filtro_status_encerrada_agrupa_codigos_7_e_8(client, auth_headers, db_session):
    db_session.add_all(
        [
            _cliente(),
            _veiculo(codigo="000001", sequencia_carga="001", status="1"),
            _item(codigo="000001", sequencia_carga="001"),
            _veiculo(codigo="000002", sequencia_carga="001", status="7"),
            _item(codigo="000002", sequencia_carga="001"),
            _veiculo(codigo="000003", sequencia_carga="001", status="8"),
            _item(codigo="000003", sequencia_carga="001"),
            _percurso(),
        ]
    )
    db_session.commit()

    resposta = client.get("/cargas/?status=encerrada", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 2
    assert {item["codigo"] for item in dados["items"]} == {"000002", "000003"}


def test_filtro_status_aberta_agrupa_demais_codigos(client, auth_headers, db_session):
    db_session.add_all(
        [
            _cliente(),
            _veiculo(codigo="000001", sequencia_carga="001", status="1"),
            _item(codigo="000001", sequencia_carga="001"),
            _veiculo(codigo="000002", sequencia_carga="001", status="6"),
            _item(codigo="000002", sequencia_carga="001"),
            _veiculo(codigo="000003", sequencia_carga="001", status="7"),
            _item(codigo="000003", sequencia_carga="001"),
            _percurso(),
        ]
    )
    db_session.commit()

    resposta = client.get("/cargas/?status=aberta", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 2
    assert {item["codigo"] for item in dados["items"]} == {"000001", "000002"}


def test_filtro_status_invalido_retorna_422(client, auth_headers):
    resposta = client.get("/cargas/?status=fechada", headers=auth_headers)
    assert resposta.status_code == 422


def test_filtro_data_final_via_query_string(client, auth_headers, db_session):
    db_session.add_all(
        [
            _cliente(),
            _veiculo(codigo="000001", sequencia_carga="001"),
            _item(codigo="000001", sequencia_carga="001", data="20260805"),
            _veiculo(codigo="000002", sequencia_carga="001"),
            _item(codigo="000002", sequencia_carga="001", data="20260815"),
            _percurso(),
        ]
    )
    db_session.commit()

    resposta = client.get(
        "/cargas/?data_inicial=20260801&data_final=20260810", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["codigo"] == "000001"


def test_item_sem_veiculo_correspondente_e_ignorado(client, auth_headers, db_session):
    db_session.add_all([_cliente(), _item(), _percurso()])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    assert len(resposta.json()["items"]) == 0


def test_item_sem_cliente_correspondente_e_ignorado(client, auth_headers, db_session):
    db_session.add_all([_veiculo(), _item(), _percurso()])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    assert len(resposta.json()["items"]) == 0


def test_sequencia_cancelada_e_ignorada(client, auth_headers, db_session):
    db_session.add_all([_cliente(), _veiculo(), _item(sequencia="999999"), _percurso()])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    assert len(resposta.json()["items"]) == 0


def test_registros_deletados_sao_ignorados(client, auth_headers, db_session):
    db_session.add_all([_cliente(), _veiculo(), _item(deletado="*"), _percurso()])
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    assert len(resposta.json()["items"]) == 0


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
            _percurso(),
        ]
    )
    db_session.commit()

    resposta = client.get("/cargas/", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["codigo"] == "000002"


def test_filtro_data_inicial_via_query_string(client, auth_headers, db_session):
    db_session.add_all(
        [
            _cliente(),
            _veiculo(codigo="000001", sequencia_carga="001"),
            _item(codigo="000001", sequencia_carga="001", data="20260101"),
            _veiculo(codigo="000002", sequencia_carga="001"),
            _item(codigo="000002", sequencia_carga="001", data="20260801"),
            _percurso(),
        ]
    )
    db_session.commit()

    resposta = client.get("/cargas/?data_inicial=20260801", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["codigo"] == "000002"


def test_metodos_de_escrita_nao_existem(client, auth_headers):
    assert client.post("/cargas/", json={}, headers=auth_headers).status_code == 405
    assert client.put("/cargas/", json={}, headers=auth_headers).status_code == 405
    assert client.delete("/cargas/", headers=auth_headers).status_code == 405
