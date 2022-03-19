from pathlib import Path

from mouseapp.controller.main_controller import load_audio_files
from mouseapp.view.project_init_view import LoadAudio
from mouseapp.view.main_view import ProjectTab
from tests.model_fixtures import *  # noqa F401 F403


def test_load_audio_files(clean_main_model):
    """Tests whether files are loaded to the model.

    Files should be stored in an alphabetical order.
    """
    load_audio_files(clean_main_model, ["file_a.wav", "file_c.wav", "file_b.wav"])

    assert clean_main_model.project_model.audio_files == [
        Path("file_a.wav"),
        Path("file_b.wav"),
        Path("file_c.wav"),
    ]


def test_load_audio_files_from_folder(clean_main_model, tmpdir):
    """Tests whether files are loaded from the folder to the model.

    Files should be stored in an alphabetical order.
    """
    tmpdir.join("file_a.wav").ensure()
    tmpdir.join("file_c.wav").ensure()
    tmpdir.join("file_b.wav").ensure()
    tmpdir.join("file_a.mp3").ensure()

    load_audio_files(clean_main_model, str(tmpdir), folder=True)

    assert clean_main_model.project_model.audio_files == [
        Path(str(tmpdir), "file_a.mp3"),
        Path(str(tmpdir), "file_a.wav"),
        Path(str(tmpdir), "file_b.wav"),
        Path(str(tmpdir), "file_c.wav"),
    ]


def test_load_only_audio_files_from_folder(clean_main_model, tmpdir):
    """Tests whether non-audio files are ignored while reading a folder."""
    tmpdir.join("file.wav").ensure()
    tmpdir.join("file.mp3").ensure()
    tmpdir.join("file.txt").ensure()

    load_audio_files(clean_main_model, str(tmpdir), folder=True)

    assert clean_main_model.project_model.audio_files == [
        Path(str(tmpdir), "file.mp3"),
        Path(str(tmpdir), "file.wav"),
    ]


def test_loading_audio_files_from_nested_folders(clean_main_model, tmpdir):
    """Tests whether files from nested folders are loaded."""
    tmpdir.join("file.wav").ensure()
    tmpdir.join("a/file.wav").ensure()
    tmpdir.join("a/b/file.wav").ensure()

    load_audio_files(clean_main_model, str(tmpdir), folder=True)

    assert clean_main_model.project_model.audio_files == [
        Path(str(tmpdir), "a/b/file.wav"),
        Path(str(tmpdir), "a/file.wav"),
        Path(str(tmpdir), "file.wav"),
    ]


def test_audio_files_changed_signal(qtbot, clean_main_model):
    """Tests whether audio_files_changed signal is emitted.

    Information about loaded files should be shown to the user.
    """
    widget = LoadAudio(clean_main_model)
    qtbot.addWidget(widget)

    clean_main_model.project_model.audio_files = [
        "file_a.wav",
        "file_b.wav",
        "file_c.wav",
    ]

    assert widget.fileLoadingStatusInfo.text() == "Loaded 3 audio files."


# TODO(#72): fix tests
def test_first_not_common_character_on_root(qtbot, clean_main_model):
    """Tests if algorithm works for paths differing at root."""  # noqa
    project_tab = ProjectTab(clean_main_model)
    qtbot.addWidget(project_tab)
    load_audio_files(clean_main_model,
                     ["/a/file_a.wav", "/c/file_c.wav", "/b/file_b.wav"])
    clean_main_model.project_model.emit_all_setting_signals()
    short_file_names = sorted(list(project_tab.audio_file_widgets.keys()))
    assert short_file_names == ["a/file_a.wav", "b/file_b.wav", "c/file_c.wav"]


def test_first_not_common_character_same_folder_beginnings(qtbot, clean_main_model):
    """Tests if algorithm works for different folders.

    Tests if first not common character is the first character of a differing
    folder not first not common character overall.
    """
    project_tab = ProjectTab(clean_main_model)
    qtbot.addWidget(project_tab)
    load_audio_files(clean_main_model, ["/a/ab/file_a.wav", "/a/a/file_c.wav"])  # noqa
    clean_main_model.project_model.emit_all_setting_signals()
    short_file_names = sorted(list(project_tab.audio_file_widgets.keys()))
    assert short_file_names == ["a/file_c.wav", "ab/file_a.wav"]


def test_first_not_common_character_various_depths(qtbot, clean_main_model):
    """Tests if algorithm works for different path depths."""
    project_tab = ProjectTab(clean_main_model)
    qtbot.addWidget(project_tab)
    load_audio_files(
        clean_main_model,
        ["/a/b/f/file_a.wav", "/a/b/file_c.wav", "/a/b/fi/f/file_c.wav"],
    )
    clean_main_model.project_model.emit_all_setting_signals()
    short_file_names = sorted(list(project_tab.audio_file_widgets.keys()))
    assert short_file_names == ["f/file_a.wav", "fi/f/file_c.wav", "file_c.wav"]
