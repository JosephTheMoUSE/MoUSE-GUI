from pathlib import Path

from PySide6 import QtCore
from pytestqt.qt_compat import qt_api

from mouseapp.view.main_view import ProjectTab
from mouseapp.view.project_init_view import InitializeProjectWindow
from mouseapp.view.widgets import FileName
from tests.model_fixtures import *  # noqa F401 F403
from unittest import mock


@mock.patch("mouseapp.view.main_view.main_controller.update_signal_data")
def test_project_tab_updates(qtbot, main_model, empty_main_model):
    new_project_window = InitializeProjectWindow(next_model=main_model,
                                                 old_model=empty_main_model,
                                                 old_widget=None)
    main_model.project_model.audio_files = [
        Path("/some/path/file.wav"),
        Path("/some/path/folder/file.wav"),
    ]
    main_model.project_model.first_not_common_character = 11

    qtbot.addWidget(new_project_window)
    project_tab = ProjectTab(main_model)
    qtbot.addWidget(project_tab)
    main_model.project_model.emit_all_setting_signals()

    qtbot.mouseClick(
        new_project_window.load_audio_widget.buttonFinish,
        qt_api.QtCore.Qt.MouseButton.LeftButton,
    )
    files_in_file_list = set(
        item.fileName.text() for item in project_tab.fileList.findChildren(FileName))
    assert project_tab.projectNameEdit.text() == "project_name"
    assert project_tab.noteEdit.toPlainText() == "42"
    assert project_tab.dateEdit.date() == QtCore.QDate(2136, 6, 17)
    assert project_tab.key_value_widgets["key-1"].keyLabel.text() == "key-1"
    assert (
        project_tab.key_value_widgets["key-1"].valueEditField.toPlainText() == "value")
    assert (project_tab.key_value_widgets["key-1"].valueTypeComboBox.currentText() ==
            "Text")
    assert project_tab.key_value_widgets["key-2"].keyLabel.text() == "key-2"
    assert project_tab.key_value_widgets["key-2"].valueEditField.toPlainText() == "4.2"
    assert (project_tab.key_value_widgets["key-2"].valueTypeComboBox.currentText() ==
            "Real")
    assert project_tab.key_value_widgets["key3"].keyLabel.text() == "key3"
    assert project_tab.key_value_widgets["key3"].valueEditField.toPlainText() == "1"
    assert (project_tab.key_value_widgets["key3"].valueTypeComboBox.currentText() ==
            "Integer")
    assert files_in_file_list == {"file.wav", "folder/file.wav"}


def test_project_update_on_change(qtbot, main_model):
    project_tab = ProjectTab(main_model)
    qtbot.addWidget(project_tab)

    main_model.project_model.emit_all_setting_signals()

    assert project_tab.projectNameEdit.text() == "project_name"
    assert project_tab.noteEdit.toPlainText() == "42"
    assert (
        project_tab.key_value_widgets["key-1"].valueEditField.toPlainText() == "value")
    assert (project_tab.key_value_widgets["key3"].valueTypeComboBox.currentText() ==
            "Integer")

    qtbot.keyClicks(project_tab.projectNameEdit, "u")
    qtbot.keyClicks(project_tab.noteEdit, "u")
    qtbot.keyClicks(project_tab.key_value_widgets["key-1"].valueEditField, "u")
    qtbot.keyClicks(project_tab.key_value_widgets["key3"].valueTypeComboBox, "Real")

    assert main_model.project_model.project_name == "project_nameu"
    assert project_tab.projectNameEdit.text() == "project_nameu"
    assert main_model.project_model.experiment_note == "u42"
    assert project_tab.noteEdit.toPlainText() == "u42"
    assert main_model.project_model.project_metadata["key-1"][0] == "uvalue"
    assert (
        project_tab.key_value_widgets["key-1"].valueEditField.toPlainText() == "uvalue")
    assert main_model.project_model.project_metadata["key3"][1] == "Real"
    assert (
        project_tab.key_value_widgets["key3"].valueTypeComboBox.currentText() == "Real")


def test_no_change_on_wrong_value_type(qtbot, main_model):
    project_tab = ProjectTab(main_model)
    qtbot.addWidget(project_tab)

    main_model.project_model.emit_all_setting_signals()

    assert project_tab.key_value_widgets["key3"].valueEditField.toPlainText() == "1"
    assert (project_tab.key_value_widgets["key3"].valueTypeComboBox.currentText() ==
            "Integer")

    qtbot.keyClicks(project_tab.key_value_widgets["key3"].valueEditField, "u")

    assert project_tab.key_value_widgets["key3"].valueEditField.toPlainText() == "1"


def test_no_change_on_wrong_type_selected(qtbot, main_model):
    project_tab = ProjectTab(main_model)
    qtbot.addWidget(project_tab)

    main_model.project_model.emit_all_setting_signals()

    assert (
        project_tab.key_value_widgets["key-1"].valueEditField.toPlainText() == "value")
    assert (project_tab.key_value_widgets["key-1"].valueTypeComboBox.currentText() ==
            "Text")

    qtbot.keyClicks(project_tab.key_value_widgets["key-1"].valueTypeComboBox, "Integer")

    assert (project_tab.key_value_widgets["key-1"].valueTypeComboBox.currentText() ==
            "Text")
