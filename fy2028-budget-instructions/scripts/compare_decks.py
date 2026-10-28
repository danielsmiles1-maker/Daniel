"""Compare two decks slide by slide and write verification.xlsx.

Usage: python3 -I compare_decks.py SOURCE.pptx NEW.pptx verification.xlsx

Items compared per slide:
  * every text paragraph (runs joined) in every shape, recursing into groups
  * every table cell, table k in SOURCE paired with table k in NEW
  * speaker notes
  * every number token found in the slide's text (multiset)
Shape/table names are reported from the SOURCE deck where an item pairs,
otherwise from whichever deck holds the unpaired item.
"""
import re
import sys
import difflib
from collections import Counter

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

NUM_RE = re.compile(r"\d[\d,.]*%?")


def norm(s):
    s = s.replace(" ", " ").replace("’", "'").replace("‘", "'")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def walk(shapes):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from walk(sh.shapes)
        else:
            yield sh


def extract(path):
    prs = Presentation(path)
    slides = []
    for sl in prs.slides:
        paras, tables, nums = [], [], Counter()
        for sh in walk(sl.shapes):
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    t = norm("".join(r.text for r in p.runs))
                    if t:
                        paras.append((sh.name, t))
                        nums.update(NUM_RE.findall(t))
            if getattr(sh, "has_table", False) and sh.has_table:
                cells = []
                for ri, row in enumerate(sh.table.rows):
                    for ci, c in enumerate(row.cells):
                        t = norm(c.text)
                        cells.append((ri, ci, t))
                        nums.update(NUM_RE.findall(t))
                tables.append((sh.name, cells))
        notes = ""
        if sl.has_notes_slide:
            notes = norm(sl.notes_slide.notes_text_frame.text)
            nums.update(NUM_RE.findall(notes))
        slides.append({"paras": paras, "tables": tables, "notes": notes, "nums": nums})
    return slides


def compare(src, new):
    total = matches = 0
    rows = []  # (slide, name, src_val, new_val, kind)

    def mm(slide, name, a, b, kind):
        rows.append((slide, name, a, b, kind))

    n = max(len(src), len(new))
    if len(src) != len(new):
        mm("deck", "slide count", str(len(src)), str(len(new)), "structure")
        total += 1
    else:
        total += 1
        matches += 1

    for i in range(n):
        s = src[i] if i < len(src) else {"paras": [], "tables": [], "notes": "", "nums": Counter()}
        d = new[i] if i < len(new) else {"paras": [], "tables": [], "notes": "", "nums": Counter()}
        sn = i + 1

        # --- paragraphs: exact match first, then nearest-neighbour pairing
        src_p = list(s["paras"])
        new_p = list(d["paras"])
        unmatched_src = []
        for name, t in src_p:
            total += 1
            hit = next((j for j, (_, u) in enumerate(new_p) if u == t), None)
            if hit is not None:
                matches += 1
                new_p.pop(hit)
            else:
                unmatched_src.append((name, t))
        for name, t in unmatched_src:
            if new_p:
                j = max(range(len(new_p)), key=lambda k: difflib.SequenceMatcher(None, t, new_p[k][1]).ratio())
                mm(sn, name, t, new_p.pop(j)[1], "text")
            else:
                mm(sn, name, t, "", "text")
        for name, u in new_p:
            total += 1
            mm(sn, name, "", u, "text (extra in new)")

        # --- tables
        for k in range(max(len(s["tables"]), len(d["tables"]))):
            st = s["tables"][k] if k < len(s["tables"]) else None
            dt = d["tables"][k] if k < len(d["tables"]) else None
            if st is None or dt is None:
                total += 1
                mm(sn, (st or dt)[0], "table present" if st else "", "table present" if dt else "", "table missing")
                continue
            sc = {(r, c): t for r, c, t in st[1]}
            dc = {(r, c): t for r, c, t in dt[1]}
            for key in sorted(set(sc) | set(dc)):
                total += 1
                a, b = sc.get(key, "<no cell>"), dc.get(key, "<no cell>")
                if a == b:
                    matches += 1
                else:
                    mm(sn, f"{st[0]} [r{key[0]+1},c{key[1]+1}]", a, b, "table cell")

        # --- notes
        total += 1
        if s["notes"] == d["notes"]:
            matches += 1
        else:
            mm(sn, "notes", s["notes"], d["notes"], "notes")

        # --- numbers (multiset)
        for tok, cnt in s["nums"].items():
            total += cnt
            got = d["nums"].get(tok, 0)
            matches += min(cnt, got)
            if got < cnt:
                mm(sn, "numbers", f"{tok} x{cnt}", f"{tok} x{got}", "number")
        for tok, cnt in d["nums"].items():
            if tok not in s["nums"]:
                total += cnt
                mm(sn, "numbers", "", f"{tok} x{cnt}", "number (extra in new)")

    return total, matches, rows


def write_xlsx(path, src_path, new_path, total, matches, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    hdr = Font(bold=True, color="FFFFFF")
    fill = PatternFill("solid", fgColor="7C1C91")
    ws.append(["Item", "Value"])
    for c in ws[1]:
        c.font, c.fill = hdr, fill
    result = "PASS" if not rows else "FAIL"
    for r in [
        ("Source deck (Byron)", src_path),
        ("New deck", new_path),
        ("Items compared", total),
        ("Matches", matches),
        ("Mismatches", len(rows)),
        ("Result", result),
        ("Basis", "Paragraph text (runs joined), table cells, speaker notes and number tokens, per slide; whitespace normalised"),
    ]:
        ws.append(list(r))
    ws["B7"].font = Font(bold=True, color="1B7A4B" if result == "PASS" else "B3213C")
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 90

    ws2 = wb.create_sheet("Mismatches")
    ws2.append(["Slide", "Shape / table", "Byron's value", "New deck's value", "Type"])
    for c in ws2[1]:
        c.font, c.fill = hdr, fill
    for r in rows:
        ws2.append(list(r))
    for col, w in zip("ABCDE", (8, 34, 60, 60, 18)):
        ws2.column_dimensions[col].width = w
    for row in ws2.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    wb.save(path)
    return result


if __name__ == "__main__":
    src_path, new_path, out = sys.argv[1:4]
    total, matches, rows = compare(extract(src_path), extract(new_path))
    result = write_xlsx(out, src_path, new_path, total, matches, rows)
    print(f"items={total} matches={matches} mismatches={len(rows)} result={result}")
    for r in rows[:40]:
        print("  ", r)
    sys.exit(0 if result == "PASS" else 1)
