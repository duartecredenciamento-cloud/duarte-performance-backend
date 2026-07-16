@echo off
TITLE Duarte Performance - Inicializador Unificado
echo ====================================================
echo    INICIALIZANDO ECOSSISTEMA DUARTE PERFORMANCE
echo ====================================================
echo.

echo [1/2] Iniciando Servidor Backend (FastAPI)...
start /min cmd /k "uvicorn main:app --reload --port 8000"

echo Aguardando sincronizacao do Banco de Dados...
timeout /t 3 /nobreak >vazio

echo [2/2] Iniciando Interface Visual (Streamlit)...
start cmd /k "streamlit run interface.py"

echo.
echo ====================================================
echo    SISTEMA RODANDO PERFEITAMENTE EM SEGUNDO PLANO
echo ====================================================
pause