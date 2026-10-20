"""Render the live `wipboard` board as an animated terminal SVG for the README.

Reads real tool output on stdin, so the image in the README cannot drift into
fiction: it is whatever the tool actually printed when it was last regenerated.

    PYTHONIOENCODING=utf-8 wipboard | python scripts/board_svg.py > docs/board.svg

Not imported by anything. It exists so the README asset can be refreshed without
anyone reverse-engineering how it was drawn.
"""
import html
import sys

CH = 7.8          # monospace advance at 13px
LH = 20           # line height
PAD = 22
TOP = 56          # below the title bar
NOTE_MAX = 38

STAGE_COLOR = {
    "idea": "#8b93a7",
    "spec": "#79c0ff",
    "building": "#e3b341",
    "testing": "#d2a8ff",
    "shipped": "#3fb950",
    "parked": "#6e7681",
}
FLAGS = ("!", "stuck", "dirty", "no", "missing")


def split_row(line, cols):
    """Slice a rendered row at the column offsets taken from the header."""
    out = []
    for i, start in enumerate(cols):
        end = cols[i + 1] if i + 1 < len(cols) else len(line)
        out.append(line[start:end].rstrip())
    return out


def main():
    lines = [ln.rstrip("\n") for ln in sys.stdin if ln.strip()]
    header, rows = lines[0], lines[1:]
    cols = [header.index(h) for h in ("PROJECT", "STAGE", "TOUCHED", "NOTE")]

    parsed = []
    for line in rows:
        name, stage, touched, rest = split_row(line, cols)
        words = rest.split()
        flags, note = [], []
        for w in words:
            if not note and (w in FLAGS or w.startswith("^") or (flags and flags[-1] in ("stuck", "no"))):
                flags.append(w)
            else:
                note.append(w)
        note = " ".join(note)
        if len(note) > NOTE_MAX:
            note = note[: NOTE_MAX - 1] + "…"
        parsed.append((name, stage, touched, " ".join(flags), note))

    # Column x positions, in characters, from the widest cell in each column.
    w_name = max([len("PROJECT")] + [len(p[0]) for p in parsed])
    w_stage = max([len("STAGE")] + [len(p[1]) for p in parsed])
    w_touch = max([len("TOUCHED")] + [len(p[2]) for p in parsed])
    w_flags = max([0] + [len(p[3]) for p in parsed])
    w_note = max([len("NOTE")] + [len(p[4]) for p in parsed])
    x_name, x_stage = 0, w_name + 2
    x_touch = x_stage + w_stage + 2
    x_flags = x_touch + w_touch + 2
    x_note = x_flags + w_flags + (2 if w_flags else 0)

    width = int(PAD * 2 + (x_note + w_note) * CH) + 10
    height = TOP + LH * (len(parsed) + 1) + PAD

    def x(chars):
        return round(PAD + chars * CH, 1)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="ui-monospace,SFMono-Regular,'
        f'Menlo,Consolas,monospace" font-size="13">',
        "<style>",
        "  .r{opacity:0}",
        "  .c{opacity:0}",
        # One shared timeline: prompt types, then rows drop in, then it holds.
        "  @keyframes in{to{opacity:1}}",
        "  @keyframes blink{50%{opacity:0}}",
        f"  .c{{animation:in .01s linear forwards}}",
        f"  .r{{animation:in .18s ease-out forwards}}",
        "  .cur{animation:blink 1s step-end infinite}",
        "</style>",
        f'<rect width="{width}" height="{height}" rx="10" fill="#0d1117"/>',
        f'<rect width="{width}" height="34" rx="10" fill="#161b22"/>',
        f'<rect y="24" width="{width}" height="10" fill="#161b22"/>',
        '<circle cx="20" cy="17" r="5" fill="#ff5f57"/>',
        '<circle cx="38" cy="17" r="5" fill="#febc2e"/>',
        '<circle cx="56" cy="17" r="5" fill="#28c840"/>',
    ]

    # The typed command, one character at a time.
    cmd = "wipboard"
    out.append(f'<text x="{x(0)}" y="{TOP - 6}" fill="#3fb950">$</text>')
    for i, ch in enumerate(cmd):
        delay = 0.12 + i * 0.07
        out.append(
            f'<text class="c" x="{x(2 + i)}" y="{TOP - 6}" fill="#e6edf3" '
            f'style="animation-delay:{delay:.2f}s">{html.escape(ch)}</text>'
        )
    cur_delay = 0.12 + len(cmd) * 0.07
    out.append(
        f'<rect class="cur" x="{x(2 + len(cmd))}" y="{TOP - 17}" width="7" height="14" '
        f'fill="#e6edf3" style="animation-delay:{cur_delay:.2f}s"/>'
    )

    base = cur_delay + 0.25
    hy = TOP + LH
    for label, cx in (("PROJECT", x_name), ("STAGE", x_stage), ("TOUCHED", x_touch), ("NOTE", x_note)):
        out.append(
            f'<text class="r" x="{x(cx)}" y="{hy}" fill="#6e7681" '
            f'style="animation-delay:{base:.2f}s">{label}</text>'
        )

    for i, (name, stage, touched, flags, note) in enumerate(parsed):
        y = hy + LH * (i + 1)
        d = base + 0.12 + i * 0.055
        style = f'style="animation-delay:{d:.2f}s"'
        out.append(f'<g class="r" {style}>')
        out.append(f'<text x="{x(x_name)}" y="{y}" fill="#e6edf3">{html.escape(name)}</text>')
        out.append(
            f'<text x="{x(x_stage)}" y="{y}" fill="{STAGE_COLOR.get(stage, "#8b93a7")}">'
            f"{html.escape(stage)}</text>"
        )
        out.append(f'<text x="{x(x_touch)}" y="{y}" fill="#8b93a7">{html.escape(touched)}</text>')
        if flags:
            colour = "#f85149" if flags.startswith("!") else "#6e7681"
            weight = ' font-weight="700"' if flags.startswith("!") else ""
            out.append(
                f'<text x="{x(x_flags)}" y="{y}" fill="{colour}"{weight}>{html.escape(flags)}</text>'
            )
        if note:
            out.append(f'<text x="{x(x_note)}" y="{y}" fill="#6e7681">{html.escape(note)}</text>')
        out.append("</g>")

    out.append("</svg>")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
