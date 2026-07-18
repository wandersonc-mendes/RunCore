@echo off
cd /d %~dp0

echo ================================================
echo   RunCore Web - iniciando backend e frontend
echo ================================================
echo.

where npm >nul 2>nul
if errorlevel 1 (
    echo ATENCAO: nao encontrei o Node.js instalado nesta maquina.
    echo O frontend do RunCore Web precisa dele pra funcionar.
    echo.
    echo Baixe e instale a versao LTS em: https://nodejs.org
    echo Depois de instalar, feche esta janela e clique de novo neste arquivo.
    echo.
    pause
    exit /b
)

echo [1/3] Instalando dependencias do backend (Python)...
pip install -r requirements.txt

echo.
echo [2/3] Abrindo o backend (API)...
start "RunCore - BACKEND (nao feche esta janela)" cmd /k "cd /d %~dp0src && uvicorn api.main:app --reload --port 8000"

echo.
echo [3/3] Preparando o frontend (tela)...
if not exist "%~dp0frontend\node_modules" (
    echo Baixando pacotes do frontend, isso acontece so na primeira vez e pode demorar alguns minutos...
    call npm install --prefix "%~dp0frontend"
)
if not exist "%~dp0frontend\.env" (
    copy "%~dp0frontend\.env.example" "%~dp0frontend\.env" > nul
)

start "RunCore - FRONTEND (nao feche esta janela)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Aguardando o site ficar pronto...
timeout /t 8 /nobreak > nul
start http://localhost:5173

echo.
echo ================================================
echo Pronto! Devem ter aberto 2 janelas pretas (BACKEND e FRONTEND).
echo Deixe as duas abertas enquanto estiver usando o RunCore Web.
echo O navegador deve ter aberto sozinho em localhost:5173
echo Pra fechar tudo, so fechar essas 2 janelas pretas.
echo ================================================
pause
