@echo off
:: =====================================================================
:: B2B Loterias — Iniciador do Servidor (versao .bat hibrida)
:: Inicia Node.js se disponivel ou PowerShell server.ps1 automaticamente
:: =====================================================================

set "APP_DIR=%~dp0"

:: Verificar se servidor ja esta rodando
curl -s --connect-timeout 2 http://localhost:8777/ >nul 2>&1
if %errorlevel%==0 (
    echo [B2B] Servidor ja esta rodando em http://localhost:8777
    start "" msedge "http://localhost:8777/"
    exit /b 0
)

echo [B2B] Iniciando servidor B2B Loterias...

:: Verificar se Node.js esta disponivel
set "USE_NODE=0"
where node >nul 2>&1
if %errorlevel% equ 0 (
    set "NODE_EXE=node"
    set "USE_NODE=1"
) else if exist "C:\Program Files\nodejs\node.exe" (
    set "NODE_EXE=C:\Program Files\nodejs\node.exe"
    set "USE_NODE=1"
) else if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe" (
    set "NODE_EXE=%LOCALAPPDATA%\Programs\nodejs\node.exe"
    set "USE_NODE=1"
)

if "%USE_NODE%"=="1" (
    echo [B2B] Modo: Node.js
    start "" /min "%NODE_EXE%" "%APP_DIR%server.js"
) else (
    echo [B2B] Modo: PowerShell nativo
    start "" powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "%APP_DIR%server.ps1"
)

:: Aguardar o servidor subir (ate 15 segundos)
set /a tentativas=0
:aguardar
set /a tentativas=%tentativas%+1
if %tentativas% GTR 15 goto timeout_msg
timeout /t 1 /nobreak >nul
curl -s --connect-timeout 1 http://localhost:8777/ >nul 2>&1
if %errorlevel% NEQ 0 goto aguardar

echo [B2B] Servidor iniciado com sucesso em http://localhost:8777
start "" msedge "http://localhost:8777/"
exit /b 0

:timeout_msg
echo [B2B] Servidor pode estar finalizando inicializacao...
start "" msedge "http://localhost:8777/"
exit /b 0
