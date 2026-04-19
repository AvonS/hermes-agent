"""Tests for fork version banner functionality.

These tests verify the fork version display logic, including:
- .fork-version file persistence (survives upstream sync)
- Priority order: .fork-version > .update_check > git describe
- Correct version format parsing

Fork-managed file - survives upstream merge.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGetInstalledVersion:
    """Test get_installed_version() priority and edge cases."""
    
    def test_reads_from_fork_version_first(self, tmp_path, monkeypatch):
        """Priority 1: .fork-version file is checked first."""
        from hermes_cli.banner import get_installed_version
        
        # Create isolated HERMES_HOME
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        
        # Create .fork-version
        fork_file = tmp_path / ".fork-version"
        fork_file.write_text(json.dumps({
            "installed_version": "0.10.0-avons.1.5",
            "installed_at": "2026-04-19T10:00:00Z"
        }))
        
        # Create .update_check with different version
        update_file = tmp_path / ".update_check"
        update_file.write_text(json.dumps({
            "installed_version": "0.10.0-avons.1.0",  # Should be ignored
            "ts": 1234567890
        }))
        
        result = get_installed_version()
        assert result == "0.10.0-avons.1.5"
    
    def test_falls_back_to_update_check(self, tmp_path, monkeypatch):
        """Priority 2: Falls back to .update_check if .fork-version missing."""
        from hermes_cli.banner import get_installed_version
        
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        
        # Only create .update_check
        update_file = tmp_path / ".update_check"
        update_file.write_text(json.dumps({
            "installed_version": "0.10.0-avons.1.0"
        }))
        
        result = get_installed_version()
        assert result == "0.10.0-avons.1.0"
    
    def test_returns_none_if_no_files(self, tmp_path, monkeypatch):
        """Returns None when neither file exists."""
        from hermes_cli.banner import get_installed_version
        
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        
        result = get_installed_version()
        assert result is None
    
    def test_survives_corrupt_fork_version(self, tmp_path, monkeypatch):
        """Falls back to .update_check if .fork-version is corrupt."""
        from hermes_cli.banner import get_installed_version
        
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        
        # Create corrupt .fork-version
        fork_file = tmp_path / ".fork-version"
        fork_file.write_text("not valid json")
        
        # Create valid .update_check
        update_file = tmp_path / ".update_check"
        update_file.write_text(json.dumps({
            "installed_version": "0.10.0-avons.1.0"
        }))
        
        result = get_installed_version()
        assert result == "0.10.0-avons.1.0"
    
    def test_empty_installed_version_in_fork_version(self, tmp_path, monkeypatch):
        """Falls back if installed_version is missing in .fork-version."""
        from hermes_cli.banner import get_installed_version
        
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        
        # Create .fork-version without installed_version
        fork_file = tmp_path / ".fork-version"
        fork_file.write_text(json.dumps({"other": "data"}))
        
        # Create valid .update_check
        update_file = tmp_path / ".update_check"
        update_file.write_text(json.dumps({
            "installed_version": "0.10.0-avons.1.0"
        }))
        
        result = get_installed_version()
        assert result == "0.10.0-avons.1.0"


class TestFormatBannerVersionLabel:
    """Test version label formatting with fork versions."""
    
    def test_shows_fork_version_when_available(self, tmp_path, monkeypatch):
        """Banner shows fork version when installed_version is present."""
        from hermes_cli.banner import format_banner_version_label
        
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        
        # Mock FORK_VERSION_ENABLED
        import hermes_cli.banner as banner
        old_flag = banner.FORK_VERSION_ENABLED
        try:
            banner.FORK_VERSION_ENABLED = True
            
            # Create .fork-version
            fork_file = tmp_path / ".fork-version"
            fork_file.write_text(json.dumps({
                "installed_version": "0.10.0-avons.1.5"
            }))
            
            label = format_banner_version_label()
            assert "0.10.0-avons.1.5" in label
        finally:
            banner.FORK_VERSION_ENABLED = old_flag
    
    def test_shows_upstream_version_when_fork_disabled(self, tmp_path, monkeypatch):
        """Banner shows upstream version when FORK_VERSION_ENABLED=False."""
        from hermes_cli.banner import format_banner_version_label, VERSION
        import hermes_cli.banner as banner
        
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        
        old_flag = banner.FORK_VERSION_ENABLED
        try:
            banner.FORK_VERSION_ENABLED = False
            
            label = format_banner_version_label()
            # Should show upstream version
            assert VERSION in label
            assert "-avons." not in label or VERSION in label
        finally:
            banner.FORK_VERSION_ENABLED = old_flag
