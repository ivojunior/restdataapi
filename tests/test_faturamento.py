from datetime import date, timedelta
from decimal import Decimal

from app.models.item_faturamento import ItemFaturamento
from app.models.produto import Produto


def _produto(**overrides):
    dados = dict(
        deletado=" ",
        filial="  ",
        codigo="PROD1",
        descricao="Produto Exemplo",
        tipo="PA",
        conversao=Decimal("1.0000"),
    )
    dados.update(overrides)
    return Produto(**dados)


def _item(**overrides):
    dados = dict(
        deletado=" ",
        filial="01",
        emissao="20260805",
        codigo_produto="PROD1",
        operacao="501",
        quantidade=Decimal("10.0000"),
        total=Decimal("1000.00"),
        custo=Decimal("600.00"),
    )
    dados.update(overrides)
    return ItemFaturamento(**dados)


def test_requer_api_key(client):
    assert client.get("/faturamento/").status_code == 401


def test_agrega_vendas_do_mesmo_dia_produto_e_filial(client, auth_headers, db_session):
    db_session.add_all([
        _produto(),
        _item(quantidade=Decimal("10.0000"), total=Decimal("1000.00"), custo=Decimal("600.00")),
        _item(quantidade=Decimal("5.0000"), total=Decimal("500.00"), custo=Decimal("300.00")),
    ])
    db_session.commit()

    resposta = client.get("/faturamento/?data_inicial=20260101", headers=auth_headers)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert len(dados["items"]) == 1
    item = dados["items"][0]
    assert item["filial"] == "01"
    assert item["dia"] == 5
    assert item["codigo"] == "PROD1"
    assert item["descricao"] == "Produto Exemplo"
    assert item["quantidade"] == "15.0000"
    assert item["faturamento"] == "1500.00"
    assert item["lucro_bruto"] == "600.00"
    assert item["margem"] == "40.00"


def test_bonificacao_zera_faturamento_e_conta_como_prejuizo_no_lucro(client, auth_headers, db_session):
    # select_faturamento.sql zera FATURAMENTO para bonificação (542/543/544)
    # — dar um produto de bonificação não gera receita — mas QTDE conta
    # normalmente (sem CASE). LUCRO_BRUTO e PRECO_MEDIO são calculados a
    # partir do FATURAMENTO já zerado (não mais do D2_TOTAL bruto — correção
    # do usuário na consulta), então a bonificação contribui só com o custo
    # (prejuízo), sem nenhuma "receita" contrapondo.
    db_session.add_all([
        _produto(),
        _item(operacao="501", quantidade=Decimal("10.0000"),
              total=Decimal("1000.00"), custo=Decimal("600.00")),
        _item(operacao="542", quantidade=Decimal("2.0000"),
              total=Decimal("200.00"), custo=Decimal("120.00")),
    ])
    db_session.commit()

    resposta = client.get("/faturamento/?data_inicial=20260101", headers=auth_headers)
    item = resposta.json()["items"][0]
    assert item["quantidade"] == "12.0000"
    assert item["faturamento"] == "1000.00"
    # lucro_bruto = SUM(faturamento) - SUM(custo) = 1000 - (600+120) = 280
    assert item["lucro_bruto"] == "280.00"
    assert item["margem"] == "28.00"
    # preco_medio = AVG(faturamento/qtde por linha) = AVG(1000/10, 0/2) = AVG(100, 0) = 50
    assert item["preco_medio"] == "50.0"


def test_quantidade_dividida_pela_conversao_do_produto(client, auth_headers, db_session):
    db_session.add_all([
        _produto(conversao=Decimal("2.0000")),
        _item(quantidade=Decimal("10.0000")),
    ])
    db_session.commit()

    resposta = client.get("/faturamento/?data_inicial=20260101", headers=auth_headers)
    assert resposta.json()["items"][0]["quantidade"] == "5.0000"


def test_produto_tipo_diferente_de_pa_e_ignorado(client, auth_headers, db_session):
    db_session.add_all([_produto(tipo="AM"), _item()])
    db_session.commit()

    resposta = client.get("/faturamento/?data_inicial=20260101", headers=auth_headers)
    assert len(resposta.json()["items"]) == 0


def test_operacao_fora_da_lista_e_ignorada(client, auth_headers, db_session):
    db_session.add_all([_produto(), _item(operacao="999")])
    db_session.commit()

    resposta = client.get("/faturamento/?data_inicial=20260101", headers=auth_headers)
    assert len(resposta.json()["items"]) == 0


def test_item_sem_produto_correspondente_e_ignorado(client, auth_headers, db_session):
    db_session.add(_item())
    db_session.commit()

    resposta = client.get("/faturamento/?data_inicial=20260101", headers=auth_headers)
    assert len(resposta.json()["items"]) == 0


def test_registros_deletados_sao_ignorados(client, auth_headers, db_session):
    db_session.add_all([
        _produto(),
        _item(total=Decimal("1000.00")),
        _item(total=Decimal("5000.00"), deletado="*"),
    ])
    db_session.commit()

    resposta = client.get("/faturamento/?data_inicial=20260101", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["faturamento"] == "1000.00"


def test_dias_de_meses_diferentes_com_mesmo_numero_sao_somados(client, auth_headers, db_session):
    # DAY(D2_EMISSAO) só considera o dia do mês — dois meses diferentes com
    # o mesmo número de dia (05/01 e 05/02) caem no mesmo grupo. Réplica
    # fiel de select_faturamento.sql, mesmo sendo um comportamento pouco
    # intuitivo à primeira vista.
    db_session.add_all([
        _produto(),
        _item(emissao="20260105", total=Decimal("1000.00")),
        _item(emissao="20260205", total=Decimal("2000.00")),
    ])
    db_session.commit()

    resposta = client.get(
        "/faturamento/?data_inicial=20260101&data_final=20260228", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["dia"] == 5
    assert dados["items"][0]["faturamento"] == "3000.00"


def test_filtro_data_final_via_query_string(client, auth_headers, db_session):
    db_session.add_all([
        _produto(),
        _item(emissao="20260805", total=Decimal("1000.00")),
        _item(emissao="20260815", total=Decimal("2000.00")),
    ])
    db_session.commit()

    resposta = client.get(
        "/faturamento/?data_inicial=20260801&data_final=20260810", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["dia"] == 5


def test_sem_filtro_assume_data_atual(client, auth_headers, db_session):
    hoje = date.today().strftime("%Y%m%d")
    ontem = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
    db_session.add_all([
        _produto(),
        _item(emissao=ontem, total=Decimal("1000.00")),
        _item(emissao=hoje, total=Decimal("2000.00")),
    ])
    db_session.commit()

    resposta = client.get("/faturamento/", headers=auth_headers)
    dados = resposta.json()
    assert len(dados["items"]) == 1
    assert dados["items"][0]["faturamento"] == "2000.00"


def test_metodos_de_escrita_nao_existem(client, auth_headers):
    assert client.post("/faturamento/", json={}, headers=auth_headers).status_code == 405
    assert client.put("/faturamento/", json={}, headers=auth_headers).status_code == 405
    assert client.delete("/faturamento/", headers=auth_headers).status_code == 405
