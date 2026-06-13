from webmainbench.extractors.trafilatura_extractor import (
    TrafilaturaExtractor as MarkdownTrafilaturaExtractor,
)
from webmainbench.extractors.trafilatura_txt_extractor import (
    TrafilaturaExtractor as TextTrafilaturaExtractor,
)


def test_trafilatura_markdown_defaults_match_standard_options():
    extractor = MarkdownTrafilaturaExtractor("trafilatura")

    assert extractor.inference_config.favor_precision is False
    assert extractor.inference_config.favor_recall is False
    assert extractor.inference_config.include_comments is True
    assert extractor.inference_config.output_format == "markdown"


def test_trafilatura_txt_defaults_to_extract_txt(monkeypatch):
    calls = {}

    def fake_extract(html, **kwargs):
        calls["html"] = html
        calls["kwargs"] = kwargs
        return "plain text"

    monkeypatch.setattr(
        "webmainbench.extractors.trafilatura_txt_extractor.extract",
        fake_extract,
    )
    extractor = TextTrafilaturaExtractor("trafilatura_txt")

    result = extractor.extract("<html><body>plain text</body></html>", url="https://example.com")

    assert result.content == "plain text"
    assert calls["kwargs"]["url"] == "https://example.com"
    assert calls["kwargs"]["favor_precision"] is False
    assert calls["kwargs"]["favor_recall"] is False
    assert calls["kwargs"]["include_comments"] is True
    assert calls["kwargs"]["output_format"] == "txt"
