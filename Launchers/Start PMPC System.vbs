Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
' Get the root directory
strScriptFolder = objFSO.GetParentFolderName(WScript.ScriptFullName)
strRootFolder = objFSO.GetParentFolderName(strScriptFolder)
' Set the working directory to the root folder
objShell.CurrentDirectory = strRootFolder
' Run the python script silently
objShell.Run "python """ & strRootFolder & "\launcher.pyw""", 0, False
