
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
