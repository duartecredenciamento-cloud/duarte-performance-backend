"""
Funções auxiliares de lógica de negócio do Duarte Performance.

Mantidas separadas do interface.py de propósito: a tela (layout) chama essas
funções, mas não deveria conter regra de negócio dentro dela.
"""
import pandas as pd
from datetime import datetime

DIAS_SEMANA_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def dia_semana_atual() -> str:
    """Dia da semana de hoje, em português, no mesmo formato usado no cronograma."""
    return DIAS_SEMANA_PT[datetime.now().weekday()]


def detectar_duplicidade_escala(df: pd.DataFrame, col_operador: str = "operador", col_cliente: str = "cliente") -> pd.DataFrame:
    """
    Recebe um DataFrame de cronograma e devolve o mesmo DataFrame com uma
    coluna booleana 'duplicado_local', marcando True quando o mesmo cliente
    aparece mais de uma vez para o mesmo operador (útil para conferir antes
    de importar uma planilha nova, antes mesmo de mandar pro backend).
    """
    if df.empty:
        df = df.copy()
        df["duplicado_local"] = []
        return df
    contagem = df.groupby([col_operador, col_cliente])[col_cliente].transform("count")
    df = df.copy()
    df["duplicado_local"] = contagem > 1
    return df


def formatar_cliente_suporte(cliente: str) -> str:
    """Formata a tarefa de Suporte no padrão 'Suporte - [Cliente]'."""
    cliente = (cliente or "").strip()
    return f"Suporte - {cliente}" if cliente else "Suporte"


def clientes_do_operador_no_dia(df_cronograma: pd.DataFrame, operador: str, dia: str) -> list:
    """Filtra o cronograma pra achar só os clientes atribuídos a esse operador nesse dia da semana."""
    if df_cronograma.empty or "operador" not in df_cronograma.columns:
        return []
    filtro = (df_cronograma["operador"].str.lower() == (operador or "").lower()) & (df_cronograma["dia_semana"] == dia)
    clientes = df_cronograma.loc[filtro, "cliente"].dropna().unique().tolist()
    return sorted(c for c in clientes if c)


def parsear_planilha_escala(arquivo):
    """
    Lê um .xlsx ou .csv de escala enviado pelo usuário e tenta mapear as
    colunas para o padrão do sistema (operador, dia_semana, cliente, periodo).
    Aceita variações comuns de nome de coluna (maiúsculas, com/sem acento).

    Retorna (DataFrame normalizado, lista de avisos/erros). Se a lista de
    avisos não estiver vazia e o DataFrame vier vazio, é porque a planilha
    não pôde ser processada (colunas obrigatórias não encontradas).
    """
    avisos = []
    try:
        if arquivo.name.lower().endswith(".csv"):
            df = pd.read_csv(arquivo)
        else:
            df = pd.read_excel(arquivo)
    except Exception as e:
        return pd.DataFrame(), [f"Não foi possível ler o arquivo: {e}"]

    mapa_colunas = {
        "operador": ["operador", "operador / gestor", "colaborador", "nome"],
        "dia_semana": ["dia", "dia_semana", "dia da semana"],
        "cliente": ["cliente", "atividade", "cliente / atividade"],
        "periodo": ["periodo", "período", "turno"],
    }

    colunas_normalizadas = {str(c).strip().lower(): c for c in df.columns}
    renomear = {}
    faltando = []
    for alvo, variacoes in mapa_colunas.items():
        encontrado = next((colunas_normalizadas[v] for v in variacoes if v in colunas_normalizadas), None)
        if encontrado:
            renomear[encontrado] = alvo
        elif alvo != "periodo":  # período é opcional, o resto é obrigatório
            faltando.append(alvo)

    if faltando:
        avisos.append(
            f"Colunas obrigatórias não encontradas na planilha: {', '.join(faltando)}. "
            f"Cabeçalhos esperados (algum sinônimo de): operador, dia da semana, cliente."
        )
        return pd.DataFrame(), avisos

    df = df.rename(columns=renomear)
    colunas_finais = [c for c in ["operador", "dia_semana", "cliente", "periodo"] if c in df.columns]
    df = df[colunas_finais].dropna(subset=["operador", "cliente"])
    df["operador"] = df["operador"].astype(str).str.strip()
    df["cliente"] = df["cliente"].astype(str).str.strip()
    if "dia_semana" in df.columns:
        df["dia_semana"] = df["dia_semana"].astype(str).str.strip().str.capitalize()

    return df, avisos