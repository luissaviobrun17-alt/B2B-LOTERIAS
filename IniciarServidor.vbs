' =====================================================================
' B2B Loterias — Servidor Silencioso v6.3
' 100% invisivel, sem pop-ups, execucao desacoplada via WMI / PowerShell
' =====================================================================
Option Explicit

Dim sh, fso
Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Dim APP_DIR
APP_DIR = fso.GetParentFolderName(WScript.ScriptFullName)
Const PORTA = 8777

' Testar se ja esta rodando
Dim h, rodando : rodando = False
On Error Resume Next
Set h = CreateObject("MSXML2.ServerXMLHTTP.6.0")
h.setTimeouts 2000, 2000, 2000, 2000
h.Open "GET", "http://localhost:" & PORTA & "/", False
h.Send
If Err.Number = 0 And h.Status >= 200 And h.Status < 400 Then rodando = True
Set h = Nothing : Err.Clear
On Error GoTo 0

If rodando Then WScript.Quit

' Localizar Node.js se existir
Dim nd : nd = ""
Dim caminhos : caminhos = Array( _
    "C:\Program Files\nodejs\node.exe", _
    sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\nodejs\node.exe"))
Dim p
For Each p In caminhos
    If fso.FileExists(p) Then
        nd = """" & p & """"
        Exit For
    End If
Next

If nd <> "" Then
    Dim sj : sj = APP_DIR & "\server.js"
    If fso.FileExists(sj) Then
        sh.Run nd & " """ & sj & """", 0, False
        WScript.Quit
    End If
End If

' Fallback confiavel para PowerShell nativo server.ps1 (desacoplado via WMI)
Dim sp : sp = APP_DIR & "\server.ps1"
If fso.FileExists(sp) Then
    On Error Resume Next
    Dim wmi, proc, res
    Set wmi = GetObject("winmgmts:\\.\root\cimv2:Win32_Process")
    res = wmi.Create("powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & sp & """", Null, Null, proc)
    If Err.Number <> 0 Or res <> 0 Then
        sh.Run "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & sp & """", 0, False
    End If
    On Error GoTo 0
End If

WScript.Quit
