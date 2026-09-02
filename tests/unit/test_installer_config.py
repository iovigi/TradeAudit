"""
Tests for TradeAudit Windows Installer and Packaging configuration.
"""

from pathlib import Path
import re
import tradeaudit


def test_inno_setup_script_structure():
    root = Path(__file__).parent.parent.parent
    iss_file = root / "installer" / "TradeAudit.iss"
    
    assert iss_file.exists(), "TradeAudit.iss should exist in installer/ directory"
    
    content = iss_file.read_text(encoding="utf-8")
    
    # Check definitions
    assert '#define MyAppName "TradeAudit"' in content
    assert f'#define MyAppVersion "{tradeaudit.__version__}"' in content
    assert '#define MyAppExeName "TradeAudit.exe"' in content
    
    # Check essential Inno Setup sections
    sections = ["[Setup]", "[Languages]", "[Tasks]", "[Files]", "[Icons]", "[Run]"]
    for section in sections:
        assert section in content, f"Section {section} must be present in TradeAudit.iss"
        
    # Check setup parameters
    assert "ArchitecturesInstallIn64BitMode=x64compatible" in content
    assert "TradeAudit-Setup-v" in content
    assert "tradeaudit.ico" in content


def test_installer_build_scripts_exist():
    root = Path(__file__).parent.parent.parent
    ps1_script = root / "scripts" / "build_installer.ps1"
    bat_script = root / "scripts" / "build_installer.bat"
    
    assert ps1_script.exists(), "build_installer.ps1 should exist in scripts/"
    assert bat_script.exists(), "build_installer.bat should exist in scripts/"
    
    ps1_content = ps1_script.read_text(encoding="utf-8")
    assert "TradeAudit.iss" in ps1_content
    assert "Compress-Archive" in ps1_content
    assert "ISCC" in ps1_content
