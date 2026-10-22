#!/usr/bin/env bash
# Script d'inici ràpid per a Linux (crea entorn virtual si cal i executa Ebook Renamer)
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=== Ebook Renamer per a Linux ==="

# Comprovar Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 no està instal·lat. Instal·la'l amb: sudo apt install python3 python3-pip python3-tk"
    exit 1
fi

# Crear entorn virtual si no existeix
if [ ! -d ".venv" ]; then
    echo "Configurant entorn virtual (.venv)..."
    python3 -m venv .venv || {
        echo "[AVÍS] No s'ha pogut crear el venv. Assegura't de tenir 'python3-venv' instal·lat."
    }
fi

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    pip install -q -r requirements.txt
    python3 main.py "$@"
else
    pip3 install --user -q -r requirements.txt
    python3 main.py "$@"
fi
