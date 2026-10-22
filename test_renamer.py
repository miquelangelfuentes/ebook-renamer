"""
Tests per verificar l'extracció de metadades, resolució de conflictes (1, 2)
i el comportament del motor de reanomenament.
"""

import os
import shutil
import tempfile
import unittest
import zipfile
from metadata_extractor import (
    sanitize_filename_part,
    normalize_author_name,
    clean_tags_from_name,
    parse_filename_heuristics,
    get_ebook_info
)
from renamer_engine import RenamerEngine

class TestEbookRenamer(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_ebook_renamer_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_sanitize_and_clean(self):
        # Neteja de dos punts i caràcters prohibits
        self.assertEqual(
            sanitize_filename_part("Star Wars: Episodi IV / Una nova esperança?"),
            "Star Wars - Episodi IV - Una nova esperança"
        )
        # Neteja d'espais
        self.assertEqual(
            sanitize_filename_part("   El   nom   del   vent   "),
            "El nom del vent"
        )
        # Normalització d'autor
        self.assertEqual(
            normalize_author_name("Sanderson, Brandon"),
            "Brandon Sanderson"
        )
        self.assertEqual(
            normalize_author_name("Patrick Rothfuss"),
            "Patrick Rothfuss"
        )

    def test_filename_heuristics(self):
        # Heurística 'Títol (Autor)'
        t, a = parse_filename_heuristics("El Senyor dels Anells (J.R.R. Tolkien)")
        self.assertEqual(t, "El Senyor dels Anells")
        self.assertEqual(a, "J.R.R. Tolkien")

        # Heurística 'Autor, Nom - Títol'
        t, a = parse_filename_heuristics("Asimov, Isaac - Fundacio")
        self.assertEqual(t, "Fundacio")
        self.assertEqual(a, "Isaac Asimov")

        # Eliminació de tags de descàrrega
        clean = clean_tags_from_name("Dune [epub] (z-lib.org) {v2.0}")
        self.assertEqual(clean, "Dune")

    def create_mock_epub(self, filename: str, title: str, author: str):
        filepath = os.path.join(self.test_dir, filename)
        container_xml = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
        content_opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
  </metadata>
</package>"""
        with zipfile.ZipFile(filepath, 'w') as zf:
            zf.writestr('META-INF/container.xml', container_xml)
            zf.writestr('OEBPS/content.opf', content_opf)
        return filepath

    def test_metadata_extraction(self):
        epub_path = self.create_mock_epub("random_name_123.epub", "Dune", "Frank Herbert")
        title, author = get_ebook_info(epub_path, prefer_metadata=True)
        self.assertEqual(title, "Dune")
        self.assertEqual(author, "Frank Herbert")

    def test_duplicate_renaming(self):
        """Verifica que quan hi ha còpies del mateix llibre, s'afegeix (1), (2), etc."""
        # Creem 3 arxius amb el mateix contingut/metadades però noms originals diferents
        self.create_mock_epub("arxiu_a.epub", "Dune", "Frank Herbert")
        self.create_mock_epub("arxiu_b.epub", "Dune", "Frank Herbert")
        self.create_mock_epub("arxiu_c.epub", "Dune", "Frank Herbert")

        engine = RenamerEngine()
        plan = engine.plan_renaming(self.test_dir, prefer_metadata=True)

        proposed_names = sorted([item.proposed_name for item in plan])
        expected_names = sorted([
            "Dune - Frank Herbert.epub",
            "Dune - Frank Herbert (1).epub",
            "Dune - Frank Herbert (2).epub"
        ])

        self.assertEqual(proposed_names, expected_names)

        # Executem el reanomenament
        success, errors_cnt, error_msgs = engine.execute_renaming(plan)
        self.assertEqual(success, 3)
        self.assertEqual(errors_cnt, 0)

        # Comprovem que existeixen en disc
        disk_files = sorted(os.listdir(self.test_dir))
        self.assertEqual(disk_files, expected_names)

        # Prova de desfer (Undo)
        undo_success, undo_err_cnt, _ = engine.undo_last_operation()
        self.assertEqual(undo_success, 3)
        self.assertEqual(sorted(os.listdir(self.test_dir)), ["arxiu_a.epub", "arxiu_b.epub", "arxiu_c.epub"])

    def test_already_standardized_and_collision(self):
        # Un fitxer ja té el nom correcte
        self.create_mock_epub("El nom del vent - Patrick Rothfuss.epub", "El nom del vent", "Patrick Rothfuss")
        # Un altre fitxer té un nom diferent però és el mateix llibre
        self.create_mock_epub("el_nom_del_vent_copia.epub", "El nom del vent", "Patrick Rothfuss")

        engine = RenamerEngine()
        plan = engine.plan_renaming(self.test_dir, prefer_metadata=True)

        items_by_orig = {item.original_name: item for item in plan}
        
        # El que ja té el nom no hauria de canviar
        self.assertFalse(items_by_orig["El nom del vent - Patrick Rothfuss.epub"].is_changed)
        self.assertEqual(items_by_orig["El nom del vent - Patrick Rothfuss.epub"].status, "Ja homogeneïtzat")
        
        # El segon ha de rebre (1)
        self.assertTrue(items_by_orig["el_nom_del_vent_copia.epub"].is_changed)
        self.assertEqual(items_by_orig["el_nom_del_vent_copia.epub"].proposed_name, "El nom del vent - Patrick Rothfuss (1).epub")

    def test_pdf_metadata(self):
        # Crear un PDF mock amb pypdf
        from pypdf import PdfWriter
        pdf_path = os.path.join(self.test_dir, "sample.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.add_metadata({
            '/Title': 'Cien anos de soledad',
            '/Author': 'Gabriel Garcia Marquez'
        })
        with open(pdf_path, 'wb') as f:
            writer.write(f)

        title, author = get_ebook_info(pdf_path, prefer_metadata=True)
        self.assertEqual(title, "Cien anos de soledad")
        self.assertEqual(author, "Gabriel Garcia Marquez")

if __name__ == '__main__':
    unittest.main()
