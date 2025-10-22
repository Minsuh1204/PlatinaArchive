from cx_Freeze import setup, Executable

from client import VERSION, version_to_string

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
        "scipy",
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
    "summary_data": {
        "author": "Endeavy",
        "comments": "Desktop app to keep track of PLATiNA::LAB results",
    },
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
    version=version_to_string(VERSION)[1:],
    description="Desktop app to capture PLATiNA::LAB results",
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=executables,
)
