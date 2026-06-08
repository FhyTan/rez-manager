@echo off
setlocal

set BUILD_DIR=build
set SCRIPTS_DIR=build_scripts

echo ===== Building rez-manager =====
uv run nuitka --output-dir=%BUILD_DIR% %SCRIPTS_DIR%\rez-manager.py
if errorlevel 1 (
    echo ERROR: rez-manager build failed.
    exit /b 1
)

echo.
echo ===== Checking rez-pkg-cache =====
if exist "%BUILD_DIR%\rez-pkg-cache.dist\rez-pkg-cache.exe" (
    echo rez-pkg-cache.exe already exists, skipping build.
) else (
    echo Building rez-pkg-cache...
    uv run nuitka --output-dir=%BUILD_DIR% %SCRIPTS_DIR%\rez-pkg-cache.py
    if errorlevel 1 (
        echo ERROR: rez-pkg-cache build failed.
        exit /b 1
    )
)

echo.
echo ===== Copying rez-pkg-cache.exe to rez-manager dist =====
copy "%BUILD_DIR%\rez-pkg-cache.dist\rez-pkg-cache.exe" "%BUILD_DIR%\rez-manager.dist\" /y
if errorlevel 1 (
    echo ERROR: Failed to copy rez-pkg-cache.exe.
    exit /b 1
)

echo.
echo ===== Build complete! =====
echo Output: %BUILD_DIR%\rez-manager.dist\rez-manager.exe
echo Cache:  %BUILD_DIR%\rez-manager.dist\rez-pkg-cache.exe
