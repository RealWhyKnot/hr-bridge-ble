' Starts the bridge at logon with no console window.
' Put a shortcut to this file in shell:startup. It looks for hr-bridge-ble.exe
' or a .venv beside itself, then one folder up.
Set fso = CreateObject("Scripting.FileSystemObject")
here = fso.GetParentFolderName(WScript.ScriptFullName)
cmdline = Launcher(here)
If cmdline = "" Then cmdline = Launcher(fso.GetParentFolderName(here))
If cmdline = "" Then
  WScript.Echo "hr-bridge-ble: no hr-bridge-ble.exe and no .venv in " & here & " or its parent."
  WScript.Quit 1
End If
CreateObject("WScript.Shell").Run cmdline, 0, False

Function Launcher(folder)
  Launcher = ""
  If folder = "" Then Exit Function
  exePath = fso.BuildPath(folder, "hr-bridge-ble.exe")
  If fso.FileExists(exePath) Then
    Launcher = """" & exePath & """ --quiet"
    Exit Function
  End If
  pythonw = fso.BuildPath(folder, ".venv\Scripts\pythonw.exe")
  If fso.FileExists(pythonw) Then
    Launcher = """" & pythonw & """ -m hr_bridge_ble --quiet"
  End If
End Function
