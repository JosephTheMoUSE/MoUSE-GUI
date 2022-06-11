#!/bin/bash

pip install PySide6==6.1.0

mkdir -p ./src/mouseapp/view/generated/init_project
mkdir -p ./src/mouseapp/view/generated/key_value_metadata
mkdir -p ./src/mouseapp/view/generated/settings

touch ./src/mouseapp/view/generated/__init__.py
touch ./src/mouseapp/view/generated/init_project/__init__.py
touch ./src/mouseapp/view/generated/key_value_metadata/__init__.py
touch ./src/mouseapp/view/generated/settings/__init__.py

pyside6-uic ./qt_designer/init_project/main_window.ui > ./src/mouseapp/view/generated/init_project/ui_main_window.py
pyside6-uic ./qt_designer/init_project/select_project.ui > ./src/mouseapp/view/generated/init_project/ui_select_project.py
pyside6-uic ./qt_designer/init_project/project_entry.ui > ./src/mouseapp/view/generated/init_project/ui_project_entry.py
pyside6-uic ./qt_designer/init_project/basic_metadata.ui > ./src/mouseapp/view/generated/init_project/ui_basic_metadata_widget.py
pyside6-uic ./qt_designer/init_project/load_audio.ui > ./src/mouseapp/view/generated/init_project/ui_load_audio_widget.py
pyside6-uic ./qt_designer/key_value_metadata/key_value_widget.ui > ./src/mouseapp/view/generated/key_value_metadata/ui_key_value_widget.py
pyside6-uic ./qt_designer/key_value_metadata/new_key_value_widget.ui > ./src/mouseapp/view/generated/key_value_metadata/ui_new_key_value_widget.py
pyside6-uic ./qt_designer/mouse_main_window.ui > ./src/mouseapp/view/generated/ui_mouse_main_window.py
pyside6-uic ./qt_designer/spectrogram_tab.ui > ./src/mouseapp/view/generated/ui_spectrogram_tab.py
pyside6-uic ./qt_designer/project_tab.ui > ./src/mouseapp/view/generated/ui_project_tab.py
pyside6-uic ./qt_designer/filename_widget.ui > ./src/mouseapp/view/generated/ui_filename_widget.py
pyside6-uic ./qt_designer/progress_bar.ui > ./src/mouseapp/view/generated/ui_progress_bar.py
pyside6-uic ./qt_designer/settings/settings.ui > ./src/mouseapp/view/generated/settings/ui_settings.py
pyside6-uic ./qt_designer/settings/detection_settings.ui > ./src/mouseapp/view/generated/settings/ui_detection_settings.py
pyside6-uic ./qt_designer/settings/denoising_settings.ui > ./src/mouseapp/view/generated/settings/ui_denoising_settings.py
pyside6-uic ./qt_designer/settings/preview_settings.ui > ./src/mouseapp/view/generated/settings/ui_preview_settings.py
pyside6-uic ./qt_designer/settings/classification_settings.ui > ./src/mouseapp/view/generated/settings/ui_classification_settings.py
pyside6-uic ./qt_designer/settings/filtering_settings.ui > ./src/mouseapp/view/generated/settings/ui_filtering_settings.py
