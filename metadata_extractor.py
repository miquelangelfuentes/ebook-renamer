"""
Mòdul d'extracció de metadades per a fitxers de llibres electrònics (EPUB, PDF, MOBI, AZW, etc.)
i neteja de noms de fitxers heurística com a alternativa de seguretat.
"""

import os
import re
import struct
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional, Tuple

# Caràcters no permesos a noms de fitxers de Windows
INVALID_WIN_CHARS = r'[\\/*?:"<>|]'

def sanitize_filename_part(text: str) -> str:
    """Neteja un fragment de text per ser segur com a nom d'arxiu a Windows."""
    if not text:
        return ""
    # Substitueix dos punts per guió (ex. "Star Wars: Una nova esperança" -> "Star Wars - Una nova esperança")
    clean = text.replace(":", " - ").replace("/", "-").replace("\\", "-")
    # Elimina caràcters prohibits
    clean = re.sub(INVALID_WIN_CHARS, "", clean)
    # Compacta espais múltiples
    clean = re.sub(r'\s+', ' ', clean)
    # Treu punts i espais inicials i finals
    clean = clean.strip(". ")
    return clean

def normalize_author_name(author: str) -> str:
    """Si l'autor ve com 'Cognom, Nom', el converteix a 'Nom Cognom'."""
    author = sanitize_filename_part(author)
    if not author:
        return ""
    # Evita invertir si hi ha múltiples autors com "Autor1, Autor2 i Autor3"
    if "," in author and not any(sep in author.lower() for sep in [" and ", " i ", " y ", "&", ";"]):
        parts = [p.strip() for p in author.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            # parts[0] = Cognom, parts[1] = Nom
            author = f"{parts[1]} {parts[0]}"
    return author

def extract_epub_metadata(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Extrau títol i autor d'un fitxer .epub mitjançant l'arxiu container.xml i el paquet OPF."""
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            # 1. Trobar la ruta de l'arxiu .opf a META-INF/container.xml
            try:
                container_data = zf.read('META-INF/container.xml')
            except KeyError:
                return None, None

            root = ET.fromstring(container_data)
            # Namespace container
            ns = {'c': 'urn:oasis:names:tc:opendocument:xmlns:container'}
            rootfile = root.find('.//c:rootfile', ns)
            if rootfile is None or 'full-path' not in rootfile.attrib:
                return None, None

            opf_path = rootfile.attrib['full-path']
            try:
                opf_data = zf.read(opf_path)
            except KeyError:
                return None, None

            opf_root = ET.fromstring(opf_data)
            
            # Dublin Core namespaces
            dc_ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
            
            # Obtenir títol
            title = None
            title_elem = opf_root.find('.//dc:title', dc_ns)
            if title_elem is not None and title_elem.text:
                title = title_elem.text.strip()
            
            # Obtenir autor / creador
            author = None
            creators = opf_root.findall('.//dc:creator', dc_ns)
            author_candidates = []
            for c in creators:
                if c.text and c.text.strip():
                    role = c.attrib.get('{http://www.idpf.org/2007/opf}role', '').lower()
                    text = c.text.strip()
                    if role == 'aut' or not role:
                        author_candidates.append(text)
            
            if author_candidates:
                author = ", ".join(author_candidates)
            elif creators and creators[0].text:
                author = creators[0].text.strip()

            return title, author
    except Exception:
        return None, None

def extract_pdf_metadata(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Extrau títol i autor d'un fitxer .pdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        meta = reader.metadata
        if not meta:
            return None, None
        
        title = meta.title if meta.title else None
        author = meta.author if meta.author else None

        # Filtratge de títols genèrics comuns en PDFs
        if title:
            title_lower = title.strip().lower()
            generic = ["untitled", "microsoft word", "document", "presentación", "presentacio"]
            if any(g in title_lower for g in generic) or len(title_lower) < 2:
                title = None
            else:
                title = title.strip()

        if author:
            author_lower = author.strip().lower()
            if any(g in author_lower for g in ["administrator", "admin", "usuario", "user"]) or len(author_lower) < 2:
                author = None
            else:
                author = author.strip()

        return title, author
    except Exception:
        return None, None

def extract_mobi_metadata(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Extrau títol i autor d'arxius MOBI / AZW3 (parsejant capçaleres PalmDOC i EXTH)."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(1024 * 64) # primeres 64KB
            
            # Trobar 'MOBI' magic
            mobi_pos = header.find(b'MOBI')
            if mobi_pos == -1:
                return None, None
            
            # Longitud capçalera MOBI
            header_len = struct.unpack('>I', header[mobi_pos + 20: mobi_pos + 24])[0]
            full_name_offset = struct.unpack('>I', header[mobi_pos + 84: mobi_pos + 88])[0]
            full_name_len = struct.unpack('>I', header[mobi_pos + 88: mobi_pos + 92])[0]
            
            title = None
            if full_name_len > 0 and full_name_offset + full_name_len <= len(header):
                try:
                    title = header[full_name_offset: full_name_offset + full_name_len].decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass

            # Buscar registre EXTH
            exth_flag = struct.unpack('>I', header[mobi_pos + 128: mobi_pos + 132])[0]
            author = None
            if exth_flag & 0x40:
                exth_offset = mobi_pos + 16 + header_len
                if exth_offset + 12 <= len(header) and header[exth_offset:exth_offset+4] == b'EXTH':
                    count = struct.unpack('>I', header[exth_offset + 8: exth_offset + 12])[0]
                    curr = exth_offset + 12
                    for _ in range(count):
                        if curr + 8 > len(header):
                            break
                        rec_type, rec_len = struct.unpack('>II', header[curr:curr+8])
                        val = header[curr+8:curr+rec_len]
                        if rec_type == 100: # Author
                            try:
                                author = val.decode('utf-8', errors='ignore').strip()
                            except Exception:
                                pass
                        elif rec_type == 503 and not title: # Updated Title
                            try:
                                title = val.decode('utf-8', errors='ignore').strip()
                            except Exception:
                                pass
                        curr += rec_len

            return title, author
    except Exception:
        return None, None

def clean_tags_from_name(name: str) -> str:
    """Elimina etiquetes típiques de descàrrega com [epub], (z-lib.org), etc."""
    # Eliminar blocs entre claudàtors [ ... ] o claus { ... }
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\{.*?\}', '', name)
    
    # Eliminar referències conegudes entre parèntesis
    tags = [
        r'\(z-lib.*?\)', r'\(v[\d\.]+\)', r'\(epub.*?\)', r'\(spanish.*?\)', 
        r'\(catalan.*?\)', r'\(castellano.*?\)', r'\(editorial.*?\)'
    ]
    for tag in tags:
        name = re.sub(tag, '', name, flags=re.IGNORECASE)
    
    # Substituir guions baixos per espais
    name = name.replace("_", " ")
    # Compactar espais
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def parse_filename_heuristics(filename_without_ext: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Intenta inferir (Títol, Autor) a partir del nom del fitxer si no hi ha metadades.
    Admet patrons freqüents com:
    - 'Autor - Títol'
    - 'Títol - Autor'
    - 'Títol (Autor)'
    - 'Cognom, Nom - Títol'
    """
    clean_name = clean_tags_from_name(filename_without_ext)
    
    # Patró 1: Títol (Autor)
    parenthesis_match = re.search(r'^(.*?)\s*\(([^()]+)\)$', clean_name)
    if parenthesis_match:
        cand1 = parenthesis_match.group(1).strip()
        cand2 = parenthesis_match.group(2).strip()
        # Si cand2 sembla un any (ex: 2021) o una edició, no és autor
        if not re.match(r'^\d{4}$', cand2) and len(cand2) > 2:
            return cand1, cand2

    # Patró 2: Separador ' - ' o ' – '
    parts = re.split(r'\s*[-–—]\s*', clean_name)
    if len(parts) == 2:
        part0, part1 = parts[0].strip(), parts[1].strip()
        # Heurística: si part0 conté una coma com 'Asimov, Isaac', part0 és l'autor
        if "," in part0:
            return part1, normalize_author_name(part0)
        # Si part1 conté coma 'Asimov, Isaac'
        if "," in part1:
            return part0, normalize_author_name(part1)
        
        # En comunitats de lectors, 'Autor - Títol' és el format més freqüent de descàrrega
        # Però si part0 ja sembla el títol, retornem com a autor i títol
        return part1, part0

    return None, None

def get_ebook_info(file_path: str, prefer_metadata: bool = True) -> Tuple[str, str]:
    """
    Retorna (títol, autor) d'un fitxer.
    Si prefer_metadata és True, intenta llegir metadades del fitxer (EPUB, PDF, MOBI).
    Si no n'hi ha o falla, recorre a l'heurística del nom.
    """
    base_name = os.path.basename(file_path)
    stem, ext = os.path.splitext(base_name)
    ext_lower = ext.lower()

    title, author = None, None

    if prefer_metadata:
        if ext_lower == '.epub':
            title, author = extract_epub_metadata(file_path)
        elif ext_lower == '.pdf':
            title, author = extract_pdf_metadata(file_path)
        elif ext_lower in ['.mobi', '.azw', '.azw3']:
            title, author = extract_mobi_metadata(file_path)

    # Si falta títol o autor, provem l'heurística del nom de fitxer
    if not title or not author:
        heur_title, heur_author = parse_filename_heuristics(stem)
        if not title and heur_title:
            title = heur_title
        if not author and heur_author:
            author = heur_author

    # Si encara falta títol, fem servir el nom base netejat
    if not title:
        title = clean_tags_from_name(stem)
    if not author:
        author = "Desconegut"

    # Sanejament final
    title = sanitize_filename_part(title)
    author = normalize_author_name(author)
    
    if not title:
        title = "Llibre sense títol"
    if not author:
        author = "Desconegut"

    return title, author
