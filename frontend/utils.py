# ==============================================================================
# UTILS.PY — Duarte Performance (Módulo de Utilitários)
# ==============================================================================
import pandas as pd
from datetime import datetime

def dia_semana_atual():
    """Retorna o dia da semana atual formatado em Português."""
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    return dias[datetime.now().weekday()]

def parsear_planilha_escala(file_upload):
    """
    Realiza o parse e higienização de arquivos de escala (.xlsx / .csv).
    Retorna o DataFrame estruturado e uma lista de avisos/erros.
    """
    avisos = []
    df = pd.DataFrame()

    try:
        if file_upload.name.endswith('.csv'):
            df = pd.read_csv(file_upload)
        else:
            df = pd.read_excel(file_upload)

        # Padroniza nomes de colunas (caixa baixa e sem espaços extras)
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Mapeamento de colunas flexível
        mapa_colunas = {
            'operador': 'operador',
            'nome': 'operador',
            'colaborador': 'operador',
            'dia': 'dia_semana',
            'dia_semana': 'dia_semana',
            'cliente': 'cliente',
            'carteira': 'cliente',
            'status': 'cliente',
            'periodo': 'periodo',
            'turno': 'periodo'
        }

        df = df.rename(columns=mapa_colunas)

        # Validação de colunas obrigatórias
        colunas_necessarias = ['operador', 'cliente']
        faltantes = [col for col in colunas_necessarias if col not in df.columns]

        if faltantes:
            avisos.append(f"A planilha precisa conter pelo menos as colunas: {', '.join(colunas_necessarias)}.")
            return pd.DataFrame(), avisos

        # Preenchimento de colunas opcionais
        if 'dia_semana' not in df.columns:
            df['dia_semana'] = 'Segunda'
        if 'periodo' not in df.columns:
            df['periodo'] = 'MANHA'

        # Limpeza de dados
        df['operador'] = df['operador'].astype(str).str.strip()
        df['cliente'] = df['cliente'].astype(str).str.strip()
        df['dia_semana'] = df['dia_semana'].astype(str).str.strip().str.capitalize()

        # Remove linhas totalmente vazias ou sem operador
        df = df[df['operador'] != ''].dropna(subset=['operador'])

    except Exception as e:
        avisos.append(f"Erro ao ler o arquivo: {str(e)}")

    return df, avisos

def detectar_duplicidade_escala(df):
    """
    Identifica se um mesmo operador possui alocações sobrepostas/duplicadas 
    no mesmo dia e período.
    """
    if df.empty or 'operador' not in df.columns or 'dia_semana' not in df.columns:
        df['duplicado_local'] = False
        return df

    # Identifica duplicatas baseadas na combinação de Operador + Dia
    duplicados = df.duplicated(subset=['operador', 'dia_semana'], keep=False)
    df['duplicado_local'] = duplicados
    return df