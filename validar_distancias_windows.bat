@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo =============================================
echo   VALIDACAO REAL OSRM - ESCOLAS DE BAURU
echo =============================================
echo Consulta real ao OSRM; nao utiliza distancias ficticias.
where py >nul 2>nul
if %errorlevel%==0 (set "PYTHON=py -3") else (set "PYTHON=python")
if not exist .venv\Scripts\python.exe (
    echo Criando ambiente Python...
    %PYTHON% -m venv .venv
    if errorlevel 1 goto erro
)
echo Instalando dependencias, se necessario...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo.
echo Consultando distancias REAIS (pode depender da resposta do servidor)...
.venv\Scripts\python.exe scripts\validar_osrm_real.py
if errorlevel 1 goto erro
echo.
echo CONSULTA CONCLUIDA.
echo PDF: data\resultados_osrm\ANEXO_VALIDACAO_OSRM_REAL.pdf
echo JSON: data\resultados_osrm\evidencia_osrm_real.json
pause
exit /b 0
:erro
echo.
echo ERRO: consulta nao validada. Verifique internet e
 echo data\resultados_osrm\ERRO_CONSULTA_OSRM.txt
pause
exit /b 2
