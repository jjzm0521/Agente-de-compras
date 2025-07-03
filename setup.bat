@echo off
setlocal

REM Define el nombre del directorio del entorno virtual
set VENV_DIR=.venv

echo Verificando instalacion de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python no parece estar instalado o no esta en el PATH.
    echo Por favor, instala Python (version 3.6 o superior) y asegurate de que este anadido al PATH.
    goto :eof
)
echo Python encontrado.

echo Verificando instalacion de Pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Pip no parece estar instalado. Pip es necesario para instalar las dependencias.
    echo Asegurate de que Python y Pip esten correctamente instalados.
    goto :eof
)
echo Pip encontrado.

REM Verifica si el directorio del entorno virtual existe
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creando entorno virtual en '%VENV_DIR%'...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo Error: No se pudo crear el entorno virtual.
        goto :eof
    )
    echo Entorno virtual creado.
) else (
    echo Entorno virtual '%VENV_DIR%' ya existe.
)

REM Activa el entorno virtual
echo Activando entorno virtual...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo Error: No se pudo activar el entorno virtual.
    goto :eof
)

REM Instala las dependencias desde requirements.txt
echo Instalando dependencias desde requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: No se pudieron instalar todas las dependencias desde requirements.txt.
    echo Revisa el output anterior para mas detalles.
    REM No desactivamos el venv aqui para que el usuario pueda intentar arreglarlo manualmente.
    goto :eof
)

echo.
echo ---------------------------------------------------------------------
echo  Configuracion completada exitosamente!
echo ---------------------------------------------------------------------
echo.
echo El entorno virtual '%VENV_DIR%' esta activo en esta ventana de comandos.
echo Las dependencias de 'requirements.txt' han sido instaladas.
echo.
echo Si abres una nueva ventana de comandos, recuerda activar el entorno con:
echo   %VENV_DIR%\Scripts\activate.bat
echo.
echo Para desactivar el entorno en esta ventana, simplemente escribe:
echo   deactivate
echo.

endlocal
goto :eof

:eof
echo.
echo El script de configuracion ha finalizado con errores o ha sido interrumpido.
pause
