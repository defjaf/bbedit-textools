-- TeX Tools: menu attachment for #! → Run (⌘R).
-- On a TeX document, Run typesets (see RUN_MENU_MODE) instead of running the
-- file as a script; for every other document, BBEdit's normal Run proceeds.
-- Installed (and compiled) by bbedit-textools/install; @RUNNER@ is filled in then.

on menuselect(menuName, itemName)
	if menuName is not "#!" or itemName is not "Run" then return false
	set p to ""
	tell application "BBEdit"
		-- the frontmost window that shows a file (skips results browsers)
		repeat with w in text windows
			try
				set p to POSIX path of ((file of (active document of w)) as alias)
				exit repeat
			end try
		end repeat
	end tell
	set isTeX to false
	repeat with suffix in {".tex", ".ltx", ".latex", ".bib", ".sty", ".cls", ".dtx"}
		if p ends with (contents of suffix) then set isTeX to true
	end repeat
	if not isTeX then return false
	-- Run in the background: the typesetter talks to BBEdit, which is busy
	-- until this handler returns.
	do shell script "/usr/bin/python3 " & quoted form of "@RUNNER@" & " >/dev/null 2>&1 &"
	return true
end menuselect
