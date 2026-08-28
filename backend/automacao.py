from datetime import date, datetime, time
from database import SessionLocal
import models

DIAS_COLUNA = {
    0: "segunda",
    1: "terca",
    2: "quarta",
    3: "quinta",
    4: "sexta",
}

def rodar_preenchimento_nao_informado(data_alvo: date = None) -> dict:
    """
    Compara os clientes esperados no Cronograma com os registros do dia.
    Gera lançamentos automáticos com status 'Não Informado' para as pendências.
    """
    if data_alvo is None:
        data_alvo = date.today()

    weekday = data_alvo.weekday()
    if weekday >= 5:
        print(f"ℹ️ [Automação] {data_alvo}: Fim de semana — sem pendências a gerar.")
        return {"status": "ok", "mensagem": "Fim de semana", "criados": 0}

    coluna = DIAS_COLUNA.get(weekday)
    if not coluna:
        return {"status": "erro", "mensagem": "Dia da semana inválido", "criados": 0}

    db = SessionLocal()
    try:
        linhas = db.query(models.CronogramaModel).all()
        if not linhas:
            print("ℹ️ [Automação] Cronograma está vazio.")
            return {"status": "ok", "mensagem": "Cronograma vazio", "criados": 0}

        esperados = []
        for lin in linhas:
            cliente = (getattr(lin, coluna, None) or "").strip()
            operador = (lin.operador or "").strip()
            if operador and cliente and cliente != "-":
                esperados.append((operador, cliente))

        inicio = datetime.combine(data_alvo, time.min)
        fim = datetime.combine(data_alvo, time.max)
        
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

            dt = datetime.combine(data_alvo, time(23, 59, 0))
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

        if criados > 0:
            db.commit()
            print(f"✅ [Automação] {criados} registro(s) 'Não Informado' criado(s) para {data_alvo}.")
        else:
            print(f"ℹ️ [Automação] Todos os lançamentos do dia {data_alvo} já existem.")

        return {
            "status": "sucesso",
            "mensagem": f"{data_alvo}: {criados} criado(s), {ignorados} já existiam.",
            "data": str(data_alvo),
            "criados": criados,
            "ignorados_ja_existiam": ignorados,
            "detalhes": detalhes[:50],
        }
    except Exception as e:
        db.rollback()
        print(f"❌ [Automação] Erro ao preencher lançamentos automáticos: {e}")
        return {"status": "erro", "mensagem": str(e), "criados": 0}
    finally:
        db.close()