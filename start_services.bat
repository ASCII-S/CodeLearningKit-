@echo off
wt.exe -w 0 nt -d . --title "JupyterLab" wsl.exe bash -c "cd /mnt/d/Document/Obsidian/TecAccumulation/.kit && ./kit.sh jupyter lab" ; nt -d . --title "Sync" wsl.exe bash -c "cd /mnt/d/Document/Obsidian/TecAccumulation/.kit && ./kit.sh sync"
pause