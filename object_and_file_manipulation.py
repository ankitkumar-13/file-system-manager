import pickle
from pathlib import Path

from custom_exceptions import DuplicateDiskNameError


# Object Related Operations :-
def save_object(obj, filename: str):
    """
    Save an object as binary file using pickle module.
    :parameter obj: object to save
    :parameter filename: string with extension. Basically the file name (with or without path)
    """
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)     # type:ignore   ~Linting Removal

def load_object(filename):
    """
    Load an object from a binary file using pickle module.
    :parameter filename: string with extension. Basically the file name (with or without path)
    :return: object loaded from file
    """
    with open(filename, 'rb') as f:
        return pickle.load(f)


# Path Related Operations
def file_exists(filename):
    """
    Determine if a file exists or not.
    :param filename: file name with extension.
    :return: True or False
    """
    return Path(filename).exists()


# Disk Related Operations :-
def register_disk(disk):
    """
    Register the disk to .fsmdata.
    :param disk: disk type object that needs to be registered.
    :return: None
    """
    if file_exists(".fsmdata"):
        all_disks = load_object(".fsmdata")
        if disk.name in all_disks:
            raise DuplicateDiskNameError(disk.name)
        all_disks[disk.name] = disk
    else:
        all_disks = {disk.name : disk}
    save_object(all_disks, ".fsmdata")

def update_disk(all_disks):
    """
    Update the .fsmdata file.
    :param all_disks: dictionary of all disks.
    :return: None
    """
    save_object(all_disks, ".fsmdata")
