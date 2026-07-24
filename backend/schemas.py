from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator
)

from datetime import datetime
from typing import Optional



# =====================================================
# UTILITÁRIOS
# =====================================================

def sanitizar_username(v: str):

    v = (
        v or ""
    ).strip().lower().replace(" ", "_")


    v = "".join(
        c for c in v
        if c.isalnum() or c == "_"
    )


    return v



def validar_email(v):

    if not v:
        return v


    v = v.strip()


    if (
        "@"
        not in v
        or "."
        not in v.split("@")[-1]
    ):

        raise ValueError(
            "Email inválido"
        )


    return v




# =====================================================
# USUÁRIOS
# =====================================================


class UserSignupPublic(BaseModel):

    username:str
    password:str
    nome:str
    email:Optional[str]=None
    telefone:Optional[str]=None



    @field_validator("username")
    @classmethod
    def validar_username(cls,v):

        v = sanitizar_username(v)


        if len(v)<3:

            raise ValueError(
                "Usuário muito curto"
            )


        return v



    @field_validator("email")
    @classmethod
    def email_valido(cls,v):

        return validar_email(v)




class UserProfileComplete(BaseModel):

    nome:str
    email:Optional[str]=None
    telefone:Optional[str]=None



    @field_validator("email")
    @classmethod
    def email_valido(cls,v):

        return validar_email(v)




class UserOut(BaseModel):

    id:int

    username:str

    nome:Optional[str]=None

    email:Optional[str]=None

    telefone:Optional[str]=None

    role:str

    departamento_id:Optional[int]=None

    perfil_completo:bool



    model_config = ConfigDict(
        from_attributes=True
    )





# =====================================================
# CRONOGRAMA
# =====================================================


class CronogramaBase(BaseModel):

    operador:str

    dia_semana:str

    atividade:str

    cliente:str

    periodo:Optional[str]=None

    data_limite:Optional[str]=None

    status_prazo:str="Pendente"



class CronogramaCreate(
    CronogramaBase
):
    pass



class CronogramaUpdate(BaseModel):

    operador:Optional[str]=None

    dia_semana:Optional[str]=None

    atividade:Optional[str]=None

    cliente:Optional[str]=None

    periodo:Optional[str]=None

    data_limite:Optional[str]=None

    status_prazo:Optional[str]=None




class CronogramaOut(
    CronogramaBase
):

    id:int


    model_config = ConfigDict(
        from_attributes=True
    )






# =====================================================
# REGISTROS OPERACIONAIS
# =====================================================


class RegistroBase(BaseModel):

    # Compatibilidade com frontend antigo
    cliente_nome:Optional[str]=None

    cliente:Optional[str]=None


    status:str


    justificativa:Optional[str]=None



    @field_validator(
        "cliente_nome",
        mode="before"
    )
    @classmethod
    def converter_cliente(
        cls,
        v,
        info
    ):

        if v:
            return v


        dados = info.data


        return dados.get(
            "cliente"
        )




class RegistroCreate(
    RegistroBase
):

    pass





class RegistroUpdate(BaseModel):

    cliente_nome:Optional[str]=None

    status:Optional[str]=None

    justificativa:Optional[str]=None





class RegistroOut(BaseModel):

    id:int

    operador_nome:str

    cliente_nome:str

    status:str

    justificativa:Optional[str]=None

    data_registro:datetime

    caminho_evidencia:Optional[str]=None

    aprovado_gestor:Optional[str]="Pendente"



    model_config = ConfigDict(
        from_attributes=True
    )






# =====================================================
# AUDITORIA
# =====================================================


class AuditoriaOut(BaseModel):

    id:int

    timestamp:datetime

    usuario_login:Optional[str]=None

    usuario_nome:Optional[str]=None

    ip_origem:Optional[str]=None

    acao:str

    detalhes:Optional[str]=None



    model_config = ConfigDict(
        from_attributes=True
    )