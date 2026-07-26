import os
from tempfile import gettempdir

# folder definitions
marble_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
temp_folder = os.path.join(gettempdir(), 'marble')
temp_tests_folder = os.path.join(temp_folder, 'tests')
gdm_folder = "gdm"
tweaks_folder = "tweaks"
themes_folder = os.path.expanduser("~/.themes")
raw_theme_folder = "theme"

# Runtime override for the detected GNOME Shell version. Set from the
# ``--gnome-version`` CLI flag so version-specific style overlays can be
# selected without a running gnome-shell (sandboxed Nix builds, CI). ``None``
# means fall back to auto-detection via ``gnome-shell --version``.
gnome_version_override = None

# GDM definitions
global_gnome_shell_theme = "/usr/share/gnome-shell"
gnome_shell_gresource = "gnome-shell-theme.gresource"
ubuntu_gresource_link = "gtk-theme.gresource"
extracted_gdm_folder = "theme"

# files definitions
tweak_file = f"./{tweaks_folder}/*/tweak.py"
colors_json = os.path.join(marble_folder, "colors.json")

user_themes_extension = "/org/gnome/shell/extensions/user-theme/name"
