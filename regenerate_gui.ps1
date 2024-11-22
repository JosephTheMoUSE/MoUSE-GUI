# PowerShell script for Windows to replace Bash script

# Create directories if they do not exist
New-Item -ItemType Directory -Force -Path ./src/mouseapp/view/generated/init_project
New-Item -ItemType Directory -Force -Path ./src/mouseapp/view/generated/key_value_metadata
New-Item -ItemType Directory -Force -Path ./src/mouseapp/view/generated/settings

# Create __init__.py files in the directories
New-Item -ItemType File -Force -Path ./src/mouseapp/view/generated/__init__.py
New-Item -ItemType File -Force -Path ./src/mouseapp/view/generated/init_project/__init__.py
New-Item -ItemType File -Force -Path ./src/mouseapp/view/generated/key_value_metadata/__init__.py
New-Item -ItemType File -Force -Path ./src/mouseapp/view/generated/settings/__init__.py

# Generate Python files from .ui files using pyside6-uic
pyside6-uic ./qt_designer/init_project/main_window.ui -o ./src/mouseapp/view/generated/init_project/ui_main_window.py
pyside6-uic ./qt_designer/init_project/select_project.ui -o ./src/mouseapp/view/generated/init_project/ui_select_project.py
pyside6-uic ./qt_designer/init_project/project_entry.ui -o ./src/mouseapp/view/generated/init_project/ui_project_entry.py
pyside6-uic ./qt_designer/init_project/basic_metadata.ui -o ./src/mouseapp/view/generated/init_project/ui_basic_metadata_widget.py
pyside6-uic ./qt_designer/init_project/load_audio.ui -o ./src/mouseapp/view/generated/init_project/ui_load_audio_widget.py
pyside6-uic ./qt_designer/key_value_metadata/key_value_widget.ui -o ./src/mouseapp/view/generated/key_value_metadata/ui_key_value_widget.py
pyside6-uic ./qt_designer/key_value_metadata/new_key_value_widget.ui -o ./src/mouseapp/view/generated/key_value_metadata/ui_new_key_value_widget.py
pyside6-uic ./qt_designer/mouse_main_window.ui -o ./src/mouseapp/view/generated/ui_mouse_main_window.py
pyside6-uic ./qt_designer/spectrogram_tab.ui -o ./src/mouseapp/view/generated/ui_spectrogram_tab.py
pyside6-uic ./qt_designer/project_tab.ui -o ./src/mouseapp/view/generated/ui_project_tab.py
pyside6-uic ./qt_designer/filename_widget.ui -o ./src/mouseapp/view/generated/ui_filename_widget.py
pyside6-uic ./qt_designer/progress_bar.ui -o ./src/mouseapp/view/generated/ui_progress_bar.py
pyside6-uic ./qt_designer/settings/settings.ui -o ./src/mouseapp/view/generated/settings/ui_settings.py
pyside6-uic ./qt_designer/settings/detection_settings.ui -o ./src/mouseapp/view/generated/settings/ui_detection_settings.py
pyside6-uic ./qt_designer/settings/denoising_settings.ui -o ./src/mouseapp/view/generated/settings/ui_denoising_settings.py
pyside6-uic ./qt_designer/settings/preview_settings.ui -o ./src/mouseapp/view/generated/settings/ui_preview_settings.py
pyside6-uic ./qt_designer/settings/classification_settings.ui -o ./src/mouseapp/view/generated/settings/ui_classification_settings.py
pyside6-uic ./qt_designer/settings/filtering_settings.ui -o ./src/mouseapp/view/generated/settings/ui_filtering_settings.py
