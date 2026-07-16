import os
import shutil
from datetime import datetime
from typing import Optional, List

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    File,
    UploadFile,
    Form,
    Request
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import JWTError, jwt

# Importações locais do projeto
from database import engine, get_db
import models
import schemas
import auth

# Força a criação/atualização de todas as tabelas no PostgreSQL ao iniciar
models.Base.metadata.create_all(bind=engine)

# Diretório para armazenamento físico das evidências de execução
UPLOAD_DIR = "./armazenamento_evidencias"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="Duarte Performance - Backend Corporativo",
    description="API de controle operacional com trilhas de auditoria, LGPD e banco PostgreSQL",
    version="4.0"
)

# Configuração de CORS para permitir que o Streamlit acesse a API local ou em nuvem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# =====================================================
# AUXILIAR: REGISTRO DE AUDITORIA INTERNA (LGPD/Compliance)
# =====================================================
def registrar_log(
    db: Session, 
    acao: str, 
    detalhes: str, 
    request: Request, 
    cpf: Optional[str] = None, 
    nome: Optional[str] = None
):
    """
    Função centralizada para registrar de forma imutável qualquer ação crítica.
    Captura automaticamente o IP de origem (mesmo atrás de proxies como Render/Nginx).
    """
    ip_cliente = request.headers.get("X-Forwarded-For", request.client.host if request.client else "IP_DESCONHECIDO")
    
    # Se o IP vier como lista de proxies, pega apenas o primeiro (IP real)
    if "," in ip_cliente:
        ip_cliente = ip_cliente.split(",")[0].strip()

    log_entry = models.AuditoriaModel(
        usuario_cpf=cpf,
        usuario_nome=nome,
        ip_origem=ip_cliente,
        acao=acao,
        detalhes=detalhes
    )
    db.add(log_entry)
    db.commit()


# =====================================================
# VALIDAÇÃO DO USUÁRIO LOGADO (JWT + RBAC)
# =====================================================
def obter_usuario_atual(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    erro_auth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessão inválida ou expirada. Faça login novamente."
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        cpf: str = payload.get("sub")
        if cpf is None:
            raise erro_auth
    except JWTError:
        raise erro_auth
        
    user = db.query(models.UserModel).filter(models.UserModel.cpf == cpf).first()
    if user is None:
        raise erro_auth
        
    return user


# =====================================================
# ENDPOINT: AUTENTICAÇÃO / LOGIN POR CPF SANITIZADO
# =====================================================
@app.post("/token")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Sanitiza o CPF digitado: remove pontos, traços e espaços, deixando apenas números
    cpf_limpo = "".join(filter(str.isdigit, form_data.username))
    
    user = db.query(models.UserModel).filter(models.UserModel.cpf == cpf_limpo).first()
    
    if not user or not auth.verificar_senha(form_data.password, user.password_hash):
        # Auditoria registra falha de login (útil para detectar ataques de força bruta)
        registrar_log(
            db=db,
            acao="LOGIN_FAILED",
            detalhes=f"Tentativa falha de login para o CPF: {cpf_limpo}",
            request=request,
            cpf=cpf_limpo
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="CPF ou Senha incorretos."
        )

    # Gera o Token de expediente (expira em 8 horas)
    token_jwt = auth.criar_token_acesso(data={"sub": user.cpf, "role": user.role})
    
    # Registra o login bem-sucedido
    registrar_log(
        db=db,
        acao="LOGIN_SUCCESS",
        detalhes=f"Usuário {user.nome} autenticado com o perfil: {user.role}",
        request=request,
        cpf=user.cpf,
        nome=user.nome
    )
    
    return {
        "access_token": token_jwt,
        "token_type": "bearer",
        "role": user.role,
        "nome": user.nome,
        "cpf": user.cpf
    }


# =====================================================
# ENDPOINTS: CRONOGRAMA OPERACIONAL & DUPLICIDADE
# =====================================================
@app.get("/cronograma/")
def listar_cronograma(
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(obter_usuario_atual)
):
    # Operadores visualizam apenas as suas respectivas alocações da semana
    if current_user.role == "Operador":
        itens = db.query(models.CronogramaModel).filter(models.CronogramaModel.operador == current_user.nome).all()
    else:
        # Administradores e Gestores têm visão macro da escala
        itens = db.query(models.CronogramaModel).all()

    # Algoritmo de validação de duplicidade semanal na listagem
    contagem_atribucoes = {}
    for item in itens:
        chave = (item.operador, item.cliente)
        contagem_atribucoes[chave] = contagem_atribucoes.get(chave, 0) + 1

    resposta_enriquecida = []
    for item in itens:
        chave = (item.operador, item.cliente)
        is_duplicado = contagem_atribucoes[chave] > 1
        
        resposta_enriquecida.append({
            "id": item.id,
            "operador": item.operador,
            "dia_semana": item.dia_semana,
            "atividade": item.atividade,
            "cliente": item.cliente,
            "periodo": item.periodo,
            "data_limite": item.data_limite,
            "status_prazo": item.status_prazo,
            "duplicado": is_duplicado  # Flag consumida pelo frontend para gerar o alerta visual
        })

    return resposta_enriquecida


@app.post("/cronograma/")
def criar_escala_semanal(
    request: Request,
    dados: schemas.CronogramaCreate,
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(obter_usuario_atual)
):
    if current_user.role not in ["Admin Master", "Gestor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso negado. Apenas Gestores ou Administradores podem criar escalas."
        )
    
    # Verifica duplicidades prévias para o log e retorno
    duplicidade_existente = db.query(models.CronogramaModel).filter(
        models.CronogramaModel.operador == dados.operador,
        models.CronogramaModel.cliente == dados.cliente
    ).first()
    
    houve_duplicidade = True if duplicidade_existente else False
        
    novo_item = models.CronogramaModel(
        operador=dados.operador,
        dia_semana=dados.dia_semana,
        atividade=dados.atividade,
        cliente=dados.cliente,
        periodo=dados.periodo,
        data_limite=dados.data_limite,
        status_prazo=dados.status_prazo
    )
    db.add(novo_item)
    db.commit()
    db.refresh(novo_item)
    
    registrar_log(
        db=db,
        acao="CREATE_CRONOGRAMA",
        detalhes=f"Definiu atividade de {dados.cliente} para {dados.operador} na {dados.dia_semana}. Duplicidade: {houve_duplicidade}",
        request=request,
        cpf=current_user.cpf,
        nome=current_user.nome
    )
    
    return {"status": "sucesso", "item": novo_item, "alerta_duplicidade": houve_duplicidade}


# =====================================================
# ENDPOINTS: REGISTRO OPERACIONAL DIÁRIO (Upload e Evidência)
# =====================================================
@app.post("/registros/")
def lancar_execucao_diaria(
    request: Request,
    operador_nome: str = Form(...),
    cliente_nome: str = Form(...),
    status: str = Form(...),
    justificativa: Optional[str] = Form(None),
    evidencia: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(obter_usuario_atual)
):
    # Validação obrigatória: status de 'Não Realizado' ou 'Realizado Parcial' EXIGE justificativa textual
    if status in ["Não Realizado", "Realizado Parcial"] and (not justificativa or len(justificativa.strip()) < 5):
        raise HTTPException(
            status_code=400, 
            detail="Justificativa obrigatória para entregas parciais ou não concluídas."
        )

    caminho_arquivo = None
    if evidencia:
        # Sanitização do nome do arquivo físico para evitar substituições
        nome_unico = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{evidencia.filename}"
        caminho_arquivo = os.path.join(UPLOAD_DIR, nome_unico)
        with open(caminho_arquivo, "wb") as buffer:
            shutil.copyfileobj(evidencia.file, buffer)
            
    novo_registro = models.RegistroModel(
        operador_nome=operador_nome,
        cliente_nome=cliente_nome,
        status=status,
        justificativa=justificativa,
        caminho_evidencia=caminho_arquivo,
        aprovado_gestor="Pendente"
    )
    
    db.add(novo_registro)
    db.commit()
    db.refresh(novo_registro)
    
    registrar_log(
        db=db,
        acao="CREATE_REGISTRO",
        detalhes=f"Lançou status '{status}' para o cliente '{cliente_nome}'",
        request=request,
        cpf=current_user.cpf,
        nome=current_user.nome
    )
    return novo_registro


# =====================================================
# ENDPOINTS: GESTÃO DE USUÁRIOS (Exclusivo Admin Master)
# =====================================================
@app.get("/usuarios/", response_model=List[schemas.UserOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(obter_usuario_atual)
):
    if current_user.role not in ["Admin Master", "Gestor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso restrito a gestores e administradores."
        )
    return db.query(models.UserModel).all()


@app.post("/usuarios/", response_model=schemas.UserOut)
def cadastrar_colaborador(
    request: Request,
    novo_usuario: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(obter_usuario_atual)
):
    if current_user.role != "Admin Master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Apenas o Admin Master pode cadastrar colaboradores no sistema."
        )
    
    # Sanitiza o CPF inserido para salvar apenas os 11 números no banco
    cpf_limpo = "".join(filter(str.isdigit, novo_usuario.cpf))
    
    usuario_existente = db.query(models.UserModel).filter(models.UserModel.cpf == cpf_limpo).first()
    if usuario_existente:
        raise HTTPException(
            status_code=400, 
            detail="Este CPF já está cadastrado no sistema."
        )
    
    # Hash seguro da senha provisória via Bcrypt
    senha_hasheada = auth.obter_hash_senha(novo_usuario.password)
    
    usuario_db = models.UserModel(
        cpf=cpf_limpo,
        nome=novo_usuario.nome,
        password_hash=senha_hasheada,
        role=novo_usuario.role,
        departamento_id=novo_usuario.departamento_id
    )
    
    db.add(usuario_db)
    db.commit()
    db.refresh(usuario_db)
    
    registrar_log(
        db=db,
        acao="CREATE_USER",
        detalhes=f"Cadastrou o colaborador {usuario_db.nome} (CPF: {cpf_limpo}) com perfil {usuario_db.role}",
        request=request,
        cpf=current_user.cpf,
        nome=current_user.nome
    )
    
    return usuario_db


@app.delete("/usuarios/{usuario_id}")
def deletar_colaborador(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(obter_usuario_atual)
):
    if current_user.role != "Admin Master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Apenas o Admin Master pode remover colaboradores."
        )
        
    usuario = db.query(models.UserModel).filter(models.UserModel.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não localizado.")
        
    if usuario.cpf == current_user.cpf:
        raise HTTPException(status_code=400, detail="Operação inválida. Você não pode deletar a si mesmo.")
        
    db.delete(usuario)
    db.commit()
    
    registrar_log(
        db=db,
        acao="DELETE_USER",
        detalhes=f"Removeu o colaborador {usuario.nome} (CPF: {usuario.cpf}) do sistema",
        request=request,
        cpf=current_user.cpf,
        nome=current_user.nome
    )
    
    return {"status": "sucesso", "mensagem": "Colaborador removido com sucesso."}


# =====================================================
# ENDPOINTS: RELATÓRIOS & AUDITORIA DE SEGURANÇA
# =====================================================
@app.get("/auditoria/", response_model=List[schemas.AuditoriaOut])
def extrair_logs_auditoria(
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(obter_usuario_atual)
):
    if current_user.role != "Admin Master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso negado. Logs de auditoria são confidenciais do Admin Master."
        )
    return db.query(models.AuditoriaModel).order_by(models.AuditoriaModel.timestamp.desc()).all()


@app.get("/departamentos/")
def listar_departamentos(
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(obter_usuario_atual)
):
    return db.query(models.DepartamentoModel).all()