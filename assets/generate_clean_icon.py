"""
Generador d'icona minimalista, neta i elegant per a Ebook Renamer.
Fons 100% transparent.
Disseny basat en línies suaus d'un llibre obert i etiqueta d'organització,
amb màxima llegibilitat a mides petites (tasques, escriptori).
"""

import math
from PIL import Image, ImageDraw

def draw_smooth_icon(output_png: str, output_ico: str):
    # Dibuixem a 2048x2048 amb anti-aliasing
    size = 2048
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    cx = size // 2      # 1024
    cy = size // 2 + 30 # 1054

    # Paleta de colors moderna i elegant:
    # Blau marí profund / Cobalt per al cos del llibre
    # Cyan elèctric suau per a la pàgina superior
    # Ambre daurat càlid per a la cinta / etiqueta
    col_cover = (30, 58, 138, 255)         # #1e3a8a
    col_page_left = (37, 99, 235, 255)     # #2563eb
    col_page_right = (14, 165, 233, 255)   # #0ea5e9
    col_paper_rim = (226, 232, 240, 240)   # #e2e8f0
    col_bookmark = (245, 158, 11, 255)     # #f59e0b

    # Dimensions proporcionades per omplir el 85% de l'espai
    page_w = 720
    page_h = 760
    spine_gap = 40

    def make_page(is_left=True, y_offset=0):
        direction = -1 if is_left else 1
        steps = 80
        top_pts = []
        for i in range(steps + 1):
            t = i / steps
            x = cx + direction * (spine_gap + t * page_w)
            # Ondulació natural del paper obert
            curve = -math.sin(t * math.pi) * 110 + (t * 50)
            y = cy - page_h // 2 + curve + y_offset
            top_pts.append((x, y))

        bot_pts = []
        for i in range(steps + 1):
            t = (steps - i) / steps
            x = cx + direction * (spine_gap + t * page_w)
            curve = -math.sin(t * math.pi) * 110 + (t * 50)
            y = cy + page_h // 2 + curve + y_offset
            bot_pts.append((x, y))

        return top_pts + bot_pts

    # 1. Base inferior / Tapa (dona relleu sense recarregar)
    cover_left = make_page(is_left=True, y_offset=45)
    cover_right = make_page(is_left=False, y_offset=45)
    draw.polygon(cover_left, fill=col_cover)
    draw.polygon(cover_right, fill=col_cover)

    # 2. Bloc de fulls (pàgines interiors blanques suaus)
    paper_left = make_page(is_left=True, y_offset=22)
    paper_right = make_page(is_left=False, y_offset=22)
    draw.polygon(paper_left, fill=col_paper_rim)
    draw.polygon(paper_right, fill=col_paper_rim)

    # 3. Pàgines superiors principals
    page_l = make_page(is_left=True, y_offset=0)
    page_r = make_page(is_left=False, y_offset=0)
    draw.polygon(page_l, fill=col_page_left)
    draw.polygon(page_r, fill=col_page_right)

    # 4. Línies minimalistes d'alta claredat a la pàgina esquerra (simulen el text/títol)
    line_col = (255, 255, 255, 200)
    line_positions = [
        (-140, 0.70, 32), # Línia de títol (més gruixuda)
        (-40,  0.80, 22),
        (60,   0.75, 22),
        (160,  0.50, 22)
    ]
    for y_rel, w_scale, l_width in line_positions:
        x_start = cx - 140
        x_end = cx - 140 - int(450 * w_scale)
        y_base = cy + y_rel
        pts = []
        for s in range(25):
            t = s / 24
            px = x_start + t * (x_end - x_start)
            py = y_base - math.sin(t * math.pi * 0.85) * 45
            pts.append((px, py))
        draw.line(pts, fill=line_col, width=l_width)

    # 5. Pàgina dreta: línies elegants representant autor i organització
    right_lines = [
        (-140, 0.60, 22),
        (-40,  0.75, 22),
        (60,   0.65, 22),
        (160,  0.40, 22)
    ]
    for y_rel, w_scale, l_width in right_lines:
        x_start = cx + 140
        x_end = cx + 140 + int(450 * w_scale)
        y_base = cy + y_rel
        pts = []
        for s in range(25):
            t = s / 24
            px = x_start + t * (x_end - x_start)
            py = y_base - math.sin(t * math.pi * 0.85) * 45
            pts.append((px, py))
        draw.line(pts, fill=(255, 255, 255, 190), width=l_width)

    # 6. Cinta central d'ambre/daurada (Bookmark / Renamer accent)
    bm_w = 90
    bm_x1 = cx - bm_w // 2
    bm_x2 = cx + bm_w // 2
    bm_top = cy - page_h // 2 - 110
    bm_bot = cy + 120
    bm_notch = cy + 190

    bm_polygon = [
        (bm_x1, bm_top),
        (bm_x2, bm_top),
        (bm_x2, bm_bot),
        (cx, bm_notch),
        (bm_x1, bm_bot)
    ]
    draw.polygon(bm_polygon, fill=col_bookmark)

    # 7. Redimensionar a 512x512 amb filtre Lanczos d'alta qualitat
    final_png = canvas.resize((512, 512), Image.Resampling.LANCZOS)
    final_png.save(output_png, format='PNG')

    # Generar el fitxer ICO amb totes les capes multi-mida (16px a 256px) amb transparència neta
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    final_png.save(output_ico, format='ICO', sizes=ico_sizes)
    print(f"[OK] Icona PNG generada: {output_png}")
    print(f"[OK] Icona ICO generada: {output_ico}")

if __name__ == '__main__':
    draw_smooth_icon(
        r'C:\Users\mique\Documents\Antigravity\EbookRenamer\assets\icon.png',
        r'C:\Users\mique\Documents\Antigravity\EbookRenamer\assets\icon.ico'
    )
