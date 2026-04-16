"""Tests for the settings controller."""

from __future__ import annotations

import json


def test_app_settings_controller_reload_exposes_saved_settings(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(
        AppSettings(
            package_repositories=["D:\\packages\\maya", "D:\\packages\\base"],
            contexts_location=str(tmp_path / "contexts"),
        )
    )

    app_error_hub.clear()
    controller = AppSettingsController()

    assert controller.packageRepositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert controller.contextsLocation == str(tmp_path / "contexts")
    assert app_error_hub.message == ""


def test_app_settings_controller_save_updates_settings_file(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import load_settings, save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))

    app_error_hub.clear()
    controller = AppSettingsController()

    assert controller.save(
        ["  D:\\packages\\maya  ", "", "D:\\packages\\base"],
        f"  {tmp_path / 'new-contexts'}  ",
    )

    settings = load_settings()
    assert settings.package_repositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert settings.contexts_location == str(tmp_path / "new-contexts")
    assert controller.packageRepositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert controller.contextsLocation == str(tmp_path / "new-contexts")
    assert app_error_hub.message == ""


def test_app_settings_controller_save_deduplicates_normalized_repositories(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import load_settings, save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))

    app_error_hub.clear()
    controller = AppSettingsController()

    assert controller.save(
        [
            "  D:\\packages\\maya\\  ",
            "d:/packages/maya",
            "D:\\packages\\base\\",
            "d:\\packages\\BASE",
        ],
        str(tmp_path / "normalized-contexts"),
    )

    settings = load_settings()
    assert settings.package_repositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert controller.packageRepositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert app_error_hub.message == ""


def test_app_settings_controller_import_from_file_updates_in_memory_state(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import load_settings, save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "saved-contexts")))

    import_path = tmp_path / "import-settings.json"
    import_path.write_text(
        json.dumps(
            {
                "package_repositories": [
                    " D:\\packages\\maya\\ ",
                    "d:/packages/maya",
                    "D:\\packages\\base",
                ],
                "contexts_location": str(tmp_path / "imported-contexts"),
            }
        ),
        encoding="utf-8",
    )

    app_error_hub.clear()
    controller = AppSettingsController()

    assert controller.importFromFile(str(import_path))
    assert controller.packageRepositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert controller.contextsLocation == str(tmp_path / "imported-contexts")
    persisted = load_settings()
    assert persisted.package_repositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert persisted.contexts_location == str(tmp_path / "imported-contexts")
    assert app_error_hub.message == ""


def test_app_settings_controller_export_to_file_writes_normalized_settings(tmp_path, monkeypatch):
    from rez_manager.persistence.settings_store import load_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))

    export_path = tmp_path / "exported-settings.json"

    app_error_hub.clear()
    controller = AppSettingsController()

    assert controller.exportToFile(
        [" D:\\packages\\maya\\ ", "d:/packages/maya", "D:\\packages\\base"],
        f"  {tmp_path / 'exported-contexts'}  ",
        str(export_path),
    )

    exported = json.loads(export_path.read_text(encoding="utf-8"))
    assert exported == {
        "package_repositories": ["D:\\packages\\maya", "D:\\packages\\base"],
        "contexts_location": str(tmp_path / "exported-contexts"),
    }
    persisted = load_settings()
    assert persisted.package_repositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert persisted.contexts_location == str(tmp_path / "exported-contexts")
    assert controller.packageRepositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert controller.contextsLocation == str(tmp_path / "exported-contexts")
    assert app_error_hub.message == ""


def test_app_settings_controller_open_path_in_file_manager(tmp_path, monkeypatch):
    import rez_manager.ui.settings_controller as settings_controller
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))

    opened_urls: list[str] = []

    def fake_open_url(url):
        opened_urls.append(url.toString())
        return True

    monkeypatch.setattr(settings_controller.QDesktopServices, "openUrl", fake_open_url)

    app_error_hub.clear()
    controller = AppSettingsController()
    repository_path = tmp_path / "packages" / "maya"
    repository_path.mkdir(parents=True)

    assert controller.revealInFileExplorer(str(repository_path))
    assert opened_urls == [f"file:///{repository_path.as_posix()}"]
    assert app_error_hub.message == ""


def test_app_settings_controller_save_rejects_blank_contexts_location(tmp_path, monkeypatch):
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))

    app_error_hub.clear()
    controller = AppSettingsController()

    assert not controller.save(["D:\\packages\\maya"], "   ")
    assert app_error_hub.message == "Contexts location is required."
