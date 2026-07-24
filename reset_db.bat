@echo off
cd backend
del duarte_performance.db
cd ..
python init_db.py
python backend\criar_admin.py
echo.
echo ✅ Banco resetado com sucesso!
pause