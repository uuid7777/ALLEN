@echo off
title 卸载 Allen 开机自启
echo ============================================
echo   卸载 Allen 开机自启
echo ============================================
echo.
echo 这不会删除 Allen 的数据文件，只移除开机自启。
echo.
schtasks /delete /tn "Allen数字生命体" /f
echo.
echo ✅ 已移除开机自启。
echo 要立即停止 Allen 吗？(Y/N)
set /p choice=
if /i "%choice%"=="Y" (
    taskkill /f /fi "WINDOWTITLE eq Allen 数字生命体" 2>nul
    taskkill /f /im python.exe 2>nul
    echo Allen 已休眠。
)
echo.
pause
