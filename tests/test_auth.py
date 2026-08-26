def test_login_google_dominio_permitido_seta_cookie_e_me_funciona(client, mock_google_id_token):
    mock_google_id_token(email="fulano@empresa-teste.com.br", nome="Fulano de Tal")

    resposta = client.post("/auth/google", json={"credential": "token-fake"})
    assert resposta.status_code == 200
    assert resposta.json() == {"email": "fulano@empresa-teste.com.br", "nome": "Fulano de Tal"}
    assert "rda_session" in resposta.cookies

    resposta_me = client.get("/auth/me")
    assert resposta_me.status_code == 200
    assert resposta_me.json()["email"] == "fulano@empresa-teste.com.br"


def test_login_google_dominio_nao_permitido_retorna_401_sem_cookie(client, mock_google_id_token):
    # empresa-teste.com.br é o único domínio permitido nos testes (ver conftest.py)
    mock_google_id_token(email="fulano@outraempresa.com")

    resposta = client.post("/auth/google", json={"credential": "token-fake"})
    assert resposta.status_code == 401
    assert "rda_session" not in resposta.cookies


def test_login_google_token_invalido_retorna_401(client, mock_google_id_token):
    mock_google_id_token(erro=True)

    resposta = client.post("/auth/google", json={"credential": "token-invalido"})
    assert resposta.status_code == 401
    assert "rda_session" not in resposta.cookies


def test_me_sem_cookie_retorna_401(client):
    assert client.get("/auth/me").status_code == 401


def test_logout_limpa_cookie(client, mock_google_id_token):
    mock_google_id_token()
    client.post("/auth/google", json={"credential": "token-fake"})
    assert client.get("/auth/me").status_code == 200

    resposta_logout = client.post("/auth/logout")
    assert resposta_logout.status_code == 200

    assert client.get("/auth/me").status_code == 401


def test_endpoint_de_dados_aceita_sessao_sem_api_key(client, mock_google_id_token):
    # Prova que a SPA funciona autenticada só por cookie, sem X-API-Key —
    # regressão coberta em separado (ver test_*.py de cada router, que
    # seguem usando a fixture auth_headers com X-API-Key sem nenhuma
    # alteração).
    mock_google_id_token()
    client.post("/auth/google", json={"credential": "token-fake"})

    resposta = client.get("/faturamento/")
    assert resposta.status_code == 200


def test_endpoint_de_dados_sem_api_key_e_sem_sessao_retorna_401(client):
    assert client.get("/faturamento/").status_code == 401
