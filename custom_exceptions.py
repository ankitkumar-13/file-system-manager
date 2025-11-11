
class InvalidPermissionNotationError(Exception):
    """
    Exception raised when a permission abbreviation that is not in the allowed list is asked for.
    """
    def __init__(self, notation):
        self.notation = notation
    def __str__(self):
        return (f"\nPermission Notation {self.notation} doesn't exists."
                f"\nCheck the notation again for the required permission.\n")
    def __repr__(self):
        return f"\nInvalidPermissionNotationError({self.notation})\n"

class DuplicateDiskNameError(Exception):
    """
    Exception raised when a disk name already exists.
    """
    def __init__(self, disk_name):
        self.disk_name = disk_name
    def __str__(self):
        return (f"\nDisk name {self.disk_name} already exists."
                f"\nChoose another name for your disk.\n")
    def __repr__(self):
        return f"\nDuplicateDiskNameError({self.disk_name})\n"

class InvalidDiskSizeError(Exception):
    """
    Exception raised when a disk size is in invalid format.
    """
    def __init__(self, disk_size):
        self.disk_size = disk_size
    def __str__(self):
        return f"\nDisk size {self.disk_size} is in invalid format.\n"
    def __repr__(self):
        return f"\nInvalidDiskSizeError({self.disk_size})\n"

class InsufficientMemoryError(Exception):
    """
    Exception raised when there is not enough memory to allocate.
    """
    def __init__(self, required_clusters, available_clusters):
        self.required_clusters = required_clusters
        self.available_clusters = available_clusters
    def __str__(self):
        return (f"\nInsufficient memory: Required {self.required_clusters} clusters, "
                f"but only {self.available_clusters} clusters available.\n")
    def __repr__(self):
        return f"\nInsufficientMemoryError({self.required_clusters}, {self.available_clusters})\n"

class FileNotFoundError(Exception):
    """
    Exception raised when a file is not found in the disk.
    """
    def __init__(self, file_name):
        self.file_name = file_name
    def __str__(self):
        return f"\nFile '{self.file_name}' not found in the disk.\n"
    def __repr__(self):
        return f"\nFileNotFoundError({self.file_name})\n"