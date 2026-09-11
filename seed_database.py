import os
import sqlite3
# Se você estiver usando SQLAlchemy / PostgreSQL no Railway:
# from database import SessionLocal, engine
# from models import User, Schedule, Client

# Lista de Operadores
OPERADORES = [
    {"username": "aline", "name": "Aline", "role": "OPERADOR"},
    {"username": "larissa", "name": "Larissa", "role": "OPERADOR"},
    {"username": "karine", "name": "Karine", "role": "OPERADOR"},
    {"username": "neia", "name": "Neia", "role": "OPERADOR"},
    {"username": "silvana", "name": "Silvana", "role": "OPERADOR"},
    {"username": "julia", "name": "Julia", "role": "OPERADOR"},
    {"username": "edvania", "name": "Edvania", "role": "OPERADOR"},
    {"username": "claudia", "name": "Claudia", "role": "OPERADOR"},
    {"username": "felipe", "name": "Felipe", "role": "OPERADOR"},
    {"username": "erick", "name": "Erick", "role": "ADMIN/TI"}
]

# Matriz Completa da Escala extraída do CONOGRAMA.xlsx
ESCALA_MATRIZ = [
    # ALINE
    {"operator": "aline", "period": "MANHA", "day": "SEGUNDA", "client": "FINANCEIRO"},
    {"operator": "aline", "period": "MANHA", "day": "TERÇA", "client": "RH/ADM"},
    {"operator": "aline", "period": "MANHA", "day": "QUARTA", "client": "SUPORTE ABRAÃO"},
    {"operator": "aline", "period": "MANHA", "day": "QUINTA", "client": "SUPORTE CRIS"},
    {"operator": "aline", "period": "MANHA", "day": "SEXTA", "client": "FINANCEIRO"},
    {"operator": "aline", "period": "TARDE", "day": "TERÇA", "client": "FINANCEIRO"},
    {"operator": "aline", "period": "TARDE", "day": "QUINTA", "client": "FINANCEIRO"},

    # LARISSA
    {"operator": "larissa", "period": "MANHA", "day": "SEGUNDA", "client": "EV-CITI"},
    {"operator": "larissa", "period": "MANHA", "day": "TERÇA", "client": "MEDLIGTH"},
    {"operator": "larissa", "period": "MANHA", "day": "QUARTA", "client": "IMC"},
    {"operator": "larissa", "period": "MANHA", "day": "QUINTA", "client": "CONVACARE"},
    {"operator": "larissa", "period": "TARDE", "day": "SEGUNDA", "client": "COBERTURA (14 Á 18) KAS"},
    {"operator": "larissa", "period": "TARDE", "day": "TERÇA", "client": "COBERTURA (14 Á 18) KAS"},
    {"operator": "larissa", "period": "TARDE", "day": "QUARTA", "client": "COBERTURA (14 Á 18) KAS"},
    {"operator": "larissa", "period": "TARDE", "day": "QUINTA", "client": "COBERTURA (14 Á 18) KAS"},
    {"operator": "larissa", "period": "TARDE", "day": "SEXTA", "client": "RESCINDIDOS - UNICLIN/MAR/SILMARO e ETC"},

    # KARINE
    {"operator": "karine", "period": "MANHA", "day": "SEGUNDA", "client": "ALPHA LABs"},
    {"operator": "karine", "period": "MANHA", "day": "TERÇA", "client": "CLINICA TOPÁZIO"},
    {"operator": "karine", "period": "MANHA", "day": "QUARTA", "client": "RALG 2° e 4° SEMANA"},
    {"operator": "karine", "period": "MANHA", "day": "QUINTA", "client": "MVS"},
    {"operator": "karine", "period": "MANHA", "day": "SEXTA", "client": "ATIVAMENTE"},
    {"operator": "karine", "period": "TARDE", "day": "QUARTA", "client": "PRIME  1° e 3° SEMANA"},
    {"operator": "karine", "period": "TARDE", "day": "SEXTA", "client": "DIOGO PARAUAPEBAS"},

    # NEIA
    {"operator": "neia", "period": "MANHA", "day": "SEGUNDA", "client": "CLINICA VIVENCY"},
    {"operator": "neia", "period": "MANHA", "day": "TERÇA", "client": "RBL"},
    {"operator": "neia", "period": "MANHA", "day": "QUARTA", "client": "CLINICA AMINO"},
    {"operator": "neia", "period": "MANHA", "day": "QUINTA", "client": "CLINICA FARFALLA"},
    {"operator": "neia", "period": "MANHA", "day": "SEXTA", "client": "INST. VER"},

    # SILVANA
    {"operator": "silvana", "period": "MANHA", "day": "SEGUNDA", "client": "PRO-EXAME"},
    {"operator": "silvana", "period": "MANHA", "day": "TERÇA", "client": "CLIN COFFI"},
    {"operator": "silvana", "period": "MANHA", "day": "QUARTA", "client": "HOSP. AMATO"},
    {"operator": "silvana", "period": "MANHA", "day": "QUINTA", "client": "TRIDES"},
    {"operator": "silvana", "period": "MANHA", "day": "SEXTA", "client": "HARMONY"},
    {"operator": "silvana", "period": "TARDE", "day": "QUARTA", "client": "LAB. BRUNO"},

    # JULIA
    {"operator": "julia", "period": "MANHA", "day": "SEGUNDA", "client": "FR FISIO"},
    {"operator": "julia", "period": "MANHA", "day": "TERÇA", "client": "CANTAREIRA"},
    {"operator": "julia", "period": "MANHA", "day": "QUARTA", "client": "CIE FISIO - SJC"},
    {"operator": "julia", "period": "MANHA", "day": "QUINTA", "client": "CLINICA ROSANA"},
    {"operator": "julia", "period": "MANHA", "day": "SEXTA", "client": "VIVA - TEA"},

    # EDVANIA
    {"operator": "edvania", "period": "MANHA", "day": "SEGUNDA", "client": "REGULAÇÃO"},
    {"operator": "edvania", "period": "MANHA", "day": "TERÇA", "client": "EDITAIS"},
    {"operator": "edvania", "period": "MANHA", "day": "QUARTA", "client": "EDITAIS"},
    {"operator": "edvania", "period": "MANHA", "day": "QUINTA", "client": "GESTÃO COMERCIAL"},
    {"operator": "edvania", "period": "MANHA", "day": "SEXTA", "client": "GESTÃO COMERCIAL"},

    # CLAUDIA
    {"operator": "claudia", "period": "MANHA", "day": "SEGUNDA", "client": "REGULAÇÃO"},
    {"operator": "claudia", "period": "MANHA", "day": "TERÇA", "client": "EDITAIS"},
    {"operator": "claudia", "period": "MANHA", "day": "QUARTA", "client": "EDITAIS"},
    {"operator": "claudia", "period": "MANHA", "day": "QUINTA", "client": "EMS-BETESDA"},
    {"operator": "claudia", "period": "MANHA", "day": "SEXTA", "client": "MULHER MODERNA"},

    # FELIPE
    {"operator": "felipe", "period": "MANHA", "day": "SEGUNDA", "client": "SUPORTE"},
    {"operator": "felipe", "period": "MANHA", "day": "TERÇA", "client": "SUPORTE"},
    {"operator": "felipe", "period": "MANHA", "day": "QUARTA", "client": "SUPORTE"},
    {"operator": "felipe", "period": "MANHA", "day": "QUINTA", "client": "CRM (apoio comercial)"},
    {"operator": "felipe", "period": "MANHA", "day": "SEXTA", "client": "MAILING"},

    # ERICK
    {"operator": "erick", "period": "MANHA", "day": "SEGUNDA", "client": "TI"},
    {"operator": "erick", "period": "MANHA", "day": "TERÇA", "client": "TI"},
    {"operator": "erick", "period": "MANHA", "day": "QUARTA", "client": "TI"},
    {"operator": "erick", "period": "MANHA", "day": "QUINTA", "client": "SUPORTE ABRAÃO"},
    {"operator": "erick", "period": "MANHA", "day": "SEXTA", "client": "SUPORTE ABRAÃO"},
    {"operator": "erick", "period": "TARDE", "day": "SEGUNDA", "client": "SUPORTE ABRAÃO"},
    {"operator": "erick", "period": "TARDE", "day": "TERÇA", "client": "SUPORTE ABRAÃO"},
    {"operator": "erick", "period": "TARDE", "day": "QUARTA", "client": "SUPORTE ABRAÃO"},
    {"operator": "erick", "period": "TARDE", "day": "QUINTA", "client": "SUPORTE ABRAÃO"},
    {"operator": "erick", "period": "TARDE", "day": "SEXTA", "client": "SUPORTE ABRAÃO"},
]

print("Script de Carga de Dados pronto para execução no banco!")