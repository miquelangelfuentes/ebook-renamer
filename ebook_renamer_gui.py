"""
Interfície gràfica moderna per a Ebook Renamer amb CustomTkinter i ttk.
"""

import os
import sys
import threading
from typing import List, Optional
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from renamer_engine import RenamerEngine, RenameItem

# Configuració visual de CustomTkinter
ctk.set_appearance_mode("System")  # Segueix el mode clar/fosc de Windows
ctk.set_default_color_theme("blue")

class EbookRenamerApp(ctk.CTk):
    def __init__(self, initial_folder: Optional[str] = None):
        super().__init__()

        self.title("Ebook Renamer - Homogeneïtzador de Llibres")
        self.geometry("980x640")
        self.minsize(800, 500)

        self.engine = RenamerEngine()
        self.current_plan: List[RenameItem] = []
        self.is_processing = False

        self._create_widgets()

        if initial_folder and os.path.isdir(initial_folder):
            self.folder_var.set(initial_folder)
            self.start_preview()

    def _create_widgets(self):
        # 1. Capçalera
        header_frame = ctk.CTkFrame(self, corner_radius=10)
        header_frame.pack(fill="x", padx=16, pady=(16, 8))

        title_label = ctk.CTkLabel(
            header_frame,
            text="📚 Ebook Renamer",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(anchor="w", padx=16, pady=(10, 2))

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Homogeneïtza els noms d'arxius al format: 'Nom del llibre - Autor' amb gestió automàtica de duplicats (1), (2)...",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.pack(anchor="w", padx=16, pady=(0, 10))

        # 2. Selecció de carpeta i opcions
        controls_frame = ctk.CTkFrame(self, corner_radius=10)
        controls_frame.pack(fill="x", padx=16, pady=8)

        # Barra de ruta
        folder_row = ctk.CTkFrame(controls_frame, fg_color="transparent")
        folder_row.pack(fill="x", padx=12, pady=(12, 6))

        folder_label = ctk.CTkLabel(folder_row, text="Carpeta d'ebooks:", font=ctk.CTkFont(size=13, weight="bold"))
        folder_label.pack(side="left", padx=(0, 8))

        self.folder_var = ctk.StringVar()
        self.folder_entry = ctk.CTkEntry(
            folder_row,
            textvariable=self.folder_var,
            placeholder_text="Selecciona la carpeta on tens els llibres...",
            font=ctk.CTkFont(size=12)
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_btn = ctk.CTkButton(
            folder_row,
            text="📁 Examinar...",
            width=120,
            command=self.browse_folder
        )
        self.browse_btn.pack(side="right")

        # Opcions (Metadades, Recursiu)
        options_row = ctk.CTkFrame(controls_frame, fg_color="transparent")
        options_row.pack(fill="x", padx=12, pady=(0, 12))

        self.meta_var = ctk.BooleanVar(value=True)
        self.meta_check = ctk.CTkCheckBox(
            options_row,
            text="Llegir metadades internes (EPUB, PDF, MOBI)",
            variable=self.meta_var,
            font=ctk.CTkFont(size=12)
        )
        self.meta_check.pack(side="left", padx=(0, 16))

        self.recursive_var = ctk.BooleanVar(value=False)
        self.recursive_check = ctk.CTkCheckBox(
            options_row,
            text="Incloure subcarpetes",
            variable=self.recursive_var,
            font=ctk.CTkFont(size=12)
        )
        self.recursive_check.pack(side="left")

        # 3. Taula de previsualització
        table_frame = ctk.CTkFrame(self, corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=16, pady=8)

        table_header_row = ctk.CTkFrame(table_frame, fg_color="transparent")
        table_header_row.pack(fill="x", padx=12, pady=(10, 4))

        self.status_summary_label = ctk.CTkLabel(
            table_header_row,
            text="Selecciona una carpeta i prem 'Previsualitzar' per començar.",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.status_summary_label.pack(side="left")

        # Treeview per a rendiment ràpid
        tree_container = tk.Frame(table_frame, bg="#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#f0f0f0")
        tree_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        columns = ("original", "proposed", "status")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("original", text="Nom actual del fitxer")
        self.tree.heading("proposed", text="Nom nou proposat (Títol - Autor)")
        self.tree.heading("status", text="Estat")

        self.tree.column("original", width=360, anchor="w")
        self.tree.column("proposed", width=380, anchor="w")
        self.tree.column("status", width=160, anchor="center")

        # Scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')

        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)

        # Tags de colors per estats a la taula
        self.tree.tag_configure("changed", foreground="#10b981")     # Verd
        self.tree.tag_configure("duplicate", foreground="#f59e0b")   # Taronja
        self.tree.tag_configure("unchanged", foreground="#6b7280")   # Gris
        self.tree.tag_configure("error", foreground="#ef4444")       # Vermell

        # 4. Barra inferior d'accions
        actions_frame = ctk.CTkFrame(self, corner_radius=10)
        actions_frame.pack(fill="x", padx=16, pady=(8, 16))

        self.preview_btn = ctk.CTkButton(
            actions_frame,
            text="🔍 Previsualitzar canvis",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.start_preview,
            width=180
        )
        self.preview_btn.pack(side="left", padx=12, pady=12)

        self.rename_btn = ctk.CTkButton(
            actions_frame,
            text="⚡ Reanomenar fitxers",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            command=self.confirm_and_rename,
            width=180,
            state="disabled"
        )
        self.rename_btn.pack(side="left", padx=6, pady=12)

        self.undo_btn = ctk.CTkButton(
            actions_frame,
            text="↩️ Desfer canvis (Undo)",
            font=ctk.CTkFont(size=12),
            fg_color="#4b5563",
            hover_color="#374151",
            command=self.undo_changes,
            width=160,
            state="disabled"
        )
        self.undo_btn.pack(side="right", padx=12, pady=12)

        self.progress_bar = ctk.CTkProgressBar(actions_frame, mode="indeterminate")
        # Inicialment oculta

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta d'ebooks")
        if folder:
            self.folder_var.set(folder)
            self.start_preview()

    def start_preview(self):
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Carpeta no vàlida", "Si us plau, selecciona una carpeta vàlida.")
            return

        if self.is_processing:
            return

        self.is_processing = True
        self.preview_btn.configure(state="disabled")
        self.rename_btn.configure(state="disabled")
        self.status_summary_label.configure(text="Examinant fitxers i llegint metadades...")
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=12, pady=12)
        self.progress_bar.start()

        # Neteja taula
        for item in self.tree.get_children():
            self.tree.delete(item)

        thread = threading.Thread(target=self._run_preview_thread, args=(folder,), daemon=True)
        thread.start()

    def _run_preview_thread(self, folder: str):
        try:
            prefer_meta = self.meta_var.get()
            recursive = self.recursive_var.get()
            plan = self.engine.plan_renaming(
                folder,
                prefer_metadata=prefer_meta,
                recursive=recursive
            )
            self.after(0, self._preview_complete, plan, None)
        except Exception as e:
            self.after(0, self._preview_complete, [], str(e))

    def _preview_complete(self, plan: List[RenameItem], error: Optional[str]):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.is_processing = False
        self.preview_btn.configure(state="normal")

        if error:
            messagebox.showerror("Error", f"S'ha produït un error en analitzar la carpeta:\n{error}")
            self.status_summary_label.configure(text="Error durant l'anàlisi.")
            return

        self.current_plan = plan
        total = len(plan)
        to_rename = sum(1 for item in plan if item.is_changed)
        unchanged = total - to_rename
        duplicates = sum(1 for item in plan if "Còpia detectada" in item.status)

        for item in plan:
            if not item.is_changed:
                tag = "unchanged"
            elif "Còpia detectada" in item.status:
                tag = "duplicate"
            else:
                tag = "changed"

            self.tree.insert(
                "",
                "end",
                values=(item.original_name, item.proposed_name, item.status),
                tags=(tag,)
            )

        summary_msg = f"Total fitxers: {total}  |  A reanomenar: {to_rename}  |  Sense canvis: {unchanged}"
        if duplicates > 0:
            summary_msg += f"  |  Còpies resoltes: {duplicates}"
        
        self.status_summary_label.configure(text=summary_msg)

        if to_rename > 0:
            self.rename_btn.configure(state="normal")
        else:
            self.rename_btn.configure(state="disabled")

    def confirm_and_rename(self):
        if not self.current_plan:
            return

        to_rename = [item for item in self.current_plan if item.is_changed]
        if not to_rename:
            messagebox.showinfo("Sense canvis", "Tots els fitxers ja estan correctament homogeneïtzats.")
            return

        confirm = messagebox.askyesno(
            "Confirmar reanomenament",
            f"Es reanomenaran {len(to_rename)} fitxers al format:\n'Nom del llibre - Autor'\n\nVols continuar?",
            icon="question"
        )
        if not confirm:
            return

        self.is_processing = True
        self.rename_btn.configure(state="disabled")
        self.preview_btn.configure(state="disabled")
        self.status_summary_label.configure(text="Reanomenant fitxers...")
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=12, pady=12)
        self.progress_bar.start()

        thread = threading.Thread(target=self._run_rename_thread, daemon=True)
        thread.start()

    def _run_rename_thread(self):
        success, errors_cnt, error_msgs = self.engine.execute_renaming(self.current_plan)
        self.after(0, self._rename_complete, success, errors_cnt, error_msgs)

    def _rename_complete(self, success: int, errors_cnt: int, error_msgs: List[str]):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.is_processing = False
        self.preview_btn.configure(state="normal")
        self.undo_btn.configure(state="normal")

        if errors_cnt == 0:
            messagebox.showinfo(
                "Procés completat",
                f"S'han reanomenat amb èxit {success} fitxers!"
            )
        else:
            details = "\n".join(error_msgs[:5])
            if len(error_msgs) > 5:
                details += f"\n... i {len(error_msgs) - 5} errors més."
            messagebox.showwarning(
                "Completat amb incidències",
                f"S'han reanomenat: {success}\nErrors: {errors_cnt}\n\nDetalls:\n{details}"
            )

        # Actualitzem la vista amb l'estat actual de la carpeta
        self.start_preview()

    def undo_changes(self):
        confirm = messagebox.askyesno(
            "Desfer operació",
            "Vols restaurar els fitxers als seus noms originals anteriors?",
            icon="question"
        )
        if not confirm:
            return

        success, error_cnt, errors = self.engine.undo_last_operation()
        if error_cnt == 0:
            messagebox.showinfo("Restaurat", f"S'han restaurat {success} fitxers correctament.")
            self.undo_btn.configure(state="disabled")
        else:
            messagebox.showwarning("Restauració parcial", f"Restaurats: {success}\nErrors: {error_cnt}")

        self.start_preview()

def main():
    initial_folder = None
    if len(sys.argv) > 1:
        initial_folder = sys.argv[1]

    app = EbookRenamerApp(initial_folder=initial_folder)
    app.mainloop()

if __name__ == "__main__":
    main()
