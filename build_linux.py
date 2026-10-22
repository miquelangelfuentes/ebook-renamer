"""
Script per compilar Ebook Renamer a un binari autònom de Linux amb PyInstaller.
"""

import os
import sys
import subprocess

def build():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)

    print("=== Compilant Ebook Renamer per a Linux ===")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name", "ebook-renamer",
        "--collect-all", "customtkinter",
        "--collect-all", "pypdf",
        "main.py"
    ]

    print("Executant:")
    print(" ".join(cmd))
    
    res = subprocess.run(cmd)
    if res.returncode == 0:
        bin_path = os.path.join(current_dir, "dist", "ebook-renamer")
        print("\n=======================================================")
        print(" [OK] Compilació per a Linux completada amb èxit!")
        print(f" Binari generat a: {bin_path}")
        print("=======================================================")
    else:
        print("\n[ERROR] Ha fallat la compilació.")
        sys.exit(1)

if __name__ == "__main__":
    build()
