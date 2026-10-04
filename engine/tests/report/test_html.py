from nostrobe.report.html import DISCLAIMER, render


def test_static_trace_only_report_and_escape(track):
    media = track.media.model_copy(update={"content_id": "<script>alert(1)</script>"})
    html = render(track.model_copy(update={"media": media}))
    assert DISCLAIMER in html
    assert "data:image/png;base64," in html
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "<video" not in html and "<iframe" not in html
    assert track.verifier.params_hash in html
