import os
import subprocess

from .theme import Theme
from .utils import remove_properties, remove_keywords, gnome
from . import config
from .utils.console import Console, Color, Format
from .utils.files_labeler import FilesLabeler


class ThemePrepare:
    """
    Theme object prepared for installation
    """

    def __init__(self, theme: Theme, theme_file, should_label=False):
        self.theme = theme
        self.theme_file = theme_file
        self.should_label = should_label


class GlobalTheme:
    def __init__(self, colors_json, theme_folder, destination_folder, destination_file, temp_folder,
                 mode=None, is_filled=False):
        """
        Initialize GlobalTheme class
        :param colors_json: location of a json file with colors
        :param theme_folder: raw theme location
        :param destination_folder: folder where themes will be installed
        :param temp_folder: folder where files will be collected
        :param mode: theme mode (light or dark). applied only for gnome-shell < 44
        :param is_filled: if True, theme will be filled
        """

        self.colors_json = colors_json
        self.theme_folder = theme_folder
        self.destination_folder = destination_folder
        self.destination_file = destination_file
        self.temp_folder = temp_folder

        self.backup_file = f"{self.destination_file}.backup"
        self.backup_trigger = "\n/* Marble theme */\n"  # trigger to check if theme is installed
        self.extracted_theme: str = os.path.join(self.temp_folder, config.extracted_gdm_folder)
        self.gst = os.path.join(self.destination_folder, self.destination_file)  # use backup file if theme is installed

        self.themes: list[ThemePrepare] = []
        self.is_filled = is_filled
        self.mode = mode


    def __create_theme(self, theme_type: str, mode=None, should_label=False, is_filled=False):
        """Helper to create theme objects"""
        theme = Theme(theme_type, self.colors_json, self.theme_folder,
                      self.extracted_theme, self.temp_folder,
                      mode=mode, is_filled=is_filled)
        theme.prepare()
        theme_file = os.path.join(self.extracted_theme, f"{theme_type}.css")
        return ThemePrepare(theme=theme, theme_file=theme_file, should_label=should_label)

    def __is_installed(self):
        """
        Check if theme is installed
        :return: True if theme is installed, False otherwise
        """

        with open(self.gst, "rb") as f:
            return self.backup_trigger.encode() in f.read()

    def __extract(self):
        """
        Extract gresource files to temp folder
        """
        extract_line = Console.Line()
        extract_line.update("Extracting gresource files...")

        resources = subprocess.getoutput(f"gresource list {self.gst}").split("\n")
        prefix = "/org/gnome/shell/"

        try:
            for resource in resources:
                resource_path = resource.replace(prefix, "")
                dir_path = os.path.join(self.temp_folder, os.path.dirname(resource_path))
                output_path = os.path.join(self.temp_folder, resource_path)

                os.makedirs(dir_path, exist_ok=True)
                with open(output_path, 'wb') as f:
                    subprocess.run(["gresource", "extract", self.gst, resource], stdout=f, check=True)

            extract_line.success("Extracted gresource files.")

        except FileNotFoundError as e:
            if "gresource" in str(e):
                print("Error: 'gresource' command not found.")
                print("Please install the glib2-devel package:")
                print(" - For Fedora/RHEL: sudo dnf install glib2-devel")
                print(" - For Ubuntu/Debian: sudo apt install libglib2.0-dev")
                print(" - For Arch: sudo pacman -S glib2-devel")
                raise Exception("Missing required dependency: glib2-devel") from e
            raise

    def __add_gnome_styles(self, theme):
        """
        Add gnome styles to the start of the file
        :param theme: Theme object
        """

        with open(f"{self.extracted_theme}/{theme.theme_type}.css", 'r') as gnome_theme:
            gnome_styles = gnome_theme.read() + self.backup_trigger
            theme.add_to_start(gnome_styles)

    def __generate_themes(self, hue, color, sat=None):
        """
        Generate theme files for gnome-shell-theme.gresource.xml
        :param hue: color hue
        :param color: color name
        :param sat: color saturation
        """

        for theme_prepare in self.themes:
            if theme_prepare.should_label:
                temp_folder = theme_prepare.theme.temp_folder
                main_styles = theme_prepare.theme.main_styles
                FilesLabeler(temp_folder, main_styles).append_label("light")

            remove_keywords(theme_prepare.theme_file, "!important")
            remove_properties(theme_prepare.theme_file, "background-color", "color", "box-shadow", "border-radius")

            self.__add_gnome_styles(theme_prepare.theme)

            theme_prepare.theme.install(hue, color, sat, destination=self.extracted_theme)


    def __backup(self):
        if self.__is_installed():
            return

        backup_line = Console.Line()

        backup_line.update("Backing up default theme...")
        subprocess.run(["cp", "-aT", self.gst, f"{self.gst}.backup"], cwd=self.destination_folder, check=True)
        backup_line.success("Backed up default theme.")

    def __generate_gresource_xml(self):
        # list of files to add to gnome-shell-theme.gresource.xml
        files = [f"<file>{file}</file>" for file in os.listdir(self.extracted_theme)]
        nl = "\n"  # fstring doesn't support newline character

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<gresources>
    <gresource prefix="/org/gnome/shell/theme">
        {nl.join(files)}
    </gresource>
</gresources>"""

    def prepare(self):
        try:
            gnome_version = gnome.gnome_version()
            gnome_major = gnome_version.split(".")[0]
            if int(gnome_major) >= 44:
                self.themes += [
                    self.__create_theme("gnome-shell-light", mode='light', should_label=True, is_filled=self.is_filled),
                    self.__create_theme("gnome-shell-dark", mode='dark', is_filled=self.is_filled)
                ]
        except Exception as e:
            print(f"Error: {e}")
            print("Using single theme.")

        if not self.themes:
            self.themes.append(
                self.__create_theme(
                    "gnome-shell", mode=self.mode if self.mode else 'dark', is_filled=self.is_filled))

    def install(self, hue, sat=None):
        """
        Install theme globally
        :param hue: color hue
        :param sat: color saturation
        """

        if os.geteuid() != 0:
            raise Exception("Root privileges required to install GDM theme")

        if self.__is_installed():
            print("Theme is installed. Reinstalling...")
            self.gst += ".backup"

        self.__extract()

        # generate theme files for global theme
        self.__generate_themes(hue, 'Marble', sat)

        # generate gnome-shell-theme.gresource.xml
        with open(f"{self.extracted_theme}/{self.destination_file}.xml", 'w') as gresource_xml:
            generated_xml = self.__generate_gresource_xml()
            gresource_xml.write(generated_xml)

        # compile gnome-shell-theme.gresource.xml
        compile_line = Console.Line()
        compile_line.update("Compiling gnome-shell theme...")
        subprocess.run(["glib-compile-resources" , f"{self.destination_file}.xml"],
                       cwd=self.extracted_theme, check=True)
        compile_line.success("Theme compiled.")

        # backup installed theme
        self.__backup()

        # install theme
        install_line = Console.Line()
        install_line.update("Moving compiled theme to system folder...")
        subprocess.run(["sudo", "cp", "-f", 
                        f"{self.extracted_theme}/{self.destination_file}", 
                        f"{self.destination_folder}/{self.destination_file}"], 
                       check=True)
        install_line.success("Theme moved to system folder.")


    def remove(self):
        """
        Remove installed theme
        """

        # use backup file if theme is installed
        if self.__is_installed():
            removing_line = Console.Line()
            removing_line.update("Theme is installed. Removing...")
            backup_path = os.path.join(self.destination_folder, self.backup_file)
            dest_path = os.path.join(self.destination_folder, self.destination_file)

            if os.path.isfile(backup_path):
                subprocess.run(["sudo", "mv", backup_path,  dest_path], check=True)
                removing_line.success("Global theme removed successfully. Restart GDM to apply changes.")

            else:
                formatted_shell = Console.format("gnome-shell", color=Color.BLUE, format_type=Format.BOLD)
                removing_line.error(f"Backup file not found. Try reinstalling {formatted_shell} package.")

        else:
            Console.Line().error("Theme is not installed. Nothing to remove.")
            Console.Line().update("If theme is still installed globally, try reinstalling gnome-shell package.", icon="⚠️")
