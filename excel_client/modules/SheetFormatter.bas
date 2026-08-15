Attribute VB_Name = "SheetFormatter"
Option Explicit

' ==============================================================================
' Module: SheetFormatter.bas
' Description: Styling routines for HSBC Product Control workbooks
' ==============================================================================

Public Sub FormatControlTable(ws As Worksheet, startRow As Long, rowCount As Long)
    Dim rng As Range
    If rowCount <= 0 Then Exit Sub
    
    Set rng = ws.Range(ws.Cells(startRow, 1), ws.Cells(startRow + rowCount, 7))
    
    ' Header Style
    With ws.Range(ws.Cells(startRow, 1), ws.Cells(startRow, 7))
        .Font.Bold = True
        .Font.Color = RGB(255, 255, 255)
        .Interior.Color = RGB(219, 0, 17) ' HSBC Red
        .HorizontalAlignment = xlCenter
    End With
    
    ' Borders
    rng.Borders.LineStyle = xlContinuous
    rng.Borders.Color = RGB(200, 200, 200)
    
    ws.Columns("A:G").AutoFit
End Sub

Public Sub FormatExceptionsTable(ws As Worksheet, rowCount As Long)
    Dim rng As Range
    If rowCount <= 0 Then Exit Sub
    
    Set rng = ws.Range(ws.Cells(1, 1), ws.Cells(1 + rowCount, 9))
    
    ' Header Style
    With ws.Range(ws.Cells(1, 1), ws.Cells(1, 9))
        .Font.Bold = True
        .Font.Color = RGB(255, 255, 255)
        .Interior.Color = RGB(178, 34, 34) ' Dark Crimson
        .HorizontalAlignment = xlCenter
    End With
    
    ' Borders
    rng.Borders.LineStyle = xlContinuous
    rng.Borders.Color = RGB(210, 210, 210)
    
    ws.Columns("A:I").AutoFit
End Sub

Public Sub FormatHistoryTable(ws As Worksheet, rowCount As Long)
    Dim rng As Range
    If rowCount <= 0 Then Exit Sub
    
    Set rng = ws.Range(ws.Cells(1, 1), ws.Cells(1 + rowCount, 8))
    
    ' Header Style
    With ws.Range(ws.Cells(1, 1), ws.Cells(1, 8))
        .Font.Bold = True
        .Font.Color = RGB(255, 255, 255)
        .Interior.Color = RGB(50, 50, 50) ' Slate Charcoal
        .HorizontalAlignment = xlCenter
    End With
    
    rng.Borders.LineStyle = xlContinuous
    rng.Borders.Color = RGB(220, 220, 220)
    
    ws.Columns("A:H").AutoFit
End Sub
