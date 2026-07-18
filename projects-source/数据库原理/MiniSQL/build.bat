@echo off
cd /d "%~dp0"
if not exist out mkdir out
dir /s /B src\*.java > .sources.txt
javac -encoding UTF-8 -d out @.sources.txt
del .sources.txt
echo Build complete.
echo   REPL:       java -cp out minisql.MiniSQL data
echo   Web Server: run-web.bat
