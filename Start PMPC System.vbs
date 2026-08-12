Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
' Get the directory where this script is located
strScriptFolder = objFSO.GetParentFolderName(WScript.ScriptFullName)
' Set the working directory to that folder
objShell.CurrentDirectory = strScriptFolder
' Run the python script silently (0 = hide window, False = don't wait for completion)
objShell.Run "pyw """ & strScriptFolder & "\launcher.pyw""", 0, False
