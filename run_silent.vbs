Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = scriptDir

' Launch with pythonw (hidden background) or fallback to python
WshShell.Run "cmd /c pythonw.exe main.py", 0, False
Set WshShell = Nothing
Set fso = Nothing
