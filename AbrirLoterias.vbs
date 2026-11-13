' =====================================================================
' B2B Loterias - Launcher Oficial v6.8
' Inicializacao direta na maquina licenciada + Auto-Recuperacao
' =====================================================================
Option Explicit

Dim sh, fso
Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Dim APP_DIR
APP_DIR = fso.GetParentFolderName(WScript.ScriptFullName)
Const PORTA = 8777
Const SENHA = "130767"

' -- 1. VERIFICAR LICENCA --
Dim pc, licenciada
pc = UCase(sh.ExpandEnvironmentStrings("%COMPUTERNAME%"))
licenciada = False

If pc = "LUISB2B" Or pc = "DESKTOP-H0KO4PH" Then
    licenciada = True
Else
    Dim lp
    lp = APP_DIR & "\licenca.key"
    If Not fso.FileExists(lp) Then
        MsgBox "LICENCA NAO ENCONTRADA!" & vbCrLf & vbCrLf & "Maquina: " & pc, vbCritical, "B2B Loterias"
        WScript.Quit
    End If
    Dim f, txt, arr, ln, comp
    comp = ""
    Set f = fso.OpenTextFile(lp, 1)
    txt = f.ReadAll
    f.Close
    txt = Replace(txt, vbCrLf, vbLf)
    txt = Replace(txt, vbCr, vbLf)
    arr = Split(txt, vbLf)
    For Each ln In arr
        If Left(ln, 11) = "Computador=" Then comp = Trim(Mid(ln, 12))
    Next
    If UCase(comp) <> pc Then
        MsgBox "Licenca invalida!" & vbCrLf & "Licenca: " & comp & vbCrLf & "Maquina: " & pc, vbCritical, "B2B Loterias"
        WScript.Quit
    End If
    licenciada = True
End If

' -- 2. PEDIR SENHA APENAS FORA DA MAQUINA PRINCIPAL DO PROPRIETARIO --
If pc <> "LUISB2B" And pc <> "DESKTOP-H0KO4PH" Then
    Dim senhaCorreta, tent, s
    senhaCorreta = False
    For tent = 1 To 3
        s = InputBox("ACESSO PROTEGIDO" & vbCrLf & vbCrLf & _
            "Maquina: " & pc & vbCrLf & vbCrLf & _
            "Digite a senha:" & vbCrLf & _
            "Tentativa " & tent & " de 3", "B2B Loterias")
        If IsEmpty(s) Then WScript.Quit
        If s = SENHA Then
            senhaCorreta = True
            Exit For
        End If
        If tent < 3 Then MsgBox "Senha incorreta! Restam " & (3 - tent) & " tentativa(s).", vbExclamation, "B2B Loterias"
    Next
    If Not senhaCorreta Then
        MsgBox "Acesso bloqueado!", vbCritical, "B2B Loterias"
        WScript.Quit
    End If
End If

' -- 3. GARANTIR SERVIDOR RODANDO --
If Not ServidorAtivo() Then
    Dim psScript
    psScript = APP_DIR & "\server.ps1"
    If fso.FileExists(psScript) Then
        On Error Resume Next
        sh.CurrentDirectory = APP_DIR
        Dim psExe : psExe = sh.ExpandEnvironmentStrings("%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe")
        sh.Run Chr(34) & psExe & Chr(34) & " -WindowStyle Hidden -ExecutionPolicy Bypass -File " & Chr(34) & psScript & Chr(34), 0, False
        On Error GoTo 0
        Dim w
        For w = 1 To 30
            WScript.Sleep 250
            If ServidorAtivo() Then Exit For
        Next
    End If
End If

' -- 4. GARANTIR API PYTHON RODANDO (SE DISPONIVEL) --
On Error Resume Next
Dim pyW, pyCands, pyCand, apiPy, esperaApi
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
apiPy = APP_DIR & "\api.py"
If fso.FileExists(apiPy) Then
    If Not Porta8000Ativa() Then
        sh.CurrentDirectory = APP_DIR
        If InStr(pyW, "\") > 0 Then
            sh.Run Chr(34) & pyW & Chr(34) & " " & Chr(34) & apiPy & Chr(34), 0, False
        Else
            sh.Run pyW & " " & Chr(34) & apiPy & Chr(34), 0, False
        End If
        For esperaApi = 1 To 24
            WScript.Sleep 250
            If Porta8000Ativa() Then Exit For
        Next
    End If
End If
On Error GoTo 0

' -- 5. ABRIR NAVEGADOR EM MODO APP --
On Error Resume Next
Dim nav, k
nav = AcharNavegador()
If nav <> "" Then
    sh.Run Chr(34) & nav & Chr(34) & " --app=" & Chr(34) & "http://localhost:" & PORTA & "/" & Chr(34), 1, False
    For k = 1 To 8
        WScript.Sleep 300
        If sh.AppActivate("B2B Loterias") Then Exit For
    Next
Else
    sh.Run "cmd /c start """" " & Chr(34) & "http://localhost:" & PORTA & "/" & Chr(34), 0, False
End If
On Error GoTo 0

Set sh = Nothing
Set fso = Nothing
WScript.Quit

' =================== FUNCOES ===================

Function ServidorAtivo()
    ServidorAtivo = False
    Dim h
    On Error Resume Next
    Set h = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    h.setTimeouts 800, 800, 800, 1500
    h.Open "GET", "http://localhost:" & PORTA & "/index.html", False
    h.Send
    If Err.Number = 0 Then
        If h.Status = 200 Then ServidorAtivo = True
    End If
    Set h = Nothing
    Err.Clear
    On Error GoTo 0
End Function

Function Porta8000Ativa()
    Porta8000Ativa = False
    Dim h
    On Error Resume Next
    Set h = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    h.setTimeouts 300, 300, 300, 500
    h.Open "GET", "http://127.0.0.1:8000/health", False
    h.Send
    If Err.Number = 0 Then
        If h.Status = 200 Then Porta8000Ativa = True
    End If
    Set h = Nothing
    Err.Clear
    On Error GoTo 0
End Function

Function AcharNavegador()
    AcharNavegador = ""
    Dim caminhos, p
    caminhos = Array( _
        "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", _
        "C:\Program Files\Microsoft\Edge\Application\msedge.exe", _
        sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"), _
        "C:\Program Files\Google\Chrome\Application\chrome.exe", _
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", _
        sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"))
    For Each p In caminhos
        If fso.FileExists(p) Then
            AcharNavegador = p
            Exit Function
        End If
    Next
End Function
