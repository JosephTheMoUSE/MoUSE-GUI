from pytestqt.qt_compat import qt_api

from mouseapp.view import widgets
from mouseapp.view.main_view import ProjectTab
from tests.model_fixtures import *  # noqa F401 F403


def test_show_key_value_window(qtbot, clean_main_model):
    """Tests if new key value window is shown when + button gets clicked."""
    widget = ProjectTab(clean_main_model)
    qtbot.addWidget(widget)

    qtbot.mouseClick(widget.addMetadataButton, qt_api.QtCore.Qt.MouseButton.LeftButton)

    assert widget.active_new_key_value_widget is not None
    assert widget.active_new_key_value_widget.isVisible()


def test_add_new_key_value_string_to_model(qtbot, clean_main_model):
    widget = widgets.NewKeyValue(clean_main_model)
    qtbot.addWidget(widget)

    widget.keyEditField.setText("test-key")
    widget.valueEditField.setText("test-value")
    qtbot.mouseClick(widget.addKeyValueButton, qt_api.QtCore.Qt.MouseButton.LeftButton)

    assert "test-key" in clean_main_model.project_model.project_metadata
    assert clean_main_model.project_model.project_metadata["test-key"] == (
        "test-value",
        "Text",
    )


def test_add_new_key_value_int_to_model(qtbot, clean_main_model):
    widget = widgets.NewKeyValue(clean_main_model)
    qtbot.addWidget(widget)

    widget.keyEditField.setText("test-key")
    widget.valueEditField.setText("2.0")
    widget.valueTypeComboBox.setCurrentText("Integer")
    qtbot.mouseClick(widget.addKeyValueButton, qt_api.QtCore.Qt.MouseButton.LeftButton)

    assert "test-key" in clean_main_model.project_model.project_metadata
    assert clean_main_model.project_model.project_metadata["test-key"] == (2, "Integer")


def test_add_new_key_value_float_to_model(qtbot, clean_main_model):
    widget = widgets.NewKeyValue(clean_main_model)
    qtbot.addWidget(widget)

    widget.keyEditField.setText("test-key")
    widget.valueEditField.setText("2.2")
    widget.valueTypeComboBox.setCurrentText("Real")
    qtbot.mouseClick(widget.addKeyValueButton, qt_api.QtCore.Qt.MouseButton.LeftButton)

    assert "test-key" in clean_main_model.project_model.project_metadata
    assert clean_main_model.project_model.project_metadata["test-key"] == (2.2, "Real")


def test_show_new_key_value_in_project_tab(qtbot, clean_main_model):
    project_tab = ProjectTab(clean_main_model)
    qtbot.addWidget(project_tab)
    new_key_value_widget = widgets.NewKeyValue(clean_main_model)
    qtbot.addWidget(new_key_value_widget)
    project_tab.active_new_key_value_widget = new_key_value_widget

    new_key_value_widget.keyEditField.setText("test-key")
    new_key_value_widget.valueEditField.setText("test-value")
    qtbot.mouseClick(new_key_value_widget.addKeyValueButton,
                     qt_api.QtCore.Qt.MouseButton.LeftButton)

    # Check if new key value widget was closed
    assert not new_key_value_widget.isVisible()
    # Check if key value widget is visible and has proper settings
    assert "test-key" in project_tab.key_value_widgets
    assert project_tab.key_value_widgets["test-key"].isVisibleTo(project_tab)
    assert project_tab.key_value_widgets["test-key"].keyLabel.text() == "test-key"
    assert (project_tab.key_value_widgets["test-key"].valueEditField.toPlainText() ==
            "test-value")
    assert (project_tab.key_value_widgets["test-key"].valueTypeComboBox.currentText() ==
            "Text")


def test_remove_key_value_from_model(qtbot, main_model):
    widget = widgets.KeyValue(main_model, ("key-1", "value", "Text"))
    qtbot.addWidget(widget)

    qtbot.mouseClick(widget.removeKeyValueButton,
                     qt_api.QtCore.Qt.MouseButton.LeftButton)

    assert "test-key" not in main_model.project_model.project_metadata


def test_remove_key_value_from_project_tab(qtbot, main_model):
    project_tab = ProjectTab(main_model)
    qtbot.addWidget(project_tab)
    project_tab.active_new_key_value_widget = widgets.NewKeyValue(main_model)
    project_tab._on_project_metadata_added(("key-1", "value", "Text"))

    key_value_widget = project_tab.key_value_widgets["key-1"]
    qtbot.mouseClick(key_value_widget.removeKeyValueButton,
                     qt_api.QtCore.Qt.MouseButton.LeftButton)

    assert not key_value_widget.isVisibleTo(project_tab)
    assert "key-1" not in project_tab.key_value_widgets
