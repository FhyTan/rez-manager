"""Tests for the QML-facing launch target model."""

from __future__ import annotations


def test_launch_target_list_model_exposes_expected_roles():
    from rez_manager.ui.launch_target_model import LaunchTargetListModel

    model = LaunchTargetListModel()

    assert model.rowCount() == 7
    assert model.defaultValue == "Shell"
    assert model.customValue == "Custom"
    assert model.option("Maya") == {
        "value": "Maya",
        "label": "Maya",
        "accentColor": "#4DB880",
        "iconName": "Maya",
        "iconSource": "qrc:/icons/dcc/Maya",
    }


def test_launch_target_list_model_returns_empty_map_for_invalid_value():
    from rez_manager.ui.launch_target_model import LaunchTargetListModel

    model = LaunchTargetListModel()

    assert model.option("maya") == {}
