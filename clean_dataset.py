"""
clean.py — Strip browser annotation plugin artifacts from WebMainBench JSONL files.

Fix Method (from issue.md)
--------------------------
_ANNOTATION_TAG_RE = re.compile(
    r'</?(?:marked-tail|marked-text|marked-inline)[^>]*>', re.IGNORECASE
)
_ANNO_ATTR_RE = re.compile(r'\\s+data-anno-uid="[^"]*"', re.IGNORECASE)

def clean_html(html: str) -> str:
    html = _ANNOTATION_TAG_RE.sub('', html)
    html = _ANNO_ATTR_RE.sub('', html)
    return html

Cleaned fields: html, main_html (both present in the dataset)
"""

import json
import re
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Compiled patterns (strictly from issue.md)
# ---------------------------------------------------------------------------

_ANNOTATION_TAG_RE = re.compile(
    r'</?(?:marked-tail|marked-text|marked-inline)[^>]*>',
    re.IGNORECASE,
)

_ANNO_ATTR_RE = re.compile(
    r'\s+data-anno-uid="[^"]*"',
    re.IGNORECASE,
)


def clean_html(html: str) -> str:
    """Strip browser annotation plugin artifacts from saved HTML."""
    html = _ANNOTATION_TAG_RE.sub('', html)
    html = _ANNO_ATTR_RE.sub('', html)
    return html


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

_MARKED_TAIL_RE = re.compile(r'</?marked-tail', re.IGNORECASE)
_MARKED_TEXT_RE = re.compile(r'</?marked-text', re.IGNORECASE)


def collect_stats(html: str) -> dict:
    return {
        'marked_tail': bool(_MARKED_TAIL_RE.search(html)),
        'marked_text': bool(_MARKED_TEXT_RE.search(html)),
        'anno_uid':    bool(_ANNO_ATTR_RE.search(html)),
    }


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

HTML_FIELDS = ('html', 'main_html')


def process_file(src: Path, dst: Path) -> dict:
    """Clean src, write to dst, return aggregate stats."""
    totals = {'marked_tail': 0, 'marked_text': 0, 'anno_uid': 0}
    n_records = 0

    with src.open(encoding='utf-8') as fin, dst.open('w', encoding='utf-8') as fout:
        for raw in fin:
            raw = raw.strip()
            if not raw:
                continue
            obj = json.loads(raw)
            n_records += 1

            for field in HTML_FIELDS:
                val = obj.get(field)
                if not isinstance(val, str):
                    continue
                stats = collect_stats(val)
                for k, v in stats.items():
                    if v:
                        totals[k] += 1
                obj[field] = clean_html(val)

            fout.write(json.dumps(obj, ensure_ascii=False) + '\n')

    return {'n_records': n_records, **totals}


DEFAULT_INPUTS = [
    'data/WebMainBench_545.jsonl',
    'data/webmainbench.jsonl',
]
DEFAULT_OUTDIR = 'cleaned_output'


def main():
    parser = argparse.ArgumentParser(description='Clean WebMainBench JSONL files')
    parser.add_argument('inputs', nargs='*', default=DEFAULT_INPUTS, help='Input JSONL file(s)')
    parser.add_argument('--outdir', default=DEFAULT_OUTDIR, help='Output directory (default: cleaned_output)')
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for src_path in args.inputs:
        src = Path(src_path)
        dst = outdir / (src.stem + '_cleaned' + src.suffix)
        print(f'Processing {src} → {dst}')
        stats = process_file(src, dst)
        print(f"  Records     : {stats['n_records']}")
        print(f"  marked-tail : {stats['marked_tail']}")
        print(f"  marked-text : {stats['marked_text']}")
        print(f"  anno-uid    : {stats['anno_uid']}")
        print()


if __name__ == '__main__':
    main()
