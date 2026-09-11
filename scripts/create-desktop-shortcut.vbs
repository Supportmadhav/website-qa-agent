Option Explicit

Dim shell
Dim fso
Dim scriptFolder
Dim projectRoot
Dim desktop
Dim shortcutPath
Dim targetPath
Dim shortcut

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptFolder = fso.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(scriptFolder)

targetPath = projectRoot & "\Start Website QA Agent.bat"

If Not fso.FileExists(targetPath) Then
    WScript.Echo "ERROR: Start Website QA Agent.bat was not found:"
    WScript.Echo targetPath
    WScript.Quit 1
End If

desktop = shell.SpecialFolders("Desktop")
shortcutPath = desktop & "\Website QA Agent.lnk"

Set shortcut = shell.CreateShortcut(shortcutPath)

shortcut.TargetPath = targetPath
shortcut.WorkingDirectory = projectRoot
shortcut.Description = "Start Website QA Agent"
shortcut.WindowStyle = 7
shortcut.Save

WScript.Echo "Desktop shortcut created successfully."
WScript.Echo ""
WScript.Echo shortcutPath
WScript.Echo ""
WScript.Echo "From now on, double-click Website QA Agent on your Desktop."

WScript.Quit 0
