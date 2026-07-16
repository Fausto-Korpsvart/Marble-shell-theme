import os


def _folder_bounds(folder):
    """
    Parse a version-folder name into an inclusive ``(low, high)`` bound, or
    ``None`` if the folder isn't a version range.

    Naming: ``..N`` = up to N, ``N..`` = N and up, ``M..N`` = M through N,
    ``N`` = exactly N.
    """
    if '..' in folder:
        from_version, to_version = folder.split('..')
        try:
            low = int(from_version) if from_version else float('-inf')
            high = int(to_version) if to_version else float('inf')
        except ValueError:
            return None
        return low, high

    if folder.isdigit():
        exact = int(folder)
        return exact, exact

    return None


def get_version_folders(version, base_path):
    """
    Get version folders matching the given gnome-shell version, ordered so that
    higher-version (more specific) folders come last — i.e. their styles
    override lower ones when the combined stylesheet is built.

    :param version: gnome-shell version
    :param base_path: base path to version folders
    :return: list of matching version folder names, ascending by lower bound
    """
    if not os.path.exists(base_path):
        return []

    version = int(version.split('.')[0])  # compare on the major version only
    matching = []

    for folder in os.listdir(base_path):
        bounds = _folder_bounds(folder)
        if bounds is None:
            continue

        low, high = bounds
        if low <= version <= high:
            matching.append((low, high, folder))

    matching.sort()  # by lower bound, then upper bound, then name — deterministic
    return [folder for _, _, folder in matching]
