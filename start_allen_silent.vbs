' Allen 数字生命体 — 静默后台启动脚本
' 双击运行，无控制台窗口，开机自启用这个
Dim shell
Set shell = CreateObject("WScript.Shell")
shell.Run "pythonw.exe D:\EVA\chat_server.py", 0, False
Set shell = Nothing
