#!/bin/bash
# Make the compute queue survive a REBOOT.
#
# The machine rebooted once mid-chain (2026-09-06, 22:54) and about twelve hours
# were lost before anyone noticed. This drops a one-line launcher in the current
# user's Startup folder so the queue resumes at the next logon.
#
# It is deliberately the least invasive mechanism available: a .bat in the user's
# own Startup folder. No scheduled task, no service, no administrator rights, no
# registry. To remove it at any time:  bash uninstall_autorun.sh
# autorun.sh also removes it ITSELF once the queue reports AUTORUN_QUEUE_DONE, so
# it cannot outlive the work it exists for.

PROJ="C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics"
STARTUP="$HOME/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
BAT="$STARTUP/mof_ladder_autorun.bat"
BASH_EXE="C:\Program Files\Git\bin\bash.exe"

if [ ! -d "$STARTUP" ]; then
  echo "Startup folder not found: $STARTUP"; exit 1
fi

cat > "$BAT" <<BAT
@echo off
REM ---------------------------------------------------------------------------
REM  MOF ladder -- resume the compute queue after a reboot.
REM  Installed by install_autorun.sh. Safe to delete at any time; autorun.sh
REM  deletes it itself once the queue completes.
REM ---------------------------------------------------------------------------
cd /d "$PROJ"
start "" /min "$BASH_EXE" -lc "cd '$PROJ' && nohup bash autorun.sh >> autorun_outer.log 2>&1 &"
BAT

echo "installed: $BAT"
echo "  the queue will resume at next logon."
echo "  remove with:  bash uninstall_autorun.sh"
