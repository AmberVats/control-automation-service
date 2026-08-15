Attribute VB_Name = "JsonConverter"
Option Explicit

' ==============================================================================
' VBA-JSON v2.3.1 (Stripped / Core Engine)
' Parses JSON strings into native VBA Collection and Dictionary structures.
' ==============================================================================

Public Function ParseJson(ByVal JsonString As String) As Object
    Dim Index As Long
    Index = 1
    JsonString = Trim(JsonString)
    
    SkipWhitespace JsonString, Index
    If Mid$(JsonString, Index, 1) = "{" Then
        Set ParseJson = ParseObject(JsonString, Index)
    ElseIf Mid$(JsonString, Index, 1) = "[" Then
        Set ParseJson = ParseArray(JsonString, Index)
    Else
        Err.Raise 10001, "JsonConverter", "Invalid JSON starting character: " & Mid$(JsonString, Index, 1)
    End If
End Function

Private Function ParseObject(ByVal json As String, ByRef Index As Long) As Object
    Dim dict As Object
    Dim Key As String
    Dim Val As Object
    
    Set dict = CreateObject("Scripting.Dictionary")
    Index = Index + 1 ' Skip {
    
    Do
        SkipWhitespace json, Index
        If Mid$(json, Index, 1) = "}" Then
            Index = Index + 1
            Exit Do
        End If
        
        Key = ParseString(json, Index)
        SkipWhitespace json, Index
        
        If Mid$(json, Index, 1) <> ":" Then
            Err.Raise 10002, "JsonConverter", "Expected ':' at position " & Index
        End If
        Index = Index + 1 ' Skip :
        
        SkipWhitespace json, Index
        dict.Add Key, ParseValue(json, Index)
        
        SkipWhitespace json, Index
        If Mid$(json, Index, 1) = "," Then
            Index = Index + 1
        ElseIf Mid$(json, Index, 1) = "}" Then
            Index = Index + 1
            Exit Do
        End If
    Loop
    
    Set ParseObject = dict
End Function

Private Function ParseArray(ByVal json As String, ByRef Index As Long) As Object
    Dim col As Collection
    Set col = New Collection
    Index = Index + 1 ' Skip [
    
    Do
        SkipWhitespace json, Index
        If Mid$(json, Index, 1) = "]" Then
            Index = Index + 1
            Exit Do
        End If
        
        col.Add ParseValue(json, Index)
        
        SkipWhitespace json, Index
        If Mid$(json, Index, 1) = "," Then
            Index = Index + 1
        ElseIf Mid$(json, Index, 1) = "]" Then
            Index = Index + 1
            Exit Do
        End If
    Loop
    
    Set ParseArray = col
End Function

Private Function ParseValue(ByVal json As String, ByRef Index As Long) As Variant
    SkipWhitespace json, Index
    Select Case Mid$(json, Index, 1)
        Case "{"
            Set ParseValue = ParseObject(json, Index)
        Case "["
            Set ParseValue = ParseArray(json, Index)
        Case """"
            ParseValue = ParseString(json, Index)
        Case "t", "T"
            ParseValue = True
            Index = Index + 4
        Case "f", "F"
            ParseValue = False
            Index = Index + 5
        Case "n", "N"
            ParseValue = Null
            Index = Index + 4
        Case Else
            ParseValue = ParseNumber(json, Index)
    End Select
End Function

Private Function ParseString(ByVal json As String, ByRef Index As Long) As String
    Dim endPos As Long
    Index = Index + 1 ' Skip open quote
    endPos = InStr(Index, json, """")
    If endPos = 0 Then
        Err.Raise 10003, "JsonConverter", "Unterminated string at " & Index
    End If
    ParseString = Mid$(json, Index, endPos - Index)
    Index = endPos + 1
End Function

Private Function ParseNumber(ByVal json As String, ByRef Index As Long) As Variant
    Dim startPos As Long
    Dim ch As String
    startPos = Index
    Do While Index <= Len(json)
        ch = Mid$(json, Index, 1)
        If InStr("0123456789+-.eE", ch) > 0 Then
            Index = Index + 1
        Else
            Exit Do
        End If
    Loop
    ParseNumber = Val(Mid$(json, startPos, Index - startPos))
End Function

Private Sub SkipWhitespace(ByVal json As String, ByRef Index As Long)
    Do While Index <= Len(json)
        Select Case Mid$(json, Index, 1)
            Case " ", vbTab, vbCr, vbLf
                Index = Index + 1
            Case Else
                Exit Sub
        End Select
    Loop
End Sub
