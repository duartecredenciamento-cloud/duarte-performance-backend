from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from database import SessionLocal
import models

DIAS_SEMANA_MAP = {
    0: "segunda",
    1: "terca",
    2: "quarta",
    3: "quinta",
    4: "sexta",
}

def _extrair_cliente_base(nome_cliente: str) -> str:
    """Remove prefixos como 'Antecipação - ' ou 'Suporte - ' para conciliação estrita."""
    if not nome_cliente:
        return ""
    limpo = nome_cliente.strip()
    for prefixo in ["Antecipação - ", "Suporte - ", "antecipação - ", "suporte - "]:
        if limpo.lower().startswith(prefixo.lower()):
            return limpo[len(prefixo):].strip()
    return limpo

def rodar_preenchimento_nao_informado(data_alvo: date = None) -> dict:
    """
    Verifica operadores/clientes previstos na escala para `data_alvo`.
    Considera lançamentos diretos, suporte e antecipações registradas até a data alvo.
    """
    if data_alvo is None:
        data_alvo = date.today()

    dia_semana_num = data_alvo.weekday()
    if dia_semana_num not in DIAS_SEMANA_MAP:
        return {
            "status": "ignorado",
            "mensagem": f"Data {data_alvo} é final de semana. Nenhuma automação executada.",
            "registros_criados": 0
        }

    coluna_dia = DIAS_SEMANA_MAP[dia_semana_num]
    db: Session = SessionLocal()

    try:
        # 1. Obter a escala agendada para o dia alvo
        itens_escala = db.query(models.CronogramaModel).all()
        if not itens_escala:
            return {"status": "alerta", "mensagem": "Nenhum cronograma encontrado.", "registros_criados": 0}

        esperados = []
        for item in itens_escala:
            cliente_agendado = getattr(item, coluna_dia, None)
            if cliente_agendado and str(cliente_agendado).strip() not in ("-", ""):
                esperados.append({
                    "operador": item.operador.strip(),
                    "cliente": str(cliente_agendado).strip()
                })

        if not esperados:
            return {"status": "sucesso", "mensagem": f"Sem agendamentos para {coluna_dia}.", "registros_criados": 0}

        # 2. Definir janela de busca (Início da semana até o fim do dia alvo para pegar antecipações prévias)
        inicio_semana = data_alvo - timedelta(days=dia_semana_num)
        dt_inicio_semana = datetime.combine(inicio_semana, time(0, 0, 0))
        dt_fim_dia_alvo = datetime.combine(data_alvo, time(23, 59, 59))

        # 3. Buscar todos os lançamentos da semana até a data_alvo
        registros_semana = db.query(models.RegistroModel).filter(
            models.RegistroModel.data_registro >= dt_inicio_semana,
            models.RegistroModel.data_registro <= dt_fim_dia_alvo
        ).all()

        # Build de mapa de conciliação: (operador_slug, cliente_base_slug)
        atividades_concluidas = set()
        for r in registros_semana:
            if not r.operador_nome or not r.cliente_nome:
                continue
            
            op_norm = r.operador_nome.strip().lower()
            cli_base = _extrair_cliente_base(r.cliente_nome).strip().lower()
            
            # Se foi lançado no próprio dia OU se foi uma antecipação gravada em dias anteriores
            eh_no_dia = (r.data_registro.date() == data_alvo)
            eh_antecipacao = "antecipação" in r.cliente_nome.lower()

            if eh_no_dia or eh_antecipacao:
                atividades_concluidas.add((op_norm, cli_base))

        # 4. Inserir 'Não Informado' apenas para o que não foi nem realizado no dia nem antecipado
        novos_registros = []
        data_hora_gravar = datetime.combine(data_alvo, time(23, 50, 0))

        for esp in esperados:
            op_norm = esp["operador"].lower()
            cli_norm = _extrair_cliente_base(esp["cliente"]).lower()

            if (op_norm, cli_norm) not in atividades_concluidas:
                novos_registros.append(
                    models.RegistroModel(
                        operador_nome=esp["operador"],
                        cliente_nome=esp["cliente"],
                        status="Não Informado",
                        justificativa="Preenchimento automático via sistema (ausência de lançamento ou antecipação).",
                        data_registro=data_hora_gravar
                    )
                )

        if novos_registros:
            db.bulk_save_objects(novos_registros)
            db.commit()

        return {
            "status": "sucesso",
            "data_processada": data_alvo.isoformat(),
            "registros_criados": len(novos_registros),
            "detalhes": [f"{r.operador_nome} -> {r.cliente_nome}" for r in novos_registros]
        }

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()