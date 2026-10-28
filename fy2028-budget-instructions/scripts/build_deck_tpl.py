"""Rebuild Byron's FY2028 Budget Instructions content on the look of
FY2028_Maziv_BudgetInstructions_v1_Template.pptx (the 'Maziv template' deck).

Content source : Byron's deck (every paragraph, run, table cell and note, verbatim).
Look source    : the template deck's master/theme/fonts/colours/footer and composition,
                 laid out on A4 landscape.
Usage: python3 -I build_deck_tpl.py BYRON.pptx TEMPLATE.pptx OUT.pptx
"""
import sys
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn

SRC, TPL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
MEDIA = "tpl_media"   # logos extracted from the template deck

# ---- template palette (exact hexes used in the template deck) ---------------
PURPLE, PURPLE_M, LILAC, WASH, PAGE = "461B55", "7A4D87", "C09CCD", "F4ECF7", "F7F5F0"
INK, MUTE, LINE, PAPER = "1F2937", "747474", "D1D1D1", "FFFFFF"
FONT = "Calibri"
FOOTER_TEXT = "Maziv Group  •  FY2028 Budget Instructions  •  Strictly confidential"

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
W, H = 11.69, 8.27                     # A4 landscape, inches

src = Presentation(SRC)
prs = Presentation(TPL)
S = src.slides
N = len(S)

prs.slide_width, prs.slide_height = Emu(10692000), Emu(7559675)   # A4 landscape

for sldId in list(prs.slides._sldIdLst):            # strip the template's own slides
    prs.part.drop_rel(sldId.rId)
    prs.slides._sldIdLst.remove(sldId)
layout = prs.slide_masters[0].slide_layouts[0]       # the template's single DEFAULT layout
report = []


# ---- content helpers --------------------------------------------------------------
def runs_of(paragraph):
    out = []
    for r in paragraph.runs:
        b = bool(r.font.bold)
        hl = r._r.find(f".//{{{A_NS}}}highlight") is not None
        if out and out[-1][1] == b and out[-1][2] == hl:
            out[-1][0] += r.text
        else:
            out.append([r.text, b, hl])
    return [(t, b, h) for t, b, h in out]


def paras_of(tf):
    return [(p.level, runs_of(p)) for p in tf.paragraphs if "".join(r.text for r in p.runs)]


def by_name(slide, name):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    raise KeyError(name)


def title_text(slide):
    return "".join(r.text for p in slide.shapes.title.text_frame.paragraphs for r in p.runs)


def set_bullet(p, mode, lvl=0):
    pPr = p._p.get_or_add_pPr()
    for tag in ("a:buNone", "a:buChar", "a:buSzPct", "a:buFont"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    if mode == "none":
        pPr.set("marL", "0")
        pPr.set("indent", "0")
        etree.SubElement(pPr, qn("a:buNone"))
    else:
        pPr.set("marL", str(152400 * (lvl + 1)))
        pPr.set("indent", "-152400")
        etree.SubElement(pPr, qn("a:buSzPct")).set("val", "100000")
        etree.SubElement(pPr, qn("a:buChar")).set("char", "•")


def style_run(r, size, color, bold=None, italic=None):
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        r.font.bold = bold
    if italic is not None:
        r.font.italic = italic


def fill_tf(tf, paras, size, color, bold=None, bullet=None, space_after=None, align=None,
            heading=None, keep_hl=True):
    tf.clear()
    first = True
    for i, (lvl, runs) in enumerate(paras):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        if align is not None:
            p.alignment = align
        if space_after is not None:
            p.space_after = Pt(space_after)
        is_head = heading is not None and i == 0
        for text, b, hl in runs:
            r = p.add_run()
            r.text = text
            if is_head:
                style_run(r, heading[0], heading[1], bold=True)
            else:
                style_run(r, size, color, bold=(bold if bold is not None else (True if b else None)))
            if hl and keep_hl:
                rPr = r._r.get_or_add_rPr()
                h = etree.SubElement(rPr, qn("a:highlight"))
                etree.SubElement(h, qn("a:srgbClr")).set("val", "FFFF00")
        if is_head:
            set_bullet(p, "none")
        elif bullet == "none":
            set_bullet(p, "none")
        elif bullet == "char":
            set_bullet(p, "char", lvl)
    return tf


def set_notes(slide, text):
    """Write speaker notes; the template's notes master lacks a body placeholder, so add one."""
    ns = slide.notes_slide
    if ns.notes_text_frame is None:
        sp = etree.SubElement(ns.shapes._spTree, qn("p:sp"))
        nv = etree.SubElement(sp, qn("p:nvSpPr"))
        c = etree.SubElement(nv, qn("p:cNvPr")); c.set("id", "2"); c.set("name", "Notes Placeholder 2")
        etree.SubElement(nv, qn("p:cNvSpPr")).append(etree.Element(qn("a:spLocks"), noGrp="1"))
        etree.SubElement(etree.SubElement(nv, qn("p:nvPr")), qn("p:ph")).attrib.update({"type": "body", "idx": "1"})
        etree.SubElement(sp, qn("p:spPr"))
        tx = etree.SubElement(sp, qn("p:txBody"))
        etree.SubElement(tx, qn("a:bodyPr")); etree.SubElement(tx, qn("a:lstStyle")); etree.SubElement(tx, qn("a:p"))
    ns.notes_text_frame.text = text


def box(slide, name, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    return tb


def rect(slide, name, x, y, w, h, fill, line=None, line_w=1.0, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.name = name
    s.fill.solid()
    s.fill.fore_color.rgb = RGBColor.from_string(fill)
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = RGBColor.from_string(line)
        s.line.width = Pt(line_w)
    s.shadow.inherit = False
    if s.has_text_frame:                      # keep autoshapes text-free for verification
        s.text_frame.clear()
    return s


def card(slide, x, y, w, h, top_strip=True):
    rect(slide, "Card", x, y, w, h, PAPER, line=LINE, line_w=1.0)
    if top_strip:
        rect(slide, "Card strip", x, y, w, 0.04, LILAC)


def callout(slide, x, y, w, h):
    rect(slide, "Callout", x, y, w, h, WASH)
    rect(slide, "Callout bar", x, y, 0.06, h, LILAC)


def header(slide, src_slide):
    t = box(slide, src_slide.shapes.title.name, 0.40, 0.08, 10.9, 0.45, anchor=MSO_ANCHOR.MIDDLE)
    r = t.text_frame.paragraphs[0].add_run()
    r.text = title_text(src_slide)
    style_run(r, 22, PAPER, bold=True)


# ---- table helper -----------------------------------------------------------------
def _ln(side, color, w_pt=0.5):
    ln = etree.Element(qn(f"a:ln{side}"))
    ln.set("w", str(int(w_pt * 12700)))
    ln.set("cap", "flat"); ln.set("cmpd", "sng"); ln.set("algn", "ctr")
    sf = etree.SubElement(ln, qn("a:solidFill"))
    etree.SubElement(sf, qn("a:srgbClr")).set("val", color)
    etree.SubElement(ln, qn("a:prstDash")).set("val", "solid")
    return ln


def add_table(slide, src_shape, x, y, col_widths, head_h, row_h, head_size=11, body_size=10):
    st = src_shape.table
    nrows, ncols = len(st.rows), len(st.columns)
    gf = slide.shapes.add_table(nrows, ncols, Inches(x), Inches(y), Inches(sum(col_widths)),
                                Inches(head_h + row_h * (nrows - 1)))
    gf.name = src_shape.name
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    tblPr.set("firstRow", "1"); tblPr.set("bandRow", "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None:
        sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
    sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"
    for ci, cw in enumerate(col_widths):
        tbl.columns[ci].width = Inches(cw)
    for ri in range(nrows):
        tbl.rows[ri].height = Inches(head_h if ri == 0 else row_h)
        for ci in range(ncols):
            scell, cell = st.cell(ri, ci), tbl.cell(ri, ci)
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string(PURPLE if ri == 0 else (PAPER if ri % 2 else PAGE))
            tcPr = cell._tc.get_or_add_tcPr()
            for i, side in enumerate(("L", "R", "T", "B")):
                tcPr.insert(i, _ln(side, LINE))
            tf = cell.text_frame
            tf.word_wrap = True
            paras = [(p.level, runs_of(p)) for p in scell.text_frame.paragraphs] or [(0, [])]
            first = True
            for lvl, runs in paras:
                p = tf.paragraphs[0] if first else tf.add_paragraph()
                first = False
                for text, b, hl in runs:
                    r = p.add_run()
                    r.text = text
                    if ri == 0:
                        style_run(r, head_size, PAPER, bold=True)
                    elif text.strip() == "NEW":
                        style_run(r, 9, PURPLE_M, bold=True)
                    else:
                        style_run(r, body_size, INK, bold=(True if (ci == 0 or b) else None))
                    if hl:
                        rPr = r._r.get_or_add_rPr()
                        h = etree.SubElement(rPr, qn("a:highlight"))
                        etree.SubElement(h, qn("a:srgbClr")).set("val", "FFFF00")
                        report.append(f"Byron's yellow highlight on '{scell.text}' kept as-is (reviewer marker).")
    return gf


# ---- chrome on the layout: band, accent line, footer rule, footer text, page no., logo ----
def build_chrome():
    tmp = prs.slides.add_slide(layout)
    shapes = []
    shapes.append(rect(tmp, "Header band", 0, 0, W, 0.60, PURPLE))
    shapes.append(rect(tmp, "Header accent", 0, 0.60, W, 0.04, LILAC))
    shapes.append(rect(tmp, "Footer rule", 0.40, H - 0.44, W - 0.80, 0.01, LINE))
    ft = box(tmp, "Footer text", 0.40, H - 0.40, 7.0, 0.28, anchor=MSO_ANCHOR.MIDDLE)
    r = ft.text_frame.paragraphs[0].add_run()
    r.text = FOOTER_TEXT
    style_run(r, 9, MUTE, italic=True)
    shapes.append(ft)
    pn = box(tmp, "Page number", W - 0.40 - 1.30 - 3.5, H - 0.40, 3.5, 0.28, anchor=MSO_ANCHOR.MIDDLE)
    p = pn.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    fld = etree.SubElement(p._p, qn("a:fld"))
    fld.set("id", "{B6F15528-21DB-4D62-9E3B-7A1C0A5D2F10}"); fld.set("type", "slidenum")
    rPr = etree.SubElement(fld, qn("a:rPr")); rPr.set("lang", "en-ZA"); rPr.set("sz", "900")
    sf = etree.SubElement(rPr, qn("a:solidFill")); etree.SubElement(sf, qn("a:srgbClr")).set("val", MUTE)
    etree.SubElement(rPr, qn("a:latin")).set("typeface", FONT)
    etree.SubElement(fld, qn("a:t")).text = "1"
    r2 = p.add_run(); r2.text = f" / {N}"; style_run(r2, 9, MUTE)
    shapes.append(pn)
    pic = tmp.shapes.add_picture(f"{MEDIA}/image2.png", Inches(W - 0.40 - 0.90), Inches(H - 0.37), Inches(0.90), Inches(0.16))
    pic.name = "Logo"
    # re-home the picture relationship on the layout part
    img_part = tmp.part.related_part(pic._element.blip_rId)
    new_rId = layout.part.relate_to(img_part, RT.IMAGE)
    pic._element.find(f".//{{{A_NS}}}blip").set(qn("r:embed"), new_rId)
    shapes.append(pic)
    spTree = layout.shapes._spTree
    for i, shp in enumerate(shapes):
        el = shp._element
        el.getparent().remove(el)
        el.find(f".//{{{P_NS}}}cNvPr").set("id", str(9001 + i))
        spTree.append(el)
    sid = prs.slides._sldIdLst[-1]
    prs.part.drop_rel(sid.rId)
    prs.slides._sldIdLst.remove(sid)


build_chrome()

# ============================================================================
# SLIDE 1 — cover: full-bleed purple, lilac left bar, white landscape logo
# ============================================================================
s1 = prs.slides.add_slide(layout)
src1 = S[0]
rect(s1, "Cover ground", 0, 0, W, H, PURPLE)
rect(s1, "Cover bar", 0, 0, 0.40, H, LILAC)
logo = s1.shapes.add_picture(f"{MEDIA}/image1.png", Inches(W - 0.55 - 3.40), Inches(0.50), Inches(3.40), Inches(1.57))
logo.name = "Logo"
cp = paras_of(by_name(src1, "Subtitle 2").text_frame)
t = box(s1, "Subtitle 2", 1.10, 3.00, 9.8, 1.40, anchor=MSO_ANCHOR.MIDDLE)
fill_tf(t.text_frame, cp[:1], 36, PAPER, bold=True, bullet="none")
st_ = box(s1, "Subtitle 2 (line 2)", 1.10, 4.45, 9.8, 0.80, anchor=MSO_ANCHOR.MIDDLE)
fill_tf(st_.text_frame, cp[1:], 20, PAPER, bullet="none")

# ============================================================================
# SLIDE 2 — four principle cards (2 x 2)
# ============================================================================
s2 = prs.slides.add_slide(layout)
src2 = S[1]
header(s2, src2)
CW, CH, GX = (W - 0.80 - 0.30) / 2, 3.32, 0.30
quad = [("Text Placeholder 2", "Content Placeholder 3", 0.40, 0.88),
        ("Text Placeholder 6", "Content Placeholder 7", 0.40 + CW + GX, 0.88),
        ("Text Placeholder 4", "Content Placeholder 5", 0.40, 0.88 + CH + 0.15),
        ("Text Placeholder 8", "Content Placeholder 9", 0.40 + CW + GX, 0.88 + CH + 0.15)]
for hname, cname, x, y in quad:
    card(s2, x, y, CW, CH, top_strip=False)
    h = box(s2, hname, x + 0.20, y + 0.15, CW - 0.40, 0.45, anchor=MSO_ANCHOR.MIDDLE)
    fill_tf(h.text_frame, paras_of(by_name(src2, hname).text_frame), 14, PURPLE, bold=True, bullet="none")
    c = box(s2, cname, x + 0.20, y + 0.65, CW - 0.40, CH - 0.80)
    fill_tf(c.text_frame, paras_of(by_name(src2, cname).text_frame), 12, INK, bullet="char", space_after=5)

# ============================================================================
# SLIDE 3 — process flow, two rule panels, draft tag, note
# ============================================================================
s3 = prs.slides.add_slide(layout)
src3 = S[2]
header(s3, src3)
n, gap = 5, 0.08
sw = (W - 0.80 - gap * (n - 1)) / n
for i in range(1, n + 1):
    x = 0.40 + (i - 1) * (sw + gap)
    a_src = by_name(src3, f"Step {i} arrow")
    shp = rect(s3, a_src.name, x, 0.92, sw, 0.62, PURPLE if i % 2 else PURPLE_M, line=PAPER, line_w=1.5,
               shape=MSO_SHAPE.PENTAGON if i == 1 else MSO_SHAPE.CHEVRON)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.18)
    fill_tf(tf, paras_of(a_src.text_frame), 12, PAPER, bold=True, bullet="none", align=PP_ALIGN.CENTER)
    t_src = by_name(src3, f"Step {i} text")
    tb = box(s3, t_src.name, x + 0.05, 1.65, sw - 0.10, 1.65)
    fill_tf(tb.text_frame, paras_of(t_src.text_frame), 11, INK, bullet="none", space_after=3, heading=(11, PURPLE))
PY, PH = 3.45, 2.45
for name, x in (("Rules left", 0.40), ("Rules right", 0.40 + CW + GX)):
    card(s3, x, PY, CW, PH, top_strip=True)
    tb = box(s3, name, x + 0.15, PY + 0.12, CW - 0.30, PH - 0.25)
    fill_tf(tb.text_frame, paras_of(by_name(src3, name).text_frame), 12, INK, bullet="char", space_after=8,
            heading=(12, PURPLE))
tag = box(s3, "Draft tag", W - 0.40 - 4.5, H - 0.80, 4.5, 0.28, anchor=MSO_ANCHOR.MIDDLE)
fill_tf(tag.text_frame, paras_of(by_name(src3, "Draft tag").text_frame), 9, MUTE, bullet="none", align=PP_ALIGN.RIGHT)
set_notes(s3, src3.notes_slide.notes_text_frame.text)

# ============================================================================
# SLIDES 4–8 — tables
# ============================================================================
TW = W - 0.80
SPECS = {
    4: dict(col_widths=[4.60, TW - 4.60], head_h=0.36, row_h=0.40),
    5: dict(col_widths=[3.70, 2.45, TW - 6.15], head_h=0.36, row_h=0.50),
    6: dict(col_widths=[5.45, 2.20, TW - 7.65], head_h=0.36, row_h=0.47),
    7: dict(col_widths=[5.69, 2.00, TW - 7.69], head_h=0.36, row_h=0.60),
    8: dict(col_widths=[3.30, TW - 3.30], head_h=0.36, row_h=0.58),
}
for k in range(4, 9):
    s = prs.slides.add_slide(layout)
    srcs = S[k - 1]
    header(s, srcs)
    add_table(s, by_name(srcs, "Table"), 0.40, 0.88, **SPECS[k])
    if k == 7:
        fn_src = by_name(srcs, "Footnote")
        callout(s, 0.40, 6.35, TW, 0.70)
        fn = box(s, fn_src.name, 0.58, 6.42, TW - 0.36, 0.56, anchor=MSO_ANCHOR.MIDDLE)
        fill_tf(fn.text_frame, paras_of(fn_src.text_frame), 11, INK, bullet="none")
    if srcs.has_notes_slide and srcs.notes_slide.notes_text_frame.text.strip():
        set_notes(s, srcs.notes_slide.notes_text_frame.text)

prs.save(OUT)
print(f"wrote {OUT}: {len(prs.slides)} slides")
for line in dict.fromkeys(report):
    print("NOTE:", line)
