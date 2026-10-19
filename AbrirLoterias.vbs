' =====================================================================
' B2B Loterias — Launcher Ultra-Leve v6.1
' Senha + Servidor + Chrome — sequencia garantida
' =====================================================================
Option Explicit

Dim sh, fso
Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Dim APP_DIR
APP_DIR = fso.GetParentFolderName(WScript.ScriptFullName)
Const PORTA   = 8777
Const SENHA   = "130767"

' ── 1. VERIFICAR LICENCA ──
Dim pc
pc = UCase(sh.ExpandEnvironmentStrings("%COMPUTERNAME%"))

If pc <> "LUISB2B" Then
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
End If

' ── 2. PEDIR SENHA (3 tentativas) ──
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

' ── 3. GARANTIR SERVIDOR RODANDO ──
If Not ServidorAtivo() Then
    Dim psScript
    psScript = APP_DIR & "\server.ps1"
    If fso.FileExists(psScript) Then
        On Error Resume Next
        Dim wmi, proc, res
        Set wmi = GetObject("winmgmts:\\.\root\cimv2:Win32_Process")
        res = wmi.Create("powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & psScript & """", APP_DIR, Null, proc)
        If Err.Number <> 0 Or res <> 0 Then
            sh.Run "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & psScript & """", 0, False
        End If
        On Error GoTo 0
        Dim w
        For w = 1 To 25
            WScript.Sleep 300
            If ServidorAtivo() Then Exit For
        Next
    End If
End If

' ── 4. DELAY DE SEGURANCA + ABRIR NAVEGADOR EM MODO APP ──
WScript.Sleep 500

Dim nav
nav = AcharNavegador()
On Error Resume Next
If nav <> "" Then
    sh.Run """" & nav & """ --app=""http://localhost:" & PORTA & "/""", 1, False
Else
    ' Fallback padrao
    sh.Run "cmd /c start msedge ""http://localhost:" & PORTA & "/""", 0, False
End If
On Error GoTo 0

Set sh = Nothing
Set fso = Nothing
WScript.Quit

' ═══════════════════ FUNCOES ═══════════════════

Function ServidorAtivo()
    ServidorAtivo = False
    Dim h
    On Error Resume Next
    Set h = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    h.setTimeouts 500, 500, 500, 1000
    h.Open "GET", "http://localhost:" & PORTA & "/", False
    h.Send
    If Err.Number = 0 Then
        If h.Status >= 200 And h.Status < 400 Then ServidorAtivo = True
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
