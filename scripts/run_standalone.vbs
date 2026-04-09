Set fso = CreateObject("Scripting.FileSystemObject")
repoRoot = fso.GetAbsolutePathName(fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), ".."))
exePath = fso.BuildPath(repoRoot, "dist\FoundryDesktop.exe")
pywPath = fso.BuildPath(repoRoot, ".venv\Scripts\pythonw.exe")

Set shell = CreateObject("WScript.Shell")

If fso.FileExists(pywPath) Then
    shell.Run Chr(34) & pywPath & Chr(34) & " -m foundry.desktop.app", 0, False
    WScript.Quit 0
End If

If Not fso.FileExists(exePath) Then
    MsgBox "Neither pythonw launcher nor FoundryDesktop.exe found. Build first with scripts\\build_standalone.ps1", 48, "Celonis Delivery Forge"
    WScript.Quit 1
End If

shell.Run Chr(34) & exePath & Chr(34), 0, False
