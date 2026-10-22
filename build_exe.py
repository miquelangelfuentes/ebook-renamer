"""
Script per compilar Ebook Renamer a un executable autònom de Windows (.exe) amb icona personalitzada.
"""

import os
import sys
import subprocess

def build():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)

    print("=== Iniciant la compilació d'Ebook Renamer (.exe) amb icona ===")
    
    icon_path = os.path.join(current_dir, "assets", "icon.ico")
    
    # Comanda PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed", # No obre consola negra
        "--name", "EbookRenamer",
        "--icon", icon_path,
        "--add-data", "assets;assets",
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
