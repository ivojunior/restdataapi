from fastapi import APIRouter, HTTPException, Request, Response, status

from app.auth_google import domain_permitido, verify_google_id_token
from app.config import settings
from app.rate_limit import limiter
from app.schemas.auth import GoogleLoginRequest, UsuarioLogado
from app.session import criar_sessao_jwt, verificar_sessao_jwt

router = APIRouter(prefix="/auth", tags=["Auth"])

# Sem `dependencies=[Depends(verify_api_key_or_session)]` aqui — este router
# é o próprio mecanismo de login, não pode exigir estar logado para logar.


def _set_session_cookie(response: Response, email: str, nome: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=criar_sessao_jwt(email, nome),
        max_age=settings.session_ttl_minutes * 60,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/google", response_model=UsuarioLogado)
@limiter.limit("10/minute")
def login_google(request: Request, body: GoogleLoginRequest, response: Response):
    """Recebe o ID token do Google Identity Services (obtido no frontend),
    valida no backend (assinatura/aud/exp — nunca confia no client-side) e,
    se o domínio do e-mail estiver na allowlist, emite a sessão da aplicação
    via cookie httpOnly."""
    try:
        usuario_google = verify_google_id_token(body.credential)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token do Google inválido",
        )

    if not domain_permitido(usuario_google.email):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Domínio de e-mail não autorizado",
        )

    _set_session_cookie(response, usuario_google.email, usuario_google.nome)
    return UsuarioLogado(email=usuario_google.email, nome=usuario_google.nome)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=settings.session_cookie_name, path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UsuarioLogado)
def me(request: Request):
    cookie = request.cookies.get(settings.session_cookie_name)
    if not cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    try:
        sessao = verificar_sessao_jwt(cookie)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida ou expirada")
    return UsuarioLogado(email=sessao.email, nome=sessao.nome)
