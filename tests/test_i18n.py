import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


UI_DIR = Path(__file__).resolve().parent.parent / "app" / "static" / "ui"

client = TestClient(app)


def language_blocks() -> dict[str, set[str]]:
    source = (UI_DIR / "i18n.js").read_text(encoding="utf-8")
    blocks = re.findall(
        r"^  (\w+): \{\n(.*?)^  \},", source, flags=re.MULTILINE | re.DOTALL
    )
    return {
        language: set(re.findall(r'^    "([^"]+)":', body, flags=re.MULTILINE))
        for language, body in blocks
    }


def test_i18n_script_is_served_and_loaded_before_ui_script():
    html = client.get("/ui/").text

    assert client.get("/ui/i18n.js").status_code == 200
    assert html.index('src="i18n.js"') < html.index('src="ui.js"')


def test_all_languages_define_the_same_keys():
    blocks = language_blocks()

    assert {"de", "en"} <= set(blocks)
    for language, keys in blocks.items():
        assert keys == blocks["de"], language


def test_page_and_script_only_use_defined_keys():
    keys = language_blocks()["de"]
    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    script = (UI_DIR / "ui.js").read_text(encoding="utf-8")

    used = set(re.findall(r'data-i18n(?:-[\w-]+)?="([^"]+)"', html))
    used |= set(re.findall(r'\bt\("([^"]+)"', script))

    assert used
    assert used <= keys, sorted(used - keys)