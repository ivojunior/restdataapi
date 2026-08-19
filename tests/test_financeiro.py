from datetime import date, timedelta

from app.models.fornecedor import Fornecedor
from app.models.tipo_operacao import TipoOperacao
from app.models.titulo_pagar import TituloPagar


def _fornecedor(**overrides):
    dados = dict(
        deletado=" ",
        filial="  ",
        codigo="000123",
        loja="01",
        nome="Fornecedor Exemplo Ltda",
    )
    dados.update(overrides)
    return Fornecedor(**dados)


def _tipo_operacao(**overrides):
    dados = dict(
        deletado=" ",
        filial="  ",
        codigo="001",
        descricao="Compra de Mercadoria",
    )
    dados.update(overrides)
    return TipoOperacao(**dados)


def _titulo(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        prefixo="A",
        numero="000001",
        parcela="01",
        tipo="NF",
        fornecedor="000123",
        loja="01",
        emissao="20260301",
        vencimento=date.today().strftime("%Y%m%d"),
        vencimento_real=date.today().strftime("%Y%m%d"),
        valor="1000.00",
        saldo="1000.00",
        moeda="01",
        historico="Compra de mercadorias",
        codigo_operacao="001",
        nome_fornecedor="Fornecedor Exemplo Ltda",
    )
    dados.update(overrides)
    return TituloPagar(**dados)


def test_requer_api_key(client):
    assert client.get("/financeiro/").status_code == 401


def test_lista_com_join_de_fornecedor_e_tipo_operacao(client, auth_headers, db_session):
    db_session.add_all([_fornecedor(), _tipo_operacao(), _titulo()])
    db_session.commit()

    resposta = client.get("/financeiro/", headers=auth_headers)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["total"] == 1
    item = dados["items"][0]
    assert item["numero"] == "000001"
    assert item["nome_fornecedor"] == "Fornecedor Exemplo Ltda"
    assert item["descricao_operacao"] == "Compra de Mercadoria"


def test_expoe_recuperacao_judicial(client, auth_headers, db_session):
    db_session.add_all(
        [
            _fornecedor(),
            _titulo(numero="000001", recuperacao_judicial="1"),
            _titulo(numero="000002", recuperacao_judicial="2"),
            _titulo(numero="000003"),
        ]
    )
    db_session.commit()

    resposta = client.get("/financeiro/", headers=auth_headers)
    valores = {item["numero"]: item["recuperacao_judicial"] for item in resposta.json()["items"]}
    assert valores["000001"] == "1"
    assert valores["000002"] == "2"
    assert valores["000003"] is None


def test_titulo_sem_tipo_operacao_correspondente_ainda_aparece(client, auth_headers, db_session):
    db_session.add_all([_fornecedor(), _titulo(codigo_operacao="999")])
    db_session.commit()

    resposta = client.get("/financeiro/", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["descricao_operacao"] is None


def test_titulo_sem_fornecedor_correspondente_e_ignorado(client, auth_headers, db_session):
    db_session.add(_titulo())
    db_session.commit()

    resposta = client.get("/financeiro/", headers=auth_headers)
    assert resposta.json()["total"] == 0


def test_tipos_excluidos_sao_ignorados(client, auth_headers, db_session):
    db_session.add_all(
        [
            _fornecedor(),
            _titulo(numero="000001", tipo="NF"),
            _titulo(numero="000002", tipo="PA"),
            _titulo(numero="000003", tipo="PR"),
            _titulo(numero="000004", tipo="NDF"),
        ]
    )
    db_session.commit()

    resposta = client.get("/financeiro/", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["numero"] == "000001"


def test_sem_filtro_ignora_vencimento_anterior_a_hoje(client, auth_headers, db_session):
    ontem = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
    db_session.add_all(
        [
            _fornecedor(),
            _titulo(numero="000001", vencimento_real=ontem),
        ]
    )
    db_session.commit()

    resposta = client.get("/financeiro/", headers=auth_headers)
    assert resposta.json()["total"] == 0


def test_filtro_vencimento_de_via_query_string(client, auth_headers, db_session):
    ontem = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
    hoje = date.today().strftime("%Y%m%d")
    db_session.add_all(
        [
            _fornecedor(),
            _titulo(numero="000001", vencimento_real=ontem),
            _titulo(numero="000002", vencimento_real=hoje),
        ]
    )
    db_session.commit()

    resposta = client.get(f"/financeiro/?vencimento_de={ontem}", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 2

    resposta = client.get(f"/financeiro/?vencimento_de={hoje}", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["numero"] == "000002"


def test_filtro_vencimento_ate_via_query_string(client, auth_headers, db_session):
    hoje = date.today().strftime("%Y%m%d")
    amanha = (date.today() + timedelta(days=1)).strftime("%Y%m%d")
    db_session.add_all(
        [
            _fornecedor(),
            _titulo(numero="000001", vencimento_real=hoje),
            _titulo(numero="000002", vencimento_real=amanha),
        ]
    )
    db_session.commit()

    resposta = client.get(
        f"/financeiro/?vencimento_de={hoje}&vencimento_ate={hoje}", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["numero"] == "000001"


def test_filtro_status_baixado_via_query_string(client, auth_headers, db_session):
    hoje = date.today().strftime("%Y%m%d")
    db_session.add_all(
        [
            _fornecedor(),
            _titulo(numero="000001", vencimento_real=hoje, data_baixa=hoje),
            _titulo(numero="000002", vencimento_real=hoje, data_baixa=""),
        ]
    )
    db_session.commit()

    resposta = client.get("/financeiro/?status=baixado", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["numero"] == "000001"


def test_filtro_status_baixado_ignora_data_baixa_so_com_espacos(client, auth_headers, db_session):
    hoje = date.today().strftime("%Y%m%d")
    db_session.add_all(
        [
            _fornecedor(),
            _titulo(numero="000001", vencimento_real=hoje, data_baixa="        "),
        ]
    )
    db_session.commit()

    resposta = client.get("/financeiro/?status=baixado", headers=auth_headers)
    assert resposta.json()["total"] == 0

    resposta = client.get("/financeiro/?status=em_aberto", headers=auth_headers)
    assert resposta.json()["total"] == 1


def test_filtro_status_em_aberto_via_query_string(client, auth_headers, db_session):
    hoje = date.today().strftime("%Y%m%d")
    db_session.add_all(
        [
            _fornecedor(),
            _titulo(numero="000001", vencimento_real=hoje, data_baixa=""),
            _titulo(numero="000002", vencimento_real=hoje, data_baixa=hoje),
        ]
    )
    db_session.commit()

    resposta = client.get("/financeiro/?status=em_aberto", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["numero"] == "000001"


def test_filtro_status_vencido_via_query_string(client, auth_headers, db_session):
    # vencimento_de precisa ser recuado, senão o filtro padrão de período
    # (vencimento_real >= hoje) já exclui o título vencido antes do status.
    ontem = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
    hoje = date.today().strftime("%Y%m%d")
    db_session.add_all(
        [
            _fornecedor(),
            _titulo(numero="000001", vencimento_real=ontem, data_baixa=""),
            _titulo(numero="000002", vencimento_real=hoje, data_baixa=""),
        ]
    )
    db_session.commit()

    resposta = client.get(
        f"/financeiro/?vencimento_de={ontem}&status=vencido", headers=auth_headers)
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["numero"] == "000001"


def test_filtro_status_invalido_retorna_422(client, auth_headers):
    resposta = client.get("/financeiro/?status=quitado", headers=auth_headers)
    assert resposta.status_code == 422


def test_metodos_de_escrita_nao_existem(client, auth_headers):
    assert client.post("/financeiro/", json={}, headers=auth_headers).status_code == 405
    assert client.put("/financeiro/", json={}, headers=auth_headers).status_code == 405
    assert client.delete("/financeiro/", headers=auth_headers).status_code == 405
