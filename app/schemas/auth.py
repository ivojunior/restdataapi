from pydantic import BaseModel


class GoogleLoginRequest(BaseModel):
    credential: str  # ID token JWT emitido pelo Google Identity Services


class UsuarioLogado(BaseModel):
    email: str
    nome: str
