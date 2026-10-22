"""
Punt d'entrada d'Ebook Renamer compatible amb Windows i Linux.
Permet executar tant en mode gràfic (GUI moderna) com en línia de comandes (CLI).
"""

import sys
import os
import argparse

# Assegurem el directori al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Assegurar UTF-8 a la consola per evitar errors de codificació a Windows cp1252
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from renamer_engine import RenamerEngine

def run_cli(args):
    """Execució en mode línia de comandes (ideal per a Linux, servidors, NAS o scripts)."""
    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        print(f"[ERROR] La ruta especificada no és una carpeta vàlida: {folder}")
        sys.exit(1)

    print("=" * 60)
    print("Ebook Renamer (Mode CLI - Línia de comandes)")
    print(f"Carpeta: {folder}")
    print(f"Llegir metadades internes: {'Sí' if not args.no_meta else 'No'}")
    print(f"Recursiu (subcarpetes): {'Sí' if args.recursive else 'No'}")
    print("=" * 60)

    engine = RenamerEngine()
    try:
        plan = engine.plan_renaming(
            folder,
            prefer_metadata=not args.no_meta,
            recursive=args.recursive
        )
    except Exception as e:
        print(f"[ERROR] Error analitzant els fitxers: {e}")
        sys.exit(1)

    if not plan:
        print("No s'ha trobat cap fitxer compatible (.epub, .pdf, .mobi, .azw, etc.).")
        return

    to_rename = [item for item in plan if item.is_changed]
    unchanged = [item for item in plan if not item.is_changed]

    print(f"\nTotal fitxers analitzats: {len(plan)}")
    print(f"  * A reanomenar: {len(to_rename)}")
    print(f"  * Ja homogeneïtzats: {len(unchanged)}")
    print("-" * 60)

    for item in plan:
        if item.is_changed:
            status_tag = f"[{item.status}]"
            print(f"{status_tag:25} {item.original_name}")
            print(f"{'-->':25} {item.proposed_name}\n")
        elif args.verbose:
            print(f"[SENSE CANVIS]            {item.original_name}")

    if not to_rename:
        print("\nTots els fitxers ja segueixen el format 'Nom del llibre - Autor'!")
        return

    if args.dry_run:
        print("\n[MODALITAT SIMULACIÓ (DRY RUN)] No s'ha modificat cap fitxer.")
        print("Per aplicar els canvis reals, torna a executar sense l'argument --dry-run o afegeix --apply.")
        return

    if not args.yes:
        try:
            resposta = input(f"\nVols procedir a reanomenar {len(to_rename)} fitxers? (s/N): ").strip().lower()
            if resposta not in ["s", "si", "sí", "y", "yes"]:
                print("Operació cancel·lada per l'usuari.")
                return
        except (KeyboardInterrupt, EOFError):
            print("\nOperació cancel·lada.")
            return

    print("\nReanomenant fitxers...")
    success, errors_cnt, error_msgs = engine.execute_renaming(plan)
    print(f"Operació finalitzada! Reanomenats amb èxit: {success} | Errors: {errors_cnt}")

    if error_msgs:
        print("\nDetall d'errors:")
        for err in error_msgs:
            print(f" - {err}")

def run_gui(folder=None):
    """Executa la interfície gràfica d'usuari."""
    try:
        from ebook_renamer_gui import EbookRenamerApp
        app = EbookRenamerApp(initial_folder=folder)
        app.mainloop()
    except Exception as e:
        # Si a Linux no hi ha entorn gràfic (X11 / Wayland display)
        if "no display name" in str(e).lower() or "display" in str(e).lower():
            print("[AVÍS] No s'ha detectat cap servidor gràfic (X11/Wayland).")
            print("Pots utilitzar el programa des de la terminal amb l'opció --cli:")
            print("  python3 main.py --cli /ruta/a/la/carpeta/ebooks")
            sys.exit(1)
        else:
            raise e

def main():
    parser = argparse.ArgumentParser(
        description="Ebook Renamer: Homogeneïtza noms d'arxius d'ebooks a 'Nom del llibre - Autor'."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Ruta de la carpeta amb els llibres (opcional per obrir la GUI directament o obligatòria amb --cli)"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Executa en mode consola/línia de comandes sense interfície gràfica"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="En mode CLI, només mostra la simulació sense canviar cap arxiu"
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="En mode CLI, confirma automàticament sense preguntar (ideal per a scripts)"
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Inclou també els fitxers de les subcarpetes"
    )
    parser.add_argument(
        "--no-meta",
        action="store_true",
        help="No llegeix les metadades internes i fa servir només l'heurística del nom"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostra informació detallada de tots els fitxers, inclosos els que no canvien"
    )

    args = parser.parse_args()

    # Si s'indica explícitament --cli o s'introdueixen flags de CLI com --dry-run
    if args.cli or args.dry_run or args.yes:
        if not args.folder:
            print("[ERROR] Cal indicar una carpeta en mode CLI. Exemple: python3 main.py --cli /home/usuari/ebooks")
            sys.exit(1)
        run_cli(args)
    else:
        # Per defecte obrim GUI
        run_gui(args.folder)

if __name__ == "__main__":
    main()
