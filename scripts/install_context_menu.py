"""Windows context menu integration for Multi-Utility Tool."""

import os
import sys

try:
    import winreg
except ImportError:  # not on Windows
    winreg = None


def install():
    if winreg is None:
        print("This script only works on Windows.")
        return
    exe = os.path.abspath(sys.argv[0])
    command = f'"{sys.executable}" "{exe}" "%1"'
    key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"*\shell\MultiUtilityTool")
    winreg.SetValue(key, "", winreg.REG_SZ, "Process with Multi-Utility Tool")
    cmd_key = winreg.CreateKey(key, "command")
    winreg.SetValue(cmd_key, "", winreg.REG_SZ, command)
    winreg.CloseKey(cmd_key)
    winreg.CloseKey(key)
    print("Context menu entry installed.")


if __name__ == "__main__":
    install()
