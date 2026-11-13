' =====================================================================
' B2B Loterias - Servidor Silencioso v6.5
' 100% invisivel, sem pop-ups, execucao desacoplada e auto-recuperavel
' =====================================================================
Option Explicit

Dim sh, fso
Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Dim APP_DIR
APP_DIR = fso.GetParentFolderName(WScript.ScriptFullName)
Const PORTA = 8777

' 1. Testar se servidor web (8777) ja esta rodando
Dim h, rodando : rodando = False
On Error Resume Next
Set h = CreateObject("MSXML2.ServerXMLHTTP.6.0")
h.setTimeouts 800, 800, 800, 800
h.Open "GET", "http://localhost:" & PORTA & "/", False
h.Send
If Err.Number = 0 Then
    If h.Status >= 200 And h.Status < 400 Then rodando = True
End If
Set h = Nothing
Err.Clear
On Error GoTo 0

If Not rodando Then
    Dim iniciado8777 : iniciado8777 = False

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
            sh.CurrentDirectory = APP_DIR
            sh.Run nd & " """ & sj & """", 0, False
            iniciado8777 = True
        End If
    End If

    ' Fallback confiavel para PowerShell nativo server.ps1
    If Not iniciado8777 Then
        Dim sp : sp = APP_DIR & "\server.ps1"
        If fso.FileExists(sp) Then
            On Error Resume Next
            sh.CurrentDirectory = APP_DIR
            Dim psExe : psExe = sh.ExpandEnvironmentStrings("%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe")
            sh.Run Chr(34) & psExe & Chr(34) & " -WindowStyle Hidden -ExecutionPolicy Bypass -File " & Chr(34) & sp & Chr(34), 0, False
            On Error GoTo 0
        End If
    End If
End If

' 2. Garantir API matematica Python (porta 8000)
GarantirApiPython

WScript.Quit

Sub GarantirApiPython()
    On Error Resume Next
    Dim apiPy
    apiPy = APP_DIR & "\api.py"
    If Not fso.FileExists(apiPy) Then
        On Error GoTo 0
        Exit Sub
    End If
    If Porta8000Ativa() Then
        On Error GoTo 0
        Exit Sub
    End If

    Dim pyW, pyCands, pyCand
    pyW = ""
    pyCands = Array( _
        sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"), _
        sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"), _
        sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"), _
        "C:\Python312\pythonw.exe", _
        "C:\Program Files\Python312\pythonw.exe")
    For Each pyCand In pyCands
        If fso.FileExists(pyCand) Then
            pyW = pyCand
            Exit For
        End If
    Next
    If pyW = "" Then pyW = "pythonw.exe"

    sh.CurrentDirectory = APP_DIR
    If InStr(pyW, "\") > 0 Then
        sh.Run Chr(34) & pyW & Chr(34) & " " & Chr(34) & apiPy & Chr(34), 0, False
    Else
        sh.Run pyW & " " & Chr(34) & apiPy & Chr(34), 0, False
    End If
    On Error GoTo 0
End Sub

Function Porta8000Ativa()
    Porta8000Ativa = False
    Dim hApi
    On Error Resume Next
    Set hApi = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    hApi.setTimeouts 500, 500, 500, 500
    hApi.Open "GET", "http://127.0.0.1:8000/health", False
    hApi.Send
    If Err.Number = 0 Then
        If hApi.Status = 200 Then Porta8000Ativa = True
    End If
    Set hApi = Nothing
    Err.Clear
    On Error GoTo 0
End Function
