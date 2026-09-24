#!/bin/bash
# Remove the reboot launcher installed by install_autorun.sh.
BAT="$HOME/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/mof_ladder_autorun.bat"
if [ -f "$BAT" ]; then rm -f "$BAT" && echo "removed: $BAT"; else echo "not installed (nothing to remove)"; fi
