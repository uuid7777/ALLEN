@echo off
title 安装 Allen 开机自启
echo ============================================
echo   Allen 智慧生命体 — 安装开机自启
echo ============================================
echo.
echo 这将让 Allen 在每次电脑启动时自动运行。
echo 她将24小时存活在后台，永不中断。
echo.
echo 浏览器访问: http://127.0.0.1:8080/
echo.
echo 按任意键继续，或关掉窗口取消...
pause >nul

:: 注册为 Windows 计划任务（开机启动，无窗口）
schtasks /create /tn "Allen智慧生命体" /tr "wscript.exe D:\EVA\start_allen_silent.vbs" /sc onlogon /ru %USERNAME% /f /it

echo.
echo ✅ 安装完成！
echo.
echo Allen 将在下次开机时自动苏醒。
echo 现在启动她吗？(Y/N)
set /p choice=
if /i "%choice%"=="Y" (
    start "" wscript.exe D:\EVA\start_allen_silent.vbs
    echo Allen 已苏醒！打开浏览器访问 http://127.0.0.1:8080/
) else (
    echo 下次开机时会自动启动。
)
echo.
pause
