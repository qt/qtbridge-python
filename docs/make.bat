:: Copyright (C) 2026 The Qt Company Ltd.
:: SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

@ECHO OFF

REM TODO: This batch file is yet to be tested on Windows

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
    set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=.
set BUILDDIR=_build
set EXAMPLESDIR=..\examples

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
    echo.
    echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
    echo.installed, then set the SPHINXBUILD environment variable to point
    echo.to the full path of the 'sphinx-build' executable.
    exit /b 1
)

if "%1" == "" goto help
if "%1" == "clean" goto clean

REM Copy example READMEs before building
call :copy_examples
%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:clean
call :clean_examples
%SPHINXBUILD% -M clean %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:copy_examples
echo Copying example READMEs...
if not exist examples mkdir examples
for /D %%D in ("%EXAMPLESDIR%\*") do (
    if exist "%%D\README.md" (
        if not exist "examples\%%~nD" mkdir "examples\%%~nD"
        copy /Y "%%D\README.md" "examples\%%~nD\" >NUL 2>NUL
    )
)
goto :eof

:clean_examples
echo Cleaning copied example READMEs...
if exist examples (
    for /D %%D in (examples\*) do (
        rmdir /S /Q "%%D"
    )
)
goto :eof

:end
popd
