@echo off
chcp 65001 > nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON=py -3"
) else (
  set "PYTHON=python"
)
echo ===============================================
echo  CAMINHOS E CICLOS HAMILTONIANOS - BAURU
 echo ===============================================
%PYTHON% --version
if errorlevel 1 (
 echo ERRO: Python 3 nao encontrado. Instale Python 3.11 ou superior.
 pause
 exit /b 1
)
if not exist .venv\Scripts\python.exe (
 echo Criando ambiente virtual...
 %PYTHON% -m venv .venv
 if errorlevel 1 goto erro
)
echo Instalando dependencias (somente na primeira execucao)...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo Iniciando aplicativo em http://localhost:8501
.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
pause
exit /b 0
:erro
echo Falha na instalacao. Verifique conexao e versao do Python.
pause
exit /b 1
