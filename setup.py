import sys
from cx_Freeze import setup, Executable

# NEVER CHANGE IT!!!
UPGRADE_CODE = "{b4c02c5f-5b55-4eeb-a4b6-624b3aa03dbf}"

build_exe_options = {
    "packages": [
        "tkinter",
        "PIL",
        "imagehash",
        "pytesseract",
        "requests",
        "keyring",
        "keyring.backends.Windows",
        "pynput",
        "win32ctypes",
        "win32ctypes.pywin32",
    ],
    "includes": [
        "analyzer",
        "login",
        "models",
    ],
    "include_files": [
        ("tesseract/", "tesseract/"),  # Include entire tesseract directory
        ("icon.ico", "icon.ico"),
    ],
    "excludes": [
        "matplotlib",
        "mypy",
        "sqlalchemy",
        "scipy",
        "pandas",
        "pytz",
        "test",
        "unittest",
    ],
    "optimize": 2,  # Optimize Python bytecode
}

bdist_msi_options = {
    "initial_target_dir": "[AppDataFolder]\\PLATiNA-ARCHiVE",
    "add_to_path": False,
    "install_icon": "icon.ico",
    "upgrade_code": UPGRADE_CODE,
    "launch_on_finish": True,
}

# Executable configuration
executables = [
    Executable(
        script="client.py",
        base="gui",
        target_name="PLATiNA-ARCHiVE.exe",
        icon="icon.ico",
        shortcut_name="PLATiNA-ARCHiVE",
        shortcut_dir="DesktopFolder",
    )
]

setup(
    name="PLATiNA-ARCHiVE",
    version="0.2.4",
    description="Desktop app to capture PLATiNA::LAB results",
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=executables,
)
