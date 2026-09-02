from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Query,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    OAuth2PasswordBearer,
)
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import text
import traceback

from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta, date, time
from zoneinfo import ZoneInfo
from typing import Optional, List
import unicodedata

from apscheduler.schedulers.background import BackgroundScheduler

import models
import schemas
import auth
from automacao import rodar_preenchimento_nao_informado

from database import (
    get_db,
    engine,
    SessionLocal,
)

models.Base.metadata.create_all(bind=engine)

scheduler = BackgroundScheduler()

def job_preenchimento_nao_informado_diario():
    """Roda diariamente às 00:10 BRT verificando as pendências do dia anterior (ontem)."""
    tz_br = ZoneInfo("America/Sao_Paulo")
    ontem = (datetime.now(tz_br) - timedelta(days=1)).date()
    print(f"⏰ Executando automação 'Não Informado' para o dia anterior: {ontem}")
    try:
        resultado = rodar_preenchimento_nao_informado(ontem)
        print(f"✅ Automação concluída: {resultado}")
    except Exception as e:
        print(f"❌ Erro na automação 'Não Informado': {e}")

def _garantir_autoincremento_users():
    """
    Corrige a causa raiz mais comum quando o ORM passa a apontar para uma
    tabela Postgres que já existia em produção (criada fora do SQLAlchemy):
    a coluna `id` sem DEFAULT/sequence associada.

    Sem isso, todo INSERT na tabela `users` falha com
    'null value in column "id" violates not-null constraint', porque o
    SQLAlchemy não envia valor de id (espera que o banco gere sozinho).

    Idempotente: seguro rodar em todo startup, em qualquer ambiente.
    Se o banco não for Postgres (ex.: SQLite local), falha silenciosamente
    e não afeta o funcionamento normal.
    """
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE c.relname = 'users_id_seq'
                    ) THEN
                        CREATE SEQUENCE users_id_seq;
                    END IF;

                    PERFORM setval(
                        'users_id_seq',
                        COALESCE((SELECT MAX(id) FROM users), 0) + 1,
                        false
                    );

                    ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq');
                    ALTER SEQUENCE users_id_seq OWNED BY users.id;
                END $$;
            """))
        print("✅ Sequence/DEFAULT da coluna id (users) verificada/corrigida.")
    except Exception as e:
        # Não é Postgres, ou usuário do banco sem permissão de ALTER TABLE.
        # Não derruba a API por causa disso — só avisa no log.
        print(f"⚠️ Não foi possível garantir autoincremento em users.id: {e}")


def criar_admin_inicial():
    db = SessionLocal()
    try:
        admin_existente = (
            db.query(models.Usuario)
            .filter(models.Usuario.username == "admin@duarte.com")
            .first()
        )
        if not admin_existente:
            senha_criptografada = auth.obter_hash_senha("123456")
            novo_admin = models.Usuario(
                username="admin@duarte.com",
                password_hash=senha_criptografada,
                role="Admin",
            )
            db.add(novo_admin)
            db.commit()
            print("✅ Admin criado.")
        else:
            print("ℹ️ Admin já existe — nenhuma ação necessária no startup.")
    except IntegrityError as e:
        db.rollback()
        # Antes este erro sumia em silêncio. Agora fica visível no log,
        # com a causa real (ex.: violação de NOT NULL, unique, etc.).
        print(f"❌ IntegrityError ao criar admin inicial: {e}")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro admin inicial: {e}")
        traceback.print_exc()
    finally:
        db.close()

app = FastAPI(
    title="Duarte Performance API",
    description="Gestão Operacional Duarte Gestão",
    version="2.9.3",
)

@app.on_event("startup")
def startup_event():
    _garantir_autoincremento_users()
    criar_admin_inicial()
    scheduler.add_job(
        job_preenchimento_nao_informado_diario,
        "cron",
        hour=0,
        minute=10,
        timezone="America/Sao_Paulo",
        id="job_nao_informado",
        replace_existing=True,
    )
    scheduler.start()
    print("⏰ Agendador de tarefas iniciado (00:10 BRT diariamente para dia anterior).")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def usuario_logado(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(
            token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM]
        )
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(
            status_code=401, detail="Token expirado ou inválido"
        )

    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == username)
        .first()
    )
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

ROLES_GESTAO = ("Admin", "Gestor", "Admin Master", "Coordenador")
ROLES_VALIDAS = ["Operador", "Visualizador", "Gestor", "Admin"]

def _eh_gestao(role: str) -> bool:
    r = (role or "").strip()
    if r in ROLES_GESTAO:
        return True
    return r.lower() in {"admin", "admin master", "gestor", "coordenador"}

def exigir_admin_ou_gestor(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
    if not _eh_gestao(usuario.role):
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito a Admin ou Gestor.",
        )
    return usuario

def exigir_admin(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
    if usuario.role not in ("Admin", "Admin Master") and (
        usuario.role or ""
    ).lower() not in ("admin", "admin master"):
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito ao perfil Admin.",
        )
    return usuario

@app.get("/")
def home():
    return {
        "status": "online",
        "sistema": "Duarte Performance API",
        "versao": "2.9.3",
    }

@app.get("/setup-admin")
def setup_admin_manual(db: Session = Depends(get_db)):
    try:
        admin = (
            db.query(models.Usuario)
            .filter(models.Usuario.username == "admin@duarte.com")
            .first()
        )
        senha_hash = auth.obter_hash_senha("123456")

        if not admin:
            admin = models.Usuario(
                username="admin@duarte.com",
                password_hash=senha_hash,
                role="Admin",
            )
            db.add(admin)
            db.commit()
            return {"status": "sucesso", "mensagem": "Admin criado. Senha: 123456"}

        admin.password_hash = senha_hash
        db.commit()
        return {"status": "sucesso", "mensagem": "Senha admin resetada para 123456"}

    except SQLAlchemyError as e:
        db.rollback()
        traceback.print_exc()
        # Expõe o erro real do banco em vez de um 500 mudo, para diagnóstico rápido.
        raise HTTPException(
            status_code=500,
            detail=f"Erro de banco de dados ao configurar admin: {str(e.__cause__ or e)}",
        )
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado ao configurar admin: {str(e)}",
        )

@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == form_data.username)
        .first()
    )
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    if not auth.verificar_senha(form_data.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")

    token = auth.criar_token_acesso(
        {
            "sub": usuario.username,
            "nome": usuario.username,  # usa username como nome
            "role": usuario.role,
            "id": usuario.id,
        }
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": usuario.username,
        "nome": usuario.username,
        "role": usuario.role,
    }

@app.post("/usuarios/", status_code=201)
def criar_usuario(
    dados: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
):
    if (
        db.query(models.Usuario)
        .filter(models.Usuario.username == dados.username)
        .first()
    ):
        raise HTTPException(
            status_code=400, detail="Este nome de usuário/e-mail já existe."
        )

    senha_hash = auth.obter_hash_senha(dados.senha)
    novo = models.Usuario(
        username=dados.username,
        password_hash=senha_hash,
        role=getattr(dados, "role", None) or "Operador",
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {
        "status": "sucesso",
        "mensagem": f"Usuário {novo.username} criado com sucesso!",
        "id": novo.id,
    }

class RoleUpdate(BaseModel):
    role: str

@app.get("/usuarios/todos")
def listar_todos_usuarios(
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin_ou_gestor),
):
    usuarios = db.query(models.Usuario).order_by(models.Usuario.username).all()
    return [
        {
            "id": u.id,
            "nome": u.username,
            "username": u.username,
            "email": None,
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
    if dados.role not in ROLES_VALIDAS:
        raise HTTPException(
            status_code=400,
            detail="Função inválida: " + ", ".join(ROLES_VALIDAS),
        )
    u = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    u.role = dados.role
    db.commit()
    db.refresh(u)
    return {
        "status": "sucesso",
        "mensagem": f"Função de {u.username} atualizada para {u.role}.",
        "id": u.id,
        "role": u.role,
    }

@app.get("/usuarios/me")
def meu_usuario(usuario: models.Usuario = Depends(usuario_logado)):
    return {
        "id": usuario.id,
        "username": usuario.username,
        "nome": usuario.username,
        "email": None,
        "role": usuario.role,
        "perfil_completo": True,
    }

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
    n = 1
    while db.query(models.Usuario).filter(models.Usuario.username == candidato).first():
        n += 1
        candidato = f"{base}{n}"
    return candidato

@app.get("/nomes-escala-disponiveis")
def listar_nomes_escala_disponiveis(db: Session = Depends(get_db)):
    nomes = db.query(models.CronogramaModel.operador).distinct().all()
    nomes = sorted({n[0].strip() for n in nomes if n[0]})
    usados = {
        _slug_nome((u[0] or "").split(" ")[0])
        for u in db.query(models.Usuario.username).all()
        if u[0]
    }
    return [
        n for n in nomes
        if _slug_nome(n.split(" ")[0]) not in usados
    ]

@app.get("/sugerir-username")
def sugerir_username(
    nome_escala: str,
    sobrenome: str,
    db: Session = Depends(get_db),
):
    if not nome_escala.strip() or not sobrenome.strip():
        raise HTTPException(status_code=400, detail="Informe nome e sobrenome.")
    return {
        "username_sugerido": _gerar_username_sugerido(nome_escala, sobrenome, db)
    }


# =====================================================
# SINCRONIZAÇÃO EM LOTE DE OPERADORES (CronogramaModel -> users)
# =====================================================
class SincronizarOperadoresIn(BaseModel):
    # Lista opcional para reforçar/cobrir nomes que ainda não apareceram
    # em nenhuma escala lançada no banco (ex.: operador novo, cronograma
    # de produção desatualizado/vazio).
    nomes_extra: Optional[List[str]] = None
    senha_padrao: Optional[str] = "123456"


def _gerar_username_completo(nome_completo: str, db: Session) -> str:
    """Gera um username no formato primeironome.ultimonome (sem acento,
    minúsculo). Se colidir com um já existente, sufixa com número (2, 3...).
    Reutiliza a mesma lógica de _slug_nome já usada em /sugerir-username,
    para manter os dois fluxos (manual e em lote) consistentes."""
    partes = [p for p in nome_completo.strip().split() if p]
    if not partes:
        raise ValueError("Nome vazio.")

    primeiro = _slug_nome(partes[0])
    ultimo = _slug_nome(partes[-1]) if len(partes) > 1 else ""
    base = f"{primeiro}.{ultimo}" if ultimo else primeiro

    candidato = base
    n = 1
    while db.query(models.Usuario).filter(models.Usuario.username == candidato).first():
        n += 1
        candidato = f"{base}{n}"
    return candidato


@app.post("/admin/sincronizar-operadores")
def sincronizar_operadores(
    payload: SincronizarOperadoresIn = SincronizarOperadoresIn(),
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(exigir_admin),
):
    """
    Cria automaticamente uma conta de acesso (role=Operador, senha padrão
    123456) para cada nome de operador que ainda não tem usuário em `users`.

    Fontes de nomes (somadas, sem duplicar):
      1. Todos os valores distintos de CronogramaModel.operador já no banco.
      2. `nomes_extra` enviado no corpo da requisição — cobre operadores que
         ainda não apareceram em nenhuma escala lançada.

    Idempotente: rodar de novo não duplica ninguém. A checagem de "já existe"
    é feita pelo PRIMEIRO NOME normalizado (sem acento/maiúscula), tanto
    comparando com o username completo quanto com o primeiro token antes do
    ponto — assim, um operador cadastrado manualmente como "larissa" ou como
    "larissa.adriene" é reconhecido do mesmo jeito e não gera duplicata.
    """
    nomes_cronograma = {
        n[0].strip()
        for n in db.query(models.CronogramaModel.operador).distinct().all()
        if n[0] and n[0].strip() and n[0].strip() != "-"
    }
    nomes_extra = {n.strip() for n in (payload.nomes_extra or []) if n and n.strip()}
    todos_nomes = sorted(nomes_cronograma | nomes_extra)

    if not todos_nomes:
        return {
            "quantidade_criados": 0,
            "criados": [],
            "ja_existentes": [],
            "erros": [],
            "aviso": (
                "Nenhum nome encontrado nem no cronograma nem em 'nomes_extra'. "
                "Envie a lista de operadores em 'nomes_extra' no corpo da requisição, "
                "ex.: {\"nomes_extra\": [\"Larissa Adriene\", \"Julia Bono\"]}"
            ),
        }

    usernames_existentes = {
        (u[0] or "").strip() for u in db.query(models.Usuario.username).all() if u[0]
    }
    primeiros_nomes_ja_cadastrados = set()
    for username in usernames_existentes:
        primeiro_token = username.split(".")[0].split("@")[0]
        primeiros_nomes_ja_cadastrados.add(_slug_nome(primeiro_token))

    senha_padrao = payload.senha_padrao or "123456"
    senha_hash = auth.obter_hash_senha(senha_padrao)

    criados: List[dict] = []
    ja_existentes: List[str] = []
    erros: List[dict] = []

    for nome in todos_nomes:
        partes = [p for p in nome.split() if p]
        if not partes:
            continue

        primeiro_nome_slug = _slug_nome(partes[0])
        if primeiro_nome_slug in primeiros_nomes_ja_cadastrados:
            ja_existentes.append(nome)
            continue

        try:
            username = _gerar_username_completo(nome, db)
            novo_usuario = models.Usuario(
                username=username,
                password_hash=senha_hash,
                role="Operador",
            )
            db.add(novo_usuario)
            db.commit()
            criados.append({"nome": nome, "username": username})
            primeiros_nomes_ja_cadastrados.add(primeiro_nome_slug)
        except IntegrityError as e:
            db.rollback()
            erros.append({"nome": nome, "erro": str(e.__cause__ or e)})
        except Exception as e:
            db.rollback()
            erros.append({"nome": nome, "erro": str(e)})

    return {
        "quantidade_criados": len(criados),
        "criados": criados,
        "ja_existentes": ja_existentes,
        "erros": erros,
        "senha_padrao_usada": senha_padrao,
    }


# =====================================================
# RESET DE SENHA EM LOTE (para contas já existentes)
# =====================================================
class ResetarSenhaLoteIn(BaseModel):
    usernames: List[str]
    nova_senha: Optional[str] = "12345"


@app.post("/admin/resetar-senha-lote")
def resetar_senha_lote(
    payload: ResetarSenhaLoteIn,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(exigir_admin),
):
    """
    Reseta a senha de uma lista de usernames já existentes em `users`.
    Diferente de /admin/sincronizar-operadores (que só CRIA quem não existe),
    esta rota SOBRESCREVE a senha de contas que já estão cadastradas —
    útil para destravar login em massa sem precisar saber a senha atual.
    """
    nova_senha = payload.nova_senha or "12345"
    senha_hash = auth.obter_hash_senha(nova_senha)

    atualizados: List[str] = []
    nao_encontrados: List[str] = []
    erros: List[dict] = []

    for username_bruto in payload.usernames:
        username = (username_bruto or "").strip()
        if not username:
            continue
        try:
            usuario = (
                db.query(models.Usuario)
                .filter(models.Usuario.username == username)
                .first()
            )
            if not usuario:
                nao_encontrados.append(username)
                continue

            usuario.password_hash = senha_hash
            db.commit()
            atualizados.append(username)
        except Exception as e:
            db.rollback()
            erros.append({"username": username, "erro": str(e)})

    return {
        "quantidade_atualizados": len(atualizados),
        "atualizados": atualizados,
        "nao_encontrados": nao_encontrados,
        "erros": erros,
        "senha_definida": nova_senha,
    }

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
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    _expirar_solicitacoes_vencidas(db)

    ativa = (
        db.query(models.SolicitacaoSenhaModel)
        .filter(
            models.SolicitacaoSenhaModel.username == usuario.username,
            models.SolicitacaoSenhaModel.status.in_(["pendente", "autorizado"]),
        )
        .order_by(models.SolicitacaoSenhaModel.solicitado_em.desc())
        .first()
    )
    if ativa:
        return {
            "status": "sucesso",
            "mensagem": "Já existe solicitação em andamento.",
            "solicitacao_status": ativa.status,
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
        "mensagem": "Solicitação registrada. Aguarde o admin.",
        "id": nova.id,
    }

@app.get("/admin/solicitacoes-senha")
def listar_solicitacoes_senha(
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin),
):
    _expirar_solicitacoes_vencidas(db)
    sols = (
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
        for s in sols
    ]

@app.post("/admin/solicitacoes-senha/{solicitacao_id}/autorizar")
def autorizar_solicitacao_senha(
    solicitacao_id: int,
    db: Session = Depends(get_db),
    admin: models.Usuario = Depends(exigir_admin),
):
    s = (
        db.query(models.SolicitacaoSenhaModel)
        .filter(models.SolicitacaoSenhaModel.id == solicitacao_id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    if s.status != "pendente":
        raise HTTPException(status_code=400, detail=f"Status atual: {s.status}.")
    agora = datetime.utcnow()
    s.status = "autorizado"
    s.autorizado_em = agora
    s.expira_em = agora + timedelta(minutes=JANELA_REDEFINICAO_MINUTOS)
    s.autorizado_por = admin.username
    db.commit()
    return {
        "status": "sucesso",
        "mensagem": f"Autorizado por {JANELA_REDEFINICAO_MINUTOS} min.",
        "expira_em": s.expira_em,
    }

@app.post("/admin/solicitacoes-senha/{solicitacao_id}/rejeitar")
def rejeitar_solicitacao_senha(
    solicitacao_id: int,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin),
):
    s = (
        db.query(models.SolicitacaoSenhaModel)
        .filter(models.SolicitacaoSenhaModel.id == solicitacao_id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    s.status = "rejeitado"
    db.commit()
    return {"status": "sucesso", "mensagem": "Rejeitada."}

@app.post("/redefinir-senha-autorizada")
def redefinir_senha_autorizada(
    dados: schemas.RedefinirSenhaAutorizada,
    db: Session = Depends(get_db),
):
    _expirar_solicitacoes_vencidas(db)
    s = (
        db.query(models.SolicitacaoSenhaModel)
        .filter(
            models.SolicitacaoSenhaModel.username == dados.username.strip(),
            models.SolicitacaoSenhaModel.status == "autorizado",
        )
        .order_by(models.SolicitacaoSenhaModel.autorizado_em.desc())
        .first()
    )
    if not s:
        raise HTTPException(status_code=400, detail="Sem autorização válida.")
    if s.expira_em and datetime.utcnow() > s.expira_em:
        s.status = "expirado"
        db.commit()
        raise HTTPException(status_code=400, detail="Prazo expirado.")

    u = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == dados.username.strip())
        .first()
    )
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    u.password_hash = auth.obter_hash_senha(dados.nova_senha)
    s.status = "usado"
    s.usado_em = datetime.utcnow()
    db.commit()
    return {"status": "sucesso", "mensagem": "Senha redefinida!"}

def _parse_data_registro(valor) -> datetime | None:
    if valor is None:
        return None
    try:
        if isinstance(valor, datetime):
            dt = valor
        elif isinstance(valor, date) and not isinstance(valor, datetime):
            dt = datetime.combine(valor, time(12, 0, 0))
        elif isinstance(valor, str):
            s = valor.strip().replace("Z", "+00:00")
            if len(s) >= 10 and s[4] == "-" and s[7] == "-":
                if len(s) == 10:
                    d = date.fromisoformat(s)
                    dt = datetime.combine(d, time(12, 0, 0))
                else:
                    dt = datetime.fromisoformat(s)
            else:
                dt = datetime.fromisoformat(s)
        else:
            return None

        if getattr(dt, "tzinfo", None) is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception as e:
        print(f"⚠️ Falha data_registro={valor!r}: {e}")
        return None

@app.post("/registros/", response_model=schemas.RegistroOut)
def criar_registro(
    registro: schemas.RegistroCreate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado),
):
    nome_operador = usuario.username or "Operador"
    role = (usuario.role or "").strip()
    gestao = _eh_gestao(role)

    if gestao:
        op = getattr(registro, "operador_nome", None)
        if op and str(op).strip():
            nome_operador = str(op).strip()

    cliente = registro.cliente_nome or getattr(registro, "cliente", None) or ""

    novo = models.RegistroModel(
        operador_nome=nome_operador,
        cliente_nome=str(cliente).strip(),
        status=registro.status,
        justificativa=(registro.justificativa or ""),
    )

    dt = _parse_data_registro(getattr(registro, "data_registro", None))
    if dt is not None:
        novo.data_registro = dt
        print(f"[CREATE] data_registro personalizada={dt} user={usuario.username}")
    else:
        novo.data_registro = datetime.now()
        print(f"[CREATE] data_registro gerada automaticamente={novo.data_registro}")

    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@app.get("/registros/", response_model=list[schemas.RegistroOut])
def listar_registros(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado),
):
    return (
        db.query(models.RegistroModel)
        .order_by(models.RegistroModel.data_registro.desc())
        .all()
    )

@app.put("/registros/{registro_id}")
def atualizar_registro(
    registro_id: int,
    dados: schemas.RegistroUpdate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado),
):
    r = (
        db.query(models.RegistroModel)
        .filter(models.RegistroModel.id == registro_id)
        .first()
    )
    if not r:
        raise HTTPException(404, "Registro não encontrado")

    try:
        payload = dados.model_dump(exclude_unset=True)
    except Exception:
        payload = dados.dict(exclude_unset=True)

    print(f"[PUT] id={registro_id} payload={payload}")

    if "cliente_nome" in payload and payload["cliente_nome"] is not None:
        r.cliente_nome = str(payload["cliente_nome"]).strip()

    if "status" in payload and payload["status"] is not None:
        r.status = str(payload["status"]).strip()

    if "justificativa" in payload:
        r.justificativa = str(payload["justificativa"] or "").strip()

    if "operador_nome" in payload and payload["operador_nome"]:
        r.operador_nome = str(payload["operador_nome"]).strip()

    if "data_registro" in payload:
        valor = payload["data_registro"]
        if valor is not None:
            dt = _parse_data_registro(valor)
            if dt is None:
                raise HTTPException(
                    400,
                    f"data_registro inválida: {valor!r}",
                )
            r.data_registro = dt
            flag_modified(r, "data_registro")
            print(f"[PUT] data_registro atualizada para {dt}")

    db.add(r)
    db.commit()
    db.refresh(r)

    return {
        "status": "Atualizado",
        "id": r.id,
        "data_registro": r.data_registro.isoformat() if r.data_registro else None,
        "operador_nome": r.operador_nome,
        "cliente_nome": r.cliente_nome,
        "status_atual": r.status,
    }

@app.delete("/registros/{registro_id}")
def deletar_registro(
    registro_id: int,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado),
):
    r = (
        db.query(models.RegistroModel)
        .filter(models.RegistroModel.id == registro_id)
        .first()
    )
    if not r:
        raise HTTPException(404, "Registro não encontrado")
    db.delete(r)
    db.commit()
    return {"status": "Excluido"}

class PreencherNaoInformadoIn(BaseModel):
    data: str | None = None

@app.post("/registros/preencher-nao-informado")
def preencher_nao_informado_endpoint(
    dados: PreencherNaoInformadoIn = None,
    data: str = Query(None),
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin_ou_gestor),
):
    if dados and dados.data:
        data_str = dados.data
    elif data:
        data_str = data
    else:
        data_str = (date.today() - timedelta(days=1)).isoformat()

    try:
        data_alvo = date.fromisoformat(data_str)
    except ValueError:
        raise HTTPException(400, "Data inválida. Use YYYY-MM-DD.")

    resultado = rodar_preenchimento_nao_informado(data_alvo)
    return resultado

class CronogramaIn(BaseModel):
    operador: str = None
    periodo: str = None
    segunda: str = None
    terca: str = None
    quarta: str = None
    quinta: str = None
    sexta: str = None
    Operador: str = None
    Periodo: str = None
    Segunda: str = None
    Terça: str = None
    Terca: str = None
    Quarta: str = None
    Quinta: str = None
    Sexta: str = None

    class Config:
        extra = "ignore"

def _normalizar_payload_cronograma(dados: CronogramaIn) -> dict:
    d = dados.dict(exclude_unset=True)

    def pegar(*chaves, default="-"):
        for c in chaves:
            if c in d and d[c] is not None and str(d[c]).strip() != "":
                return str(d[c]).strip()
        return default

    return {
        "operador": pegar("operador", "Operador", default="").upper() or "SEM NOME",
        "periodo": pegar("periodo", "Periodo", default="MANHÃ").upper(),
        "segunda": pegar("segunda", "Segunda"),
        "terca": pegar("terca", "Terca", "Terça"),
        "quarta": pegar("quarta", "Quarta"),
        "quinta": pegar("quinta", "Quinta"),
        "sexta": pegar("sexta", "Sexta"),
    }

def _cronograma_out(item) -> dict:
    return {
        "id": item.id,
        "Operador": item.operador,
        "Periodo": item.periodo,
        "Segunda": item.segunda,
        "Terça": item.terca,
        "Quarta": item.quarta,
        "Quinta": item.quinta,
        "Sexta": item.sexta,
    }

@app.get("/cronograma/")
def listar_cronograma(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado),
):
    dados = db.query(models.CronogramaModel).order_by(models.CronogramaModel.id).all()
    return [_cronograma_out(d) for d in dados]

@app.post("/cronograma/", status_code=201)
def criar_cronograma(
    dados: CronogramaIn,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin_ou_gestor),
):
    campos = _normalizar_payload_cronograma(dados)
    novo = models.CronogramaModel(**campos)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return _cronograma_out(novo)

@app.put("/cronograma/{item_id}")
def atualizar_cronograma(
    item_id: int,
    dados: CronogramaIn,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin_ou_gestor),
):
    item = (
        db.query(models.CronogramaModel)
        .filter(models.CronogramaModel.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(404, "Linha do cronograma não encontrada.")
    campos = _normalizar_payload_cronograma(dados)
    item.operador = campos["operador"]
    item.periodo = campos["periodo"]
    item.segunda = campos["segunda"]
    item.terca = campos["terca"]
    item.quarta = campos["quarta"]
    item.quinta = campos["quinta"]
    item.sexta = campos["sexta"]
    db.commit()
    db.refresh(item)
    return {**_cronograma_out(item), "status": "atualizado"}

@app.delete("/cronograma/{item_id}")
def excluir_cronograma(
    item_id: int,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin_ou_gestor),
):
    item = (
        db.query(models.CronogramaModel)
        .filter(models.CronogramaModel.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(404, "Linha do cronograma não encontrada.")
    db.delete(item)
    db.commit()
    return {"status": "excluido", "id": item_id}