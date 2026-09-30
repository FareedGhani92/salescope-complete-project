from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_all_pages_load():
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception
    assert len(app.metric) == 4
    for page in ["Sales analysis", "Forecast studio", "Model performance", "Data workspace", "Reports & guide"]:
        app.radio(key="navigation").set_value(page).run()
        assert not app.exception, page


def test_empty_filter_combination_is_explained():
    app = AppTest.from_file(APP, default_timeout=30).run()
    category = next(x for x in app.selectbox if x.label == "Category")
    category.set_value("Electronics").run()
    product = next(x for x in app.selectbox if x.label == "Product")
    product.set_value("Desk lamp").run()
    assert not app.exception
    assert any("No records match" in x.value for x in app.info)


def test_restore_dataset_button():
    app = AppTest.from_file(APP, default_timeout=30).run()
    next(x for x in app.button if x.label == "Restore sample dataset").click().run()
    assert not app.exception


def test_forecast_flow_state_and_downloads():
    app = AppTest.from_file(APP, default_timeout=120).run()
    app.radio(key="navigation").set_value("Forecast studio").run()
    app.selectbox(key="horizon").set_value(7).run()
    next(x for x in app.button if x.label == "Generate forecast").click().run()
    assert not app.exception
    assert len(app.metric) == 3
    app.radio(key="navigation").set_value("Model performance").run()
    assert not app.exception
    assert len(app.metric) == 4
    app.radio(key="navigation").set_value("Reports & guide").run()
    assert not app.exception
    assert len(app.get("download_button")) == 4
    next(x for x in app.selectbox if x.label == "Currency label").set_value("EUR").run()
    assert not app.exception
    assert len(app.get("download_button")) == 0
