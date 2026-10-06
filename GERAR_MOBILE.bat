@echo off
echo ============================================
echo   B2B Loterias - Gerando Versao Mobile...
echo ============================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0GERAR_MOBILE.ps1"
