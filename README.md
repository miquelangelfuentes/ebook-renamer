# 📚 Ebook Renamer - Homogeneïtzador de Llibres (Windows & Linux)

Aplicació per a **Windows** i **Linux** que homogeneïtza i estandarditza els noms dels arxius d'una carpeta de llibres electrònics seguint el format:
```
Nom del llibre - Autor.ext
```
Si es detecten duplicats o còpies del mateix llibre, afegeix automàticament la numeració consecutiva:
```
Nom del llibre - Autor.ext
Nom del llibre - Autor (1).ext
Nom del llibre - Autor (2).ext
```

---

## 📥 Descarregar directament l'executable per a Windows

No cal instal·lar Python ni cap dependència:
* 👉 **[Descarregar EbookRenamer.exe (clic aquí)](https://github.com/miquelangelfuentes/ebook-renamer/raw/main/EbookRenamer.exe)**  
  *(o pots descarregar-lo directament des de la llista d'arxius d'aquest repositori fent clic a `EbookRenamer.exe`)*

---

## ✨ Característiques principals

1. **Lectura directa de metadades internes**:
   - Suporta `.epub` (llegeix Dublin Core: `dc:title` i `dc:creator` de l'OPF intern).
   - Suporta `.pdf` (títol i autor des de les metadades del document).
   - Suporta `.mobi`, `.azw` i `.azw3` (capçalera PalmDOC i registres EXTH).
2. **Heurística intel·ligent com a alternativa (Fallback)**:
   - Si un fitxer no té metadades gravades, el programa analitza patrons del nom (`Autor - Títol`, `Títol (Autor)`, etc.) i neteja etiquetes de descàrrega (`[epub]`, `(z-lib.org)`, números de versió, guions baixos).
3. **Resolució de duplicats**:
   - Garanteix que cap fitxer se sobreescrigui accidentalment.
   - Assigna sufixos `(1)`, `(2)`, etc. quan coincideix el mateix títol i autor.
4. **Sanejament de noms**:
   - Reemplaça automàticament caràcters prohibits a Windows/FAT32/exFAT (`\ / : * ? " < > |`) per alternatives netes.
5. **Doble modalitat d'ús (GUI & CLI)**:
   - **Interfície gràfica moderna**: amb CustomTkinter, taula interactiva i botons per previsualitzar abans d'aplicar.
   - **Línia de comandes (CLI)**: ideal per a servidors Linux, NAS (Synology, Raspberry Pi) o scripts automatitzats.
6. **Funció Desfer (Undo)**:
   - Permet revertir els canvis en qualsevol moment i tornar als noms originals.

---

## 💻 Ús a Windows

* Executa directament l'arxiu **`EbookRenamer.exe`**.
* Selecciona la carpeta dels teus llibres, prem **"Previsualitzar"** i després **"Reanomenar"**.

---

## 🐧 Ús a Linux

### Opció A: Interfície gràfica (GUI)
Assegura't de tenir `python3-tk` instal·lat (a Ubuntu/Debian: `sudo apt install python3-tk python3-venv`).
```bash
# Execució directa amb el script d'arrencada:
chmod +x run_linux.sh
./run_linux.sh
```

### Opció B: Línia de comandes (CLI)
Pots reanomenar o simular directament des de la terminal:
```bash
# Simulació (dry-run) sense tocar cap fitxer:
python3 main.py /ruta/als/teus/ebooks --cli --dry-run

# Reanomenar confirmant interactivament:
python3 main.py /ruta/als/teus/ebooks --cli

# Reanomenar automàticament incloent subcarpetes:
python3 main.py /ruta/als/teus/ebooks --cli -y --recursive
```

---

## 🛠️ Desenvolupament i Compilació

- **Instal·lar dependències**:
  ```bash
  pip install -r requirements.txt
  ```
- **Executar bateria de tests**:
  ```bash
  python -m unittest test_renamer.py
  ```
- **Compilar executable Windows (.exe)**:
  ```bash
  python build_exe.py
  ```
- **Compilar binari de Linux**:
  ```bash
  python build_linux.py
  ```
