' Starts the bridge at logon with no console window.
' Put a shortcut to this file in shell:startup, and keep the file next to the .exe or the .venv.
Set fso = CreateObject("Scripting.FileSystemObject")
here = fso.GetParentFolderName(WScript.ScriptFullName)
exePath = fso.BuildPath(here, "hr-bridge-ble.exe")
If fso.FileExists(exePath) Then
  CreateObject("WScript.Shell").Run """" & exePath & """ --quiet", 0, False
Else
  CreateObject("WScript.Shell").Run """" & fso.BuildPath(here, ".venv\Scripts\pythonw.exe") & """ -m hr_bridge_ble --quiet", 0, False
End If
