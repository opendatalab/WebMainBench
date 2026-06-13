"""
HTML cleanup helpers.
"""

import re


_ANNOTATION_TAG_RE = re.compile(
    r"</?(?:marked-tail|marked-text|marked-inline)\b[^>]*>",
    re.IGNORECASE,
)
_ANNO_ATTR_RE = re.compile(
    r"\s+data-anno-uid(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+))?",
    re.IGNORECASE,
)


def clean_browser_annotation_artifacts(html: str) -> str:
    """Remove browser annotation plugin artifacts while preserving page text."""
    if not html:
        return html

    html = _ANNOTATION_TAG_RE.sub("", html)
    html = _ANNO_ATTR_RE.sub("", html)
    return html
