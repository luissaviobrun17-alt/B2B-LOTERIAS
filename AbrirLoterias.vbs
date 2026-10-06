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
        res = wmi.Create("powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & psScript & """", Null, Null, proc)
        If Err.Number <> 0 Or res <> 0 Then
            sh.Run "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & psScript & """", 0, False
        End If
        On Error GoTo 0
        Dim w
        For w = 1 To 50
            WScript.Sleep 300
            If ServidorAtivo() Then Exit For
        Next
    End If
End If

' ── 4. DELAY DE SEGURANCA + ABRIR CHROME ──
WScript.Sleep 800

Dim cr
cr = AcharEdge()
On Error Resume Next
If cr <> "" Then
    sh.Run """" & cr & """ --app=""http://localhost:" & PORTA & "/""", 1, False
Else
    ' Edge nao encontrado — abre no Edge pelo protocolo mesmo assim
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
    h.setTimeouts 2000, 2000, 2000, 2000
    h.Open "GET", "http://localhost:" & PORTA & "/", False
    h.Send
    If Err.Number = 0 Then
        If h.Status >= 200 And h.Status < 400 Then ServidorAtivo = True
    End If
    Set h = Nothing
    Err.Clear
    On Error GoTo 0
End Function

Function AcharNode()
    AcharNode = ""
    Dim localNode
    localNode = APP_DIR & "\node.exe"
    If fso.FileExists(localNode) Then
        AcharNode = """" & localNode & """"
        Exit Function
    End If
    Dim caminhos, p
    caminhos = Array( _
        "C:\Program Files\nodejs\node.exe", _
        sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\nodejs\node.exe"))
    For Each p In caminhos
        If fso.FileExists(p) Then
            AcharNode = """" & p & """"
            Exit Function
        End If
    Next
    AcharNode = "node.exe"
End Function

Function AcharEdge()
    AcharEdge = ""
    Dim caminhos, p
    caminhos = Array( _
        "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", _
        "C:\Program Files\Microsoft\Edge\Application\msedge.exe")
    For Each p In caminhos
        If fso.FileExists(p) Then
            AcharEdge = p
            Exit Function
        End If
    Next
End Function
