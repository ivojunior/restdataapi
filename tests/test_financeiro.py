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
        vencimento="20260401",
        vencimento_real="20260401",
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


def test_vencimento_real_anterior_ao_minimo_e_ignorado(client, auth_headers, db_session):
    db_session.add_all(
        [
            _fornecedor(),
            _titulo(numero="000001", vencimento_real="20260228"),
        ]
    )
    db_session.commit()

    resposta = client.get("/financeiro/", headers=auth_headers)
    assert resposta.json()["total"] == 0


def test_metodos_de_escrita_nao_existem(client, auth_headers):
    assert client.post("/financeiro/", json={}, headers=auth_headers).status_code == 405
    assert client.put("/financeiro/", json={}, headers=auth_headers).status_code == 405
    assert client.delete("/financeiro/", headers=auth_headers).status_code == 405
