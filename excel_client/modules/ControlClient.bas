Attribute VB_Name = "ControlClient"
Option Explicit

' ==============================================================================
' Global Markets Product Control Analytics - Control Automation Service Client
' Module: ControlClient.bas
' Description: REST API Client for executing financial controls and retrieving audit trails.
' ==============================================================================

Public Const BASE_API_URL As String = "http://localhost:8000"

Public Sub RefreshControlsList()
    Dim http As Object
    Dim url As String
    Dim jsonResponse As String
    Dim parsedControls As Object
    Dim ws As Worksheet
    Dim i As Long
    Dim ctrl As Object

    On Error GoTo ErrorHandler
    Application.ScreenUpdating = False

    Set ws = ThisWorkbook.Sheets("Control Panel")
    url = BASE_API_URL & "/api/v1/controls"

    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.Open "GET", url, False
    http.setRequestHeader "Content-Type", "application/json"
    http.setRequestHeader "Accept", "application/json"
    http.send

    If http.Status <> 200 Then
        MsgBox "Failed to fetch controls from service. HTTP Status: " & http.Status & vbCrLf & http.responseText, vbCritical, "API Error"
        Exit Sub
    End If

    jsonResponse = http.responseText
    Set parsedControls = JsonConverter.ParseJson(jsonResponse)

    ' Clear existing dropdown list area in Control Panel
    ws.Range("B6:B30").ClearContents
    ws.Range("A10:G50").ClearContents

    ' Populate Controls Table
    ws.Cells(10, 1).Value = "Control Name"
    ws.Cells(10, 2).Value = "Version"
    ws.Cells(10, 3).Value = "Component"
    ws.Cells(10, 4).Value = "Owner"
    ws.Cells(10, 5).Value = "Schedule"
    ws.Cells(10, 6).Value = "Enabled"
    ws.Cells(10, 7).Value = "Config Hash"

    For i = 1 To parsedControls.Count
        Set ctrl = parsedControls(i)
        ws.Cells(10 + i, 1).Value = ctrl("name")
        ws.Cells(10 + i, 2).Value = ctrl("version")
        ws.Cells(10 + i, 3).Value = ctrl("component")
        ws.Cells(10 + i, 4).Value = ctrl("owner")
        ws.Cells(10 + i, 5).Value = ctrl("schedule")
        ws.Cells(10 + i, 6).Value = ctrl("enabled")
        ws.Cells(10 + i, 7).Value = Left(ctrl("config_hash"), 12) & "..."
    Next i

    ' Set default selection
    If parsedControls.Count > 0 Then
        ws.Range("C4").Value = parsedControls(1)("name")
    End If

    FormatControlTable ws, 10, parsedControls.Count
    Application.ScreenUpdating = True
    MsgBox "Successfully refreshed " & parsedControls.Count & " controls from microservice.", vbInformation, "Controls Refreshed"
    Exit Sub

ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "Error communicating with Control Automation Service: " & Err.Description, vbCritical, "Connection Error"
End Sub

Public Sub RunSelectedControl()
    Dim http As Object
    Dim url As String
    Dim ws As Worksheet
    Dim controlName As String
    Dim asOfDate As String
    Dim payload As String
    Dim jsonResponse As String
    Dim result As Object
    Dim runId As String
    Dim status As String
    Dim breachCount As Long

    On Error GoTo ErrorHandler
    Set ws = ThisWorkbook.Sheets("Control Panel")
    controlName = Trim(ws.Range("C4").Value)
    asOfDate = Format(Date, "YYYY-MM-DD")

    If controlName = "" Then
        MsgBox "Please select or enter a control name to execute.", vbExclamation, "No Control Selected"
        Exit Sub
    End If

    url = BASE_API_URL & "/api/v1/controls/" & controlName & "/run"
    payload = "{""as_of_date"": """ & asOfDate & """, ""triggered_by"": ""excel_vba_client""}"

    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.Open "POST", url, False
    http.setRequestHeader "Content-Type", "application/json"
    http.send payload

    If http.Status <> 200 Then
        MsgBox "Control execution failed. HTTP Status: " & http.Status & vbCrLf & http.responseText, vbCritical, "Execution Error"
        Exit Sub
    End If

    jsonResponse = http.responseText
    Set result = JsonConverter.ParseJson(jsonResponse)

    runId = result("run_id")
    status = result("status")
    breachCount = result("breach_count")

    ' Update UI status cards
    ws.Range("F4").Value = status
    ws.Range("F5").Value = breachCount
    ws.Range("F6").Value = result("duration_ms") & " ms"
    ws.Range("F7").Value = runId

    ' Format Status indicator
    If status = "PASS" Then
        ws.Range("F4").Interior.Color = RGB(198, 239, 206) ' Light Green
        ws.Range("F4").Font.Color = RGB(0, 97, 0)
    ElseIf status = "BREACH" Then
        ws.Range("F4").Interior.Color = RGB(255, 199, 206) ' Light Red
        ws.Range("F4").Font.Color = RGB(156, 0, 6)
    Else
        ws.Range("F4").Interior.Color = RGB(255, 235, 156) ' Yellow
        ws.Range("F4").Font.Color = RGB(156, 101, 0)
    End If

    ' If breaches detected, fetch exceptions automatically
    If breachCount > 0 Then
        FetchExceptionsForRun runId
    Else
        ClearExceptionsSheet
    End If

    RefreshHistory
    MsgBox "Control execution complete." & vbCrLf & "Status: " & status & vbCrLf & "Breaches: " & breachCount, vbInformation, "Run Completed"
    Exit Sub

ErrorHandler:
    MsgBox "Error running control: " & Err.Description, vbCritical, "Execution Error"
End Sub

Public Sub FetchExceptionsForRun(ByVal runId As String)
    Dim http As Object
    Dim url As String
    Dim jsonResponse As String
    Dim resObj As Object
    Dim excList As Object
    Dim ws As Worksheet
    Dim i As Long
    Dim exc As Object

    Set ws = ThisWorkbook.Sheets("Exceptions")
    url = BASE_API_URL & "/api/v1/runs/" & runId & "/exceptions?limit=500"

    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.Open "GET", url, False
    http.setRequestHeader "Accept", "application/json"
    http.send

    If http.Status <> 200 Then Exit Sub

    jsonResponse = http.responseText
    Set resObj = JsonConverter.ParseJson(jsonResponse)
    Set excList = resObj("exceptions")

    ws.Cells.Clear

    ' Exception Sheet Headers
    ws.Cells(1, 1).Value = "Exception ID"
    ws.Cells(1, 2).Value = "Run ID"
    ws.Cells(1, 3).Value = "Type"
    ws.Cells(1, 4).Value = "Key Data"
    ws.Cells(1, 5).Value = "Field"
    ws.Cells(1, 6).Value = "Source Value"
    ws.Cells(1, 7).Value = "Target Value"
    ws.Cells(1, 8).Value = "Difference"
    ws.Cells(1, 9).Value = "Message"

    For i = 1 To excList.Count
        Set exc = excList(i)
        ws.Cells(1 + i, 1).Value = exc("id")
        ws.Cells(1 + i, 2).Value = exc("run_id")
        ws.Cells(1 + i, 3).Value = exc("exception_type")
        ws.Cells(1 + i, 4).Value = exc("key_data")
        ws.Cells(1 + i, 5).Value = exc("field")
        ws.Cells(1 + i, 6).Value = exc("source_val")
        ws.Cells(1 + i, 7).Value = exc("target_val")
        ws.Cells(1 + i, 8).Value = exc("difference")
        ws.Cells(1 + i, 9).Value = exc("message")
    Next i

    FormatExceptionsTable ws, excList.Count
End Sub

Public Sub RefreshHistory()
    Dim http As Object
    Dim url As String
    Dim jsonResponse As String
    Dim runsList As Object
    Dim ws As Worksheet
    Dim i As Long
    Dim r As Object

    Set ws = ThisWorkbook.Sheets("Run History")
    url = BASE_API_URL & "/api/v1/runs?limit=50"

    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.Open "GET", url, False
    http.setRequestHeader "Accept", "application/json"
    http.send

    If http.Status <> 200 Then Exit Sub

    jsonResponse = http.responseText
    Set runsList = JsonConverter.ParseJson(jsonResponse)

    ws.Cells.Clear

    ws.Cells(1, 1).Value = "Run ID"
    ws.Cells(1, 2).Value = "Control Name"
    ws.Cells(1, 3).Value = "Version"
    ws.Cells(1, 4).Value = "Status"
    ws.Cells(1, 5).Value = "Breaches"
    ws.Cells(1, 6).Value = "Duration (ms)"
    ws.Cells(1, 7).Value = "Triggered By"
    ws.Cells(1, 8).Value = "Start Time"

    For i = 1 To runsList.Count
        Set r = runsList(i)
        ws.Cells(1 + i, 1).Value = r("run_id")
        ws.Cells(1 + i, 2).Value = r("control_name")
        ws.Cells(1 + i, 3).Value = r("version")
        ws.Cells(1 + i, 4).Value = r("status")
        ws.Cells(1 + i, 5).Value = r("breach_count")
        ws.Cells(1 + i, 6).Value = r("duration_ms")
        ws.Cells(1 + i, 7).Value = r("triggered_by")
        ws.Cells(1 + i, 8).Value = r("start_time")
    Next i

    FormatHistoryTable ws, runsList.Count
End Sub

Private Sub ClearExceptionsSheet()
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("Exceptions")
    ws.Cells.Clear
    ws.Cells(1, 1).Value = "No exceptions detected on last run (PASS)."
End Sub
