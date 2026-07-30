from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    OAuth2PasswordRequestForm,
    OAuth2PasswordBearer
)

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from jose import JWTError, jwt

from pydantic import BaseModel

from datetime import datetime, timedelta
import unicodedata

import models
import schemas
import auth

from database import (
    get_db,
    engine,
    SessionLocal
)


# =====================================================
# CRIAÇÃO DAS TABELAS E DADOS INICIAIS
# =====================================================

models.Base.metadata.create_all(
    bind=engine
)


def criar_admin_inicial():
    """
    Verifica se o usuário administrador padrão existe.
    Caso não exista, cria automaticamente utilizando os campos
    exatos do models.Usuario, com tratamento de erros para deploy.
    """
    db = SessionLocal()
    try:
        # Verifica se o admin já existe pelo username
        admin_existente = (
            db.query(models.Usuario)
            .filter(models.Usuario.username == "admin@duarte.com")
            .first()
        )

        if not admin_existente:
            # Nunca salva a senha em texto puro, utiliza o bcrypt do auth.py
            senha_criptografada = auth.obter_hash_senha("123456")
            
            novo_admin = models.Usuario(
                username="admin@duarte.com",
                email="admin@duarte.com",
                nome="Administrador",
                password_hash=senha_criptografada,
                role="Admin",
                perfil_completo=True
            )
            
            db.add(novo_admin)
            db.commit()
            print("✅ Usuário administrador criado com sucesso no banco de dados.")
            
    except IntegrityError:
        # Evita erro fatal se múltiplos workers da Railway tentarem criar o admin ao mesmo tempo
        db.rollback()
        print("⚠️ Usuário admin já foi registrado por outro processo (IntegrityError evitado).")
    except Exception as e:
        # Garante que qualquer outro erro não trave o banco (database is locked)
        db.rollback()
        print(f"❌ Erro ao criar usuário administrador inicial: {e}")
    finally:
        # Garante que a sessão será fechada corretamente, liberando o banco
        db.close()


# =====================================================
# CONFIGURAÇÃO API
# =====================================================

app = FastAPI(
    title="Duarte Performance API",
    description="Gestão Operacional Duarte Gestão",
    version="2.6"
)

# Aciona a função de criação do admin na inicialização da API
@app.on_event("startup")
def startup_event():
    criar_admin_inicial()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# =====================================================
# JWT & AUTENTICAÇÃO
# =====================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token"
)

def usuario_logado(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            auth.SECRET_KEY,
            algorithms=[auth.ALGORITHM]
        )
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=401,
                detail="Token inválido"
            )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token expirado ou inválido"
        )

    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == username)
        .first()
    )

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )
    return usuario



# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/")
def home():
    return {
        "status":"online",
        "sistema":"Duarte Performance API",
        "versao":"2.6"
    }


# =====================================================
# ROTA DE RESGATE DO ADMIN (SETUP RÁPIDO)
# =====================================================

@app.get("/setup-admin")
def setup_admin_manual(db: Session = Depends(get_db)):
    """Acesse essa URL no navegador para criar/resetar o admin instantaneamente."""
    admin = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == "admin@duarte.com")
        .first()
    )

    senha_hash = auth.obter_hash_senha("123456")

    if not admin:
        admin = models.Usuario(
            username="admin@duarte.com",
            email="admin@duarte.com",
            nome="Administrador",
            password_hash=senha_hash,
            role="Admin",
            perfil_completo=True,
        )
        db.add(admin)
        db.commit()
        return {
            "status": "sucesso",
            "mensagem": "✅ Usuário admin@duarte.com criado do zero com a senha 123456!"
        }
    else:
        admin.password_hash = senha_hash
        db.commit()
        return {
            "status": "sucesso",
            "mensagem": "✅ Senha do usuário admin@duarte.com redefinida para 123456!"
        }


# =====================================================
# LOGIN
# =====================================================

@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == form_data.username)
        .first()
    )

    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha inválidos"
        )

    if not auth.verificar_senha(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha inválidos"
        )

    token = auth.criar_token_acesso(
        {
            "sub": usuario.username,
            "nome": usuario.nome,
            "role": usuario.role,
            "id": usuario.id
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": usuario.username,
        "nome": usuario.nome,
        "role": usuario.role
    }


# =====================================================
# GESTÃO DE USUÁRIOS (CADASTRO)
# =====================================================

@app.post("/usuarios/", status_code=201)
def criar_usuario(
    dados: schemas.UsuarioCreate, 
    db: Session = Depends(get_db)
):
    """
    Cria um novo usuário no sistema garantindo hash da senha
    e checagem de duplicidade.
    """
    
    usuario_existente = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == dados.username)
        .first()
    )

    if usuario_existente:
        raise HTTPException(
            status_code=400, 
            detail="Este nome de usuário/e-mail já existe."
        )

    senha_hash = auth.obter_hash_senha(dados.senha)

    novo_usuario = models.Usuario(
        username=dados.username,
        email=dados.email if hasattr(dados, "email") and dados.email else dados.username,
        nome=dados.nome,
        password_hash=senha_hash,
        role=dados.role if hasattr(dados, "role") and dados.role else "Operador",
        perfil_completo=True,
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {
        "status": "sucesso",
        "mensagem": f"Usuário {novo_usuario.nome} criado com sucesso!",
        "id": novo_usuario.id,
    }


# =====================================================
# GESTÃO DE PERMISSÕES / FUNÇÕES (ROLES)
# =====================================================

ROLES_VALIDAS = ["Operador", "Visualizador", "Gestor", "Admin"]


class RoleUpdate(BaseModel):
    role: str


def exigir_admin_ou_gestor(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
    """Libera o acesso apenas para Admin ou Gestor."""
    if usuario.role not in ("Admin", "Gestor"):
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito a usuários Admin ou Gestor.",
        )
    return usuario


def exigir_admin(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
    """Libera o acesso apenas para Admin."""
    if usuario.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito ao perfil Admin.",
        )
    return usuario


@app.get("/usuarios/todos")
def listar_todos_usuarios(
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin_ou_gestor),
):
    """Retorna id, nome, username, email e role de todos os usuários."""
    usuarios = db.query(models.Usuario).order_by(models.Usuario.nome).all()
    return [
        {
            "id": u.id,
            "nome": u.nome,
            "username": u.username,
            "email": u.email,
            "role": u.role,
        }
        for u in usuarios
    ]


@app.put("/usuarios/{usuario_id}/role")
def atualizar_role_usuario(
    usuario_id: int,
    dados: RoleUpdate,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin),
):
    """Atualiza a função (role) de um usuário. Somente Admin pode chamar."""
    if dados.role not in ROLES_VALIDAS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Função inválida. Use uma das opções: "
                + ", ".join(ROLES_VALIDAS)
            ),
        )

    usuario_alvo = (
        db.query(models.Usuario)
        .filter(models.Usuario.id == usuario_id)
        .first()
    )

    if not usuario_alvo:
        raise HTTPException(
            status_code=404, detail="Usuário não encontrado."
        )

    usuario_alvo.role = dados.role
    db.commit()
    db.refresh(usuario_alvo)

    return {
        "status": "sucesso",
        "mensagem": (
            f"Função de {usuario_alvo.nome} atualizada para"
            f" {usuario_alvo.role}."
        ),
        "id": usuario_alvo.id,
        "role": usuario_alvo.role,
    }


# =====================================================
# NOMES DA ESCALA DISPONÍVEIS PARA CRIAR CONTA
# =====================================================
# Rotas públicas (sem login), usadas na tela "Criar Conta":
# 1) lista quem já está na escala mas ainda não tem usuário
# 2) sugere um username no formato nome.sobrenome (ex: karine.martinez),
#    evitando colisão quando duas pessoas tiverem o mesmo primeiro nome.

def _remover_acentos(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _slug_nome(parte: str) -> str:
    parte = _remover_acentos(parte).lower().strip()
    return "".join(c for c in parte if c.isalnum())


def _gerar_username_sugerido(nome_escala: str, sobrenome: str, db: Session) -> str:
    base = f"{_slug_nome(nome_escala)}.{_slug_nome(sobrenome)}"
    candidato = base
    contador = 1
    while (
        db.query(models.Usuario)
        .filter(models.Usuario.username == candidato)
        .first()
    ):
        contador += 1
        candidato = f"{base}{contador}"
    return candidato


@app.get("/nomes-escala-disponiveis")
def listar_nomes_escala_disponiveis(db: Session = Depends(get_db)):
    """Nomes da matriz de escala (cronogramas) que ainda não têm
    usuário vinculado no sistema."""
    nomes_escala = (
        db.query(models.CronogramaModel.operador)
        .distinct()
        .all()
    )
    nomes_escala = sorted({n[0].strip() for n in nomes_escala if n[0]})

    usuarios_existentes = db.query(models.Usuario.nome).all()
    primeiros_nomes_usados = {
        _slug_nome((u[0] or "").split(" ")[0])
        for u in usuarios_existentes
        if u[0]
    }

    disponiveis = [
        nome
        for nome in nomes_escala
        if _slug_nome(nome.split(" ")[0]) not in primeiros_nomes_usados
    ]
    return disponiveis


@app.get("/sugerir-username")
def sugerir_username(
    nome_escala: str,
    sobrenome: str,
    db: Session = Depends(get_db),
):
    if not nome_escala.strip() or not sobrenome.strip():
        raise HTTPException(
            status_code=400,
            detail="Informe o nome da escala e o sobrenome.",
        )
    sugestao = _gerar_username_sugerido(nome_escala, sobrenome, db)
    return {"username_sugerido": sugestao}


# =====================================================
# RECUPERAÇÃO DE SENHA (Admin só autoriza; nunca vê/define senha)
# =====================================================
# Fluxo:
# 1) POST /recuperar-senha         -> usuário solicita (fica "pendente")
# 2) GET  /admin/solicitacoes-senha -> Admin lista pendentes
# 3) POST /admin/.../autorizar      -> Admin libera (janela de 10 min)
# 4) POST /admin/.../rejeitar       -> Admin recusa
# 5) POST /redefinir-senha-autorizada -> usuário define a própria senha
#    dentro da janela liberada

JANELA_REDEFINICAO_MINUTOS = 10


def _expirar_solicitacoes_vencidas(db: Session):
    agora = datetime.utcnow()
    vencidas = (
        db.query(models.SolicitacaoSenhaModel)
        .filter(
            models.SolicitacaoSenhaModel.status == "autorizado",
            models.SolicitacaoSenhaModel.expira_em < agora,
        )
        .all()
    )
    for s in vencidas:
        s.status = "expirado"
    if vencidas:
        db.commit()


@app.post("/recuperar-senha")
def solicitar_recuperacao_senha(
    dados: schemas.SolicitacaoSenhaCreate,
    db: Session = Depends(get_db),
):
    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == dados.username.strip())
        .first()
    )

    if not usuario:
        raise HTTPException(
            status_code=404, detail="Usuário não encontrado."
        )

    # Confere e-mail/telefone quando o cadastro já tiver esses dados
    # preenchidos (evita liberar recuperação pra qualquer um).
    if (
        usuario.email
        and dados.email
        and usuario.email.strip().lower() != dados.email.strip().lower()
    ):
        raise HTTPException(
            status_code=400,
            detail="Os dados informados não conferem com o cadastro.",
        )

    if (
        usuario.telefone
        and dados.telefone
        and usuario.telefone.strip() != dados.telefone.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail="Os dados informados não conferem com o cadastro.",
        )

    _expirar_solicitacoes_vencidas(db)

    solicitacao_ativa = (
        db.query(models.SolicitacaoSenhaModel)
        .filter(
            models.SolicitacaoSenhaModel.username == usuario.username,
            models.SolicitacaoSenhaModel.status.in_(
                ["pendente", "autorizado"]
            ),
        )
        .order_by(models.SolicitacaoSenhaModel.solicitado_em.desc())
        .first()
    )

    if solicitacao_ativa:
        return {
            "status": "sucesso",
            "mensagem": (
                "Já existe uma solicitação em andamento para este usuário."
            ),
            "solicitacao_status": solicitacao_ativa.status,
        }

    nova = models.SolicitacaoSenhaModel(
        username=usuario.username,
        email=dados.email,
        telefone=dados.telefone,
        status="pendente",
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)

    return {
        "status": "sucesso",
        "mensagem": (
            "Solicitação registrada. Aguarde a autorização do administrador."
        ),
        "id": nova.id,
    }


@app.get("/admin/solicitacoes-senha")
def listar_solicitacoes_senha(
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin),
):
    _expirar_solicitacoes_vencidas(db)
    solicitacoes = (
        db.query(models.SolicitacaoSenhaModel)
        .order_by(models.SolicitacaoSenhaModel.solicitado_em.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "username": s.username,
            "email": s.email,
            "telefone": s.telefone,
            "status": s.status,
            "solicitado_em": s.solicitado_em,
            "autorizado_em": s.autorizado_em,
            "expira_em": s.expira_em,
            "autorizado_por": s.autorizado_por,
        }
        for s in solicitacoes
    ]


@app.post("/admin/solicitacoes-senha/{solicitacao_id}/autorizar")
def autorizar_solicitacao_senha(
    solicitacao_id: int,
    db: Session = Depends(get_db),
    admin: models.Usuario = Depends(exigir_admin),
):
    solicitacao = (
        db.query(models.SolicitacaoSenhaModel)
        .filter(models.SolicitacaoSenhaModel.id == solicitacao_id)
        .first()
    )
    if not solicitacao:
        raise HTTPException(
            status_code=404, detail="Solicitação não encontrada."
        )

    if solicitacao.status != "pendente":
        raise HTTPException(
            status_code=400,
            detail=f"Solicitação já está em status '{solicitacao.status}'.",
        )

    agora = datetime.utcnow()
    solicitacao.status = "autorizado"
    solicitacao.autorizado_em = agora
    solicitacao.expira_em = agora + timedelta(
        minutes=JANELA_REDEFINICAO_MINUTOS
    )
    solicitacao.autorizado_por = admin.username

    db.commit()

    return {
        "status": "sucesso",
        "mensagem": (
            f"Solicitação autorizada. O usuário tem"
            f" {JANELA_REDEFINICAO_MINUTOS} minutos para definir a nova"
            " senha."
        ),
        "expira_em": solicitacao.expira_em,
    }


@app.post("/admin/solicitacoes-senha/{solicitacao_id}/rejeitar")
def rejeitar_solicitacao_senha(
    solicitacao_id: int,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin),
):
    solicitacao = (
        db.query(models.SolicitacaoSenhaModel)
        .filter(models.SolicitacaoSenhaModel.id == solicitacao_id)
        .first()
    )
    if not solicitacao:
        raise HTTPException(
            status_code=404, detail="Solicitação não encontrada."
        )

    solicitacao.status = "rejeitado"
    db.commit()

    return {"status": "sucesso", "mensagem": "Solicitação rejeitada."}


@app.post("/redefinir-senha-autorizada")
def redefinir_senha_autorizada(
    dados: schemas.RedefinirSenhaAutorizada,
    db: Session = Depends(get_db),
):
    _expirar_solicitacoes_vencidas(db)

    solicitacao = (
        db.query(models.SolicitacaoSenhaModel)
        .filter(
            models.SolicitacaoSenhaModel.username == dados.username.strip(),
            models.SolicitacaoSenhaModel.status == "autorizado",
        )
        .order_by(models.SolicitacaoSenhaModel.autorizado_em.desc())
        .first()
    )

    if not solicitacao:
        raise HTTPException(
            status_code=400,
            detail=(
                "Não há autorização válida para este usuário."
                " Solicite a recuperação novamente."
            ),
        )

    if solicitacao.expira_em and datetime.utcnow() > solicitacao.expira_em:
        solicitacao.status = "expirado"
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=(
                f"O prazo de {JANELA_REDEFINICAO_MINUTOS} minutos para"
                " redefinir a senha expirou. Solicite novamente."
            ),
        )

    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == dados.username.strip())
        .first()
    )
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    usuario.password_hash = auth.obter_hash_senha(dados.nova_senha)
    solicitacao.status = "usado"
    solicitacao.usado_em = datetime.utcnow()

    db.commit()

    return {
        "status": "sucesso",
        "mensagem": (
            "Senha redefinida com sucesso! Você já pode entrar com a nova"
            " senha."
        ),
    }


# =====================================================
# PERFIL DO USUÁRIO
# =====================================================

@app.get("/usuarios/me")
def meu_usuario(usuario: models.Usuario = Depends(usuario_logado)):
    return {
        "id": usuario.id,
        "username": usuario.username,
        "nome": usuario.nome,
        "email": usuario.email,
        "role": usuario.role,
        "perfil_completo": usuario.perfil_completo
    }


# =====================================================
# REGISTROS OPERACIONAIS
# =====================================================

@app.post("/registros/", response_model=schemas.RegistroOut)
def criar_registro(
    registro: schemas.RegistroCreate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado)
):
    novo = models.RegistroModel(
        operador_nome=usuario.nome,
        cliente_nome=registro.cliente_nome,
        status=registro.status,
        justificativa=registro.justificativa
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@app.get("/registros/", response_model=list[schemas.RegistroOut])
def listar_registros(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado)
):
    registros = (
        db.query(models.RegistroModel)
        .order_by(models.RegistroModel.data_registro.desc())
        .all()
    )
    return registros


@app.put("/registros/{registro_id}")
def atualizar_registro(
    registro_id: int,
    dados: schemas.RegistroUpdate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado)
):
    registro = (
        db.query(models.RegistroModel)
        .filter(models.RegistroModel.id == registro_id)
        .first()
    )

    if not registro:
        raise HTTPException(404, "Registro não encontrado")

    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(registro, campo, valor)

    db.commit()
    return {"status": "Atualizado"}


@app.delete("/registros/{registro_id}")
def deletar_registro(
    registro_id: int,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado)
):
    registro = (
        db.query(models.RegistroModel)
        .filter(models.RegistroModel.id == registro_id)
        .first()
    )

    if not registro:
        raise HTTPException(404, "Registro não encontrado")

    db.delete(registro)
    db.commit()
    return {"status": "Excluído"}


# =====================================================
# CRONOGRAMA
# =====================================================

@app.get("/cronograma/")
def listar_cronograma(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado)
):
    dados = db.query(models.CronogramaModel).all()
    return dados