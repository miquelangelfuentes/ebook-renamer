"""
Motor de reanomenament de llibres electrònics amb resolució de col·lisions i historial per desfer.
Format objectiu: 'Nom del llibre - Autor'
Duplicats: 'Nom del llibre - Autor (1)', 'Nom del llibre - Autor (2)', etc.
"""

import os
import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from metadata_extractor import get_ebook_info, sanitize_filename_part

# Extensions compatibles per defecte
DEFAULT_EXTENSIONS = {'.epub', '.pdf', '.mobi', '.azw', '.azw3', '.fb2', '.cbz', '.cbr'}

@dataclass
class RenameItem:
    original_path: str
    original_name: str
    folder: str
    extension: str
    title: str
    author: str
    proposed_name: str
    proposed_path: str
    status: str
    is_changed: bool
    error: Optional[str] = None

class RenamerEngine:
    def __init__(self):
        self.last_operations: List[Dict[str, str]] = []

    def plan_renaming(
        self,
        folder_path: str,
        prefer_metadata: bool = True,
        recursive: bool = False,
        custom_extensions: Optional[set] = None
    ) -> List[RenameItem]:
        """
        Analitza la carpeta i genera el pla de canvis detallat (previsualització)
        sense modificar cap fitxer en disc.
        """
        extensions = custom_extensions if custom_extensions else DEFAULT_EXTENSIONS
        folder_path = os.path.abspath(folder_path)
        
        if not os.path.isdir(folder_path):
            raise ValueError(f"La ruta no és una carpeta vàlida: {folder_path}")

        # Recollir fitxers
        candidate_files: List[str] = []
        if recursive:
            for root, _, files in os.walk(folder_path):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in extensions:
                        candidate_files.append(os.path.join(root, f))
        else:
            for f in os.listdir(folder_path):
                full_path = os.path.join(folder_path, f)
                if os.path.isfile(full_path):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in extensions:
                        candidate_files.append(full_path)

        # Per cada carpeta, gestionem els noms existents per evitar col·lisions
        # Clau: ruta de la carpeta; Valor: conjunt de noms en minúscules ja reservats o existents
        files_by_folder: Dict[str, List[str]] = {}
        for path in candidate_files:
            parent = os.path.dirname(path)
            files_by_folder.setdefault(parent, []).append(path)

        plan: List[RenameItem] = []

        for parent_dir, file_paths in files_by_folder.items():
            # Fitxers reals existents al directori
            existing_disk_names = set(os.listdir(parent_dir))
            # Registre de noms que s'aniran assignant en aquesta sessió (per detectar duplicats/còpies)
            assigned_names = set()

            for original_path in file_paths:
                orig_name = os.path.basename(original_path)
                stem, ext = os.path.splitext(orig_name)
                
                # Obtenir títol i autor
                title, author = get_ebook_info(original_path, prefer_metadata=prefer_metadata)
                
                # Format objectiu base: "Nom del llibre - Autor"
                base_target_stem = f"{title} - {author}"
                target_name = f"{base_target_stem}{ext}"
                
                # Resolució de duplicats i existències:
                # Si el nom ja està agafat (per un altre arxiu assignat en aquest lot o un fitxer existent al disc que no sigui aquest mateix)
                is_duplicate = False
                copy_counter = 0

                # Comprovem si el nom base està disponible per a aquest arxiu
                # Cas 1: L'arxiu ja té exactament aquest nom i no ha estat duplicat
                if orig_name == target_name and target_name not in assigned_names:
                    # Ja està perfecte
                    candidate_name = target_name
                else:
                    candidate_name = target_name
                    # Si el candidate_name està ja assignat en aquest lot, O existeix al disc i no és el propi fitxer
                    while (candidate_name in assigned_names) or (candidate_name in existing_disk_names and candidate_name != orig_name):
                        copy_counter += 1
                        candidate_name = f"{base_target_stem} ({copy_counter}){ext}"
                        is_duplicate = True

                assigned_names.add(candidate_name)
                proposed_path = os.path.join(parent_dir, candidate_name)

                # Determinació de l'estat
                is_changed = (orig_name != candidate_name)
                if not is_changed:
                    status = "Ja homogeneïtzat"
                elif is_duplicate:
                    status = f"Còpia detectada ({copy_counter})"
                else:
                    status = "A punt per reanomenar"

                plan.append(RenameItem(
                    original_path=original_path,
                    original_name=orig_name,
                    folder=parent_dir,
                    extension=ext,
                    title=title,
                    author=author,
                    proposed_name=candidate_name,
                    proposed_path=proposed_path,
                    status=status,
                    is_changed=is_changed
                ))

        return plan

    def execute_renaming(self, plan: List[RenameItem]) -> Tuple[int, int, List[str]]:
        """
        Aplica el pla de reanomenament.
        Retorna: (total_èxits, total_errors, llista_missatges_error)
        """
        success_count = 0
        error_count = 0
        errors: List[str] = []
        operations: List[Dict[str, str]] = []

        # Filtrem els que realment necessiten canvi
        items_to_rename = [item for item in plan if item.is_changed]

        # En Windows, per reanomenaments entre majúscules/minúscules (ex. arxiu.txt -> Arxiu.txt),
        # de vegades cal passar per un nom temporal intermedi si el filesystem és case-insensitive.
        for item in items_to_rename:
            try:
                # Comprovació de seguretat: l'arxiu original existeix?
                if not os.path.exists(item.original_path):
                    msg = f"No s'ha trobat l'arxiu original: {item.original_name}"
                    errors.append(msg)
                    error_count += 1
                    item.error = msg
                    continue

                # Si canvia només la capitalització
                if item.original_path.lower() == item.proposed_path.lower() and item.original_path != item.proposed_path:
                    temp_path = item.original_path + ".tmp_renamer_swap"
                    os.rename(item.original_path, temp_path)
                    os.rename(temp_path, item.proposed_path)
                else:
                    os.rename(item.original_path, item.proposed_path)

                operations.append({
                    "original": item.original_path,
                    "new": item.proposed_path
                })
                success_count += 1
                item.status = "Reanomenat amb èxit"

            except Exception as e:
                msg = f"Error en '{item.original_name}': {str(e)}"
                errors.append(msg)
                error_count += 1
                item.error = str(e)
                item.status = f"Error: {str(e)}"

        if operations:
            self.last_operations = operations
            self._save_history(operations)

        return success_count, error_count, errors

    def undo_last_operation(self) -> Tuple[int, int, List[str]]:
        """
        Desfà l'última operació de reanomenament, restaurant els noms originals.
        """
        if not self.last_operations:
            return 0, 0, ["No hi ha cap operació prèvia a la memòria per desfer."]

        success_count = 0
        error_count = 0
        errors: List[str] = []
        remaining_operations = []

        # Desfer en ordre invers
        for op in reversed(self.last_operations):
            current_path = op["new"]
            original_path = op["original"]

            try:
                if os.path.exists(current_path):
                    # Si canvia només la capitalització
                    if current_path.lower() == original_path.lower() and current_path != original_path:
                        temp_path = current_path + ".tmp_renamer_undo"
                        os.rename(current_path, temp_path)
                        os.rename(temp_path, original_path)
                    else:
                        os.rename(current_path, original_path)
                    success_count += 1
                else:
                    errors.append(f"No s'ha trobat el fitxer '{os.path.basename(current_path)}' per restaurar-lo.")
                    error_count += 1
                    remaining_operations.append(op)
            except Exception as e:
                errors.append(f"Error restaurant '{os.path.basename(current_path)}': {str(e)}")
                error_count += 1
                remaining_operations.append(op)

        self.last_operations = remaining_operations
        return success_count, error_count, errors

    def _save_history(self, operations: List[Dict[str, str]]):
        """Desa un registre de l'última operació per si l'usuari tanca el programa i vol consultar-lo."""
        try:
            log_path = os.path.join(os.path.expanduser("~"), ".ebook_renamer_last_log.json")
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(operations, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
