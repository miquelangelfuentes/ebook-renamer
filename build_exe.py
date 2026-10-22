"""
Script per compilar Ebook Renamer a un executable autònom de Windows (.exe).
Utilitza PyInstaller recollint totes les dependències necessàries (CustomTkinter, PyPDF).
"""

import os
import sys
import subprocess
import shutil

def build():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)

    print("=== Iniciant la compilació d'Ebook Renamer (.exe) ===")
    
    # Comanda PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed", # No obre finestra de consola negra al darrere
        "--name", "EbookRenamer",
        "--collect-all", "customtkinter",
        "--collect-all", "pypdf",
        "main.py"
    ]

    print("Executant comanda:")
    print(" ".join(cmd))
    
    result = subprocess.run(cmd)
    if result.returncode == 0:
        exe_path = os.path.join(current_dir, "dist", "EbookRenamer.exe")
        print("\n=======================================================")
        print(" [OK] Compilació completada amb èxit!")
        print(f" Executable generat a:\n {exe_path}")
        print("=======================================================")
    else:
        print("\n[ERROR] La compilació ha fallat.")
        sys.exit(1)

if __name__ == "__main__":
    build()
