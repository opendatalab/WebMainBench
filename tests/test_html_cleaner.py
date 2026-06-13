from webmainbench.extractors.base import BaseExtractor, ExtractionResult
from webmainbench.utils import clean_browser_annotation_artifacts


class EchoExtractor(BaseExtractor):
    def _setup(self):
        pass

    def _extract_content(self, html: str, url: str = None) -> ExtractionResult:
        return ExtractionResult(content=html)


def test_clean_browser_annotation_artifacts_preserves_text():
    html = (
        '<p data-anno-uid="anno-1">'
        '<marked-text data-anno-uid="anno-2">Hello</marked-text>'
        '<span> </span>'
        "<marked-tail data-anno-uid='anno-3'>world</marked-tail>"
        "</p>"
    )

    cleaned = clean_browser_annotation_artifacts(html)

    assert "Hello" in cleaned
    assert "world" in cleaned
    assert "marked-text" not in cleaned
    assert "marked-tail" not in cleaned
    assert "data-anno-uid" not in cleaned


def test_base_extractor_cleans_annotation_artifacts_by_default():
    extractor = EchoExtractor("echo")

    result = extractor.extract('<p><marked-text data-anno-uid="x">Hello</marked-text></p>')

    assert result.content == "<p>Hello</p>"


def test_base_extractor_can_disable_annotation_cleanup():
    extractor = EchoExtractor("echo", config={"clean_html_annotations": False})
    html = '<p><marked-text data-anno-uid="x">Hello</marked-text></p>'

    result = extractor.extract(html)

    assert result.content == html
