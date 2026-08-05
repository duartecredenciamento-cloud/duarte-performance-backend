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
from sqlalchemy.exc import IntegrityError

from jose import JWTError, jwt

from pydantic import BaseModel

from datetime import datetime, timedelta, date
import unicodedata

import models
import schemas
import auth

from database import (
    get_db,
    engine,
    SessionLocal,
)


# =====================================================
# CRIAÇÃO DAS TABELAS
# =====================================================

models.Base.metadata.create_all(bind=engine)


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
                email="admin@duarte.com",
                nome="Administrador",
                password_hash=senha_criptografada,
                role="Admin",
                perfil_completo=True,
            )
            db.add(novo_admin)
            db.commit()
            print("✅ Admin criado.")
    except IntegrityError:
        db.rollback()
    except Exception as e:
        db.rollback()
        print(f"❌ Erro admin inicial: {e}")
    finally:
        db.close()


# =====================================================
# APP
# =====================================================

app = FastAPI(
    title="Duarte Performance API",
    description="Gestão Operacional Duarte Gestão",
    version="2.8",
)


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
# JWT
# =====================================================

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


def exigir_admin_ou_gestor(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
    if usuario.role not in ROLES_GESTAO:
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito a Admin ou Gestor.",
        )
    return usuario


def exigir_admin(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
    if usuario.role not in ("Admin", "Admin Master"):
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito ao perfil Admin.",
        )
    return usuario


# =====================================================
# HEALTH
# =====================================================

@app.get("/")
def home():
    return {
        "status": "online",
        "sistema": "Duarte Performance API",
        "versao": "2.8",
    }


@app.get("/setup-admin")
def setup_admin_manual(db: Session = Depends(get_db)):
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
        return {"status": "sucesso", "mensagem": "Admin criado. Senha: 123456"}
    admin.password_hash = senha_hash
    db.commit()
    return {"status": "sucesso", "mensagem": "Senha admin resetada para 123456"}


# =====================================================
# LOGIN
# =====================================================

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
            "nome": usuario.nome,
            "role": usuario.role,
            "id": usuario.id,
        }
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": usuario.username,
        "nome": usuario.nome,
        "role": usuario.role,
    }


# =====================================================
# USUÁRIOS
# =====================================================

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
        email=getattr(dados, "email", None) or dados.username,
        nome=dados.nome,
        password_hash=senha_hash,
        role=getattr(dados, "role", None) or "Operador",
        perfil_completo=True,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {
        "status": "sucesso",
        "mensagem": f"Usuário {novo.nome} criado com sucesso!",
        "id": novo.id,
    }


class RoleUpdate(BaseModel):
    role: str


@app.get("/usuarios/todos")
def listar_todos_usuarios(
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin_ou_gestor),
):
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
        "mensagem": f"Função de {u.nome} atualizada para {u.role}.",
        "id": u.id,
        "role": u.role,
    }


@app.get("/usuarios/me")
def meu_usuario(usuario: models.Usuario = Depends(usuario_logado)):
    return {
        "id": usuario.id,
        "username": usuario.username,
        "nome": usuario.nome,
        "email": usuario.email,
        "role": usuario.role,
        "perfil_completo": usuario.perfil_completo,
    }


# =====================================================
# NOMES ESCALA / USERNAME
# =====================================================

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
        for u in db.query(models.Usuario.nome).all()
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
# RECUPERAÇÃO DE SENHA
# =====================================================

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

    if (
        usuario.email
        and dados.email
        and usuario.email.strip().lower() != dados.email.strip().lower()
    ):
        raise HTTPException(status_code=400, detail="Dados não conferem.")

    if (
        usuario.telefone
        and dados.telefone
        and usuario.telefone.strip() != dados.telefone.strip()
    ):
        raise HTTPException(status_code=400, detail="Dados não conferem.")

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
        raise HTTPException(
            status_code=400, detail=f"Status atual: {s.status}."
        )
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


# =====================================================
# REGISTROS
# =====================================================

DIAS_COLUNA = {
    0: "segunda",
    1: "terca",
    2: "quarta",
    3: "quinta",
    4: "sexta",
}


@app.post("/registros/", response_model=schemas.RegistroOut)
def criar_registro(
    registro: schemas.RegistroCreate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado),
):
    """
    Operador comum: grava com o próprio nome.
    Admin/Gestor/Coordenador: pode mandar operador_nome e data_registro.
    """
    nome_operador = usuario.nome
    role = (usuario.role or "").strip()

    if role in ROLES_GESTAO:
        op = getattr(registro, "operador_nome", None)
        if op and str(op).strip():
            nome_operador = str(op).strip()

    novo = models.RegistroModel(
        operador_nome=nome_operador,
        cliente_nome=registro.cliente_nome,
        status=registro.status,
        justificativa=registro.justificativa or "",
    )

    data_custom = getattr(registro, "data_registro", None)
    if data_custom is not None and role in ROLES_GESTAO:
        try:
            if isinstance(data_custom, str):
                data_custom = datetime.fromisoformat(
                    data_custom.replace("Z", "+00:00")
                )
            novo.data_registro = data_custom
        except Exception:
            pass

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
    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(r, campo, valor)
    db.commit()
    return {"status": "Atualizado"}


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
    return {"status": "Excluído"}


# =====================================================
# PREENCHER NÃO INFORMADO
# =====================================================

class PreencherNaoInformadoIn(BaseModel):
    data: str | None = None  # YYYY-MM-DD


@app.post("/registros/preencher-nao-informado")
def preencher_nao_informado(
    dados: PreencherNaoInformadoIn = None,
    data: str = Query(None),
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin_ou_gestor),
):
    """
    Cria 'Não Informado' para cada Operador+Cliente da escala do dia
    que ainda NÃO tem lançamento. Não apaga nem sobrescreve.
    """
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

    weekday = data_alvo.weekday()
    if weekday >= 5:
        return {
            "status": "ok",
            "mensagem": "Fim de semana — nada a preencher.",
            "data": data_str,
            "criados": 0,
            "ignorados_ja_existiam": 0,
        }

    coluna = DIAS_COLUNA[weekday]
    linhas = db.query(models.CronogramaModel).all()
    if not linhas:
        return {
            "status": "ok",
            "mensagem": "Cronograma vazio.",
            "data": data_str,
            "criados": 0,
            "ignorados_ja_existiam": 0,
        }

    esperados = []
    for lin in linhas:
        cliente = (getattr(lin, coluna, None) or "").strip()
        operador = (lin.operador or "").strip()
        if operador and cliente and cliente != "-":
            esperados.append((operador, cliente))

    # Qualquer status no dia conta como "já existe"
    inicio = datetime.combine(data_alvo, datetime.min.time())
    fim = datetime.combine(data_alvo, datetime.max.time())
    existentes = (
        db.query(
            models.RegistroModel.operador_nome,
            models.RegistroModel.cliente_nome,
        )
        .filter(
            models.RegistroModel.data_registro >= inicio,
            models.RegistroModel.data_registro <= fim,
        )
        .all()
    )
    chave_existente = {
        ((op or "").strip().upper(), (cli or "").strip().upper())
        for op, cli in existentes
    }

    criados = 0
    ignorados = 0
    detalhes = []

    for operador, cliente in esperados:
        chave = (operador.upper(), cliente.upper())
        if chave in chave_existente:
            ignorados += 1
            continue

        dt = datetime.combine(data_alvo, datetime.min.time()).replace(
            hour=23, minute=59, second=0
        )
        novo = models.RegistroModel(
            operador_nome=operador,
            cliente_nome=cliente,
            status="Não Informado",
            justificativa="Preenchido automaticamente — operador não lançou no dia.",
            data_registro=dt,
        )
        db.add(novo)
        chave_existente.add(chave)
        criados += 1
        detalhes.append({"operador": operador, "cliente": cliente})

    if criados:
        db.commit()

    return {
        "status": "sucesso",
        "mensagem": (
            f"{data_str}: {criados} criado(s), {ignorados} já existiam."
        ),
        "data": data_str,
        "criados": criados,
        "ignorados_ja_existiam": ignorados,
        "detalhes": detalhes[:50],
    }


# =====================================================
# CRONOGRAMA
# =====================================================

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