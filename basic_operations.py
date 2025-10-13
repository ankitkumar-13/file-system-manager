# Basic Operations for a file system

import re
import getpass
from object_and_file_manipulation import *
from custom_exceptions import *
from datetime import datetime

All_Perms = {
    'r': ('Read a File',100),
    'w': ('Write a File',110),
    'a': ('Modify a File',120),
    'd': ('Delete a File', 130)
}

class Permission:
    """
        :parameter abbrev: Notation of the permission.
    """
    def __init__(self, abbrev):
        if abbrev in list(All_Perms.keys()):
            self.name = All_Perms[abbrev][0]
            self.code = All_Perms[abbrev][1]
        else:
            raise InvalidPermissionNotationError(abbrev)
    def __eq__(self, other):
        return self.code == other.code
    def __str__(self):
        return self.name+"("+str(self.code)+")"
    def __repr__(self):
        return self.name+"("+str(self.code)+")"


class File:
    """
        Defines the files that can be saved or used in File System Manager
        :parameter name: Name of the disk
        :parameter size_in_bytes: Size of the disk in bytes
    """
    def __init__(self, name, size_in_bytes, permissions=None):
        if permissions is None:
            permissions = [Permission('r'), Permission('w'), Permission('a'), Permission('d')]
        self.name = name
        self.size_in_bytes = size_in_bytes
        self.owner = getpass.getuser()
        self.permissions = permissions
        self.last_modified = datetime.now()
    def __str__(self):
        return str(self.name)+"("+str(self.size_in_bytes)+")"
    def __repr__(self):
        return str(self.name)+"("+str(self.size_in_bytes)+")"


class Disk:
    """
    :parameter name: Name of the disk
    :parameter size_in_bytes: Size of the disk in bytes
    :parameter cluster_size: Optional, cluster size of the disk in bytes
    """
    def __init__(self, name, size_in_bytes, cluster_size = 4096):
        self.name = name
        self.size_in_bytes = size_in_bytes
        self.owner = getpass.getuser() #User that runs the script while creation
        self.cluster_size = cluster_size
        self.num_of_cluster = self.size_in_bytes // self.cluster_size
        self.FAT = [-1] * self.num_of_cluster
        self.num_of_empty_cluster = self.num_of_cluster
        self.num_of_filled_cluster = 0
        self.files = dict()
    def add_file(self, file_name, file_size_in_bytes):
        self.files[file_name] = File(file_name, file_size_in_bytes)
    def format(self):
        for i in range(self.num_of_cluster):
            self.FAT[i] = -1
    def disk_stat(self):
        print("Disk Name :",self.name)
        print("Disk Size :", self.size_in_bytes, "Bytes")
        print("Cluster Size :", self.cluster_size, "Bytes")
        print("No. of Cluster :", self.num_of_cluster)
        print("No. of Empty Cluster :", self.num_of_empty_cluster)
        print("No. of Filled Cluster :", self.num_of_filled_cluster)
    def __str__(self):
        return self.name
    def __repr__(self):
        return f"Disk({self.name}, {self.size_in_bytes} bytes)"



# Create a file :-
def create_disk():
    """
    Creates disk and register it. Also asks for input like disk name and disk size.
    :return: None
    """
    disk_name = input("Enter the name of the disk you want to create : ")
    disk_size = input("\nFor KiloBytes write MB suffix, Example : 250 kb or 250 KB"
                      "\nFor MegaBytes write MB suffix, Example : 250 mb or 250 MB"
                      "\nFor GigaBytes write GB suffix, Example : 250 gb or 250 GB"
                      "\nEnter the size of the disk you want to use : ")
    disk_size = disk_size.upper()
    pattern = re.compile(r' ([0-9]+)  \s*  ([a-zA-Z]{2,}) ', re.VERBOSE)
    match = pattern.search(disk_size)
    if match:
        disk_size = int(match.group(1))
        disk_size_unit = match.group(2)
    else:
        raise InvalidDiskSizeError(disk_size)

    disk_bytes = 0

    if disk_size_unit == "KB":
        disk_bytes = disk_size * 1024
    elif disk_size_unit == "MB":
        disk_bytes = disk_size * 1024 * 1024
    elif disk_size_unit == "GB":
        disk_bytes = disk_size * 1024 * 1024 * 1024
    else:
        raise Exception("Invalid disk size unit. Recheck your input : ")

    if file_exists(disk_name + '.bin'):
        raise DuplicateDiskNameError(disk_name)

    # Disk Creation and Update the manager :-
    with open(disk_name + '.bin', 'wb') as f:
        disk_obj = Disk(disk_name, disk_bytes)
        f.seek(disk_obj.size_in_bytes - 1)
        f.write(b"\0")      # Creation of file with desired size.
        register_disk(disk_obj)     # Register the disk.
        print("\nThe disk has been created successfully")


def check_disk_stat(disk_name):
    """
    :param disk_name: Name of the disk
    :return: None
    """
    all_disks = load_object(".fsmdata")
    if disk_name in all_disks:
        all_disks[disk_name].disk_stat()
    else:
        print("Disk Not Found!")
    print()


def refresh_disks():
    """
    Refreshes the list of available disks.
    Checks whether the disks shown in .fsmdata are in the same folder or not.
    :return: True if changes made, else False.
    """
    disks = load_object(".fsmdata")
    updated_list = disks.copy()
    for disk_name in disks:
        if not file_exists(disk_name + '.bin'):
            updated_list.pop(disk_name, None)
            print(f"Removed {disk_name}.bin from the .fsmdata")
    if disks != updated_list:
        update_disk(updated_list)
        return True
    else:
        return False

def display_all_disks():
    """
    Displays all available disks. in the dictionary format.
    :return: None
    """
    print("Available Disks: ")
    if file_exists(".fsmdata"):
        all_disks = load_object(".fsmdata")
        print(all_disks, '->',len(all_disks))
    else:
        print("No Disk Data Available")


# Start Main Control :-
while True:
    choice = input("\nPress 1 to create a new disk."
          "\nPress 2 to check disk stats."
          "\nPress 3 to refresh the disks."
          "\nPress 4 to display all available disks."
          "\nPress 5 to exit"
          "\nEnter your choice : ").strip()
    print("\n")
    if choice == "1":
        try:
            create_disk()
        except DuplicateDiskNameError as e:
            print(e)
        except InvalidDiskSizeError as e:
            print(e)
        except Exception as e:
            print("Unknown Error :", e)
    elif choice == "2":
        disk_chk = input("Enter the name of the disk you want to create : ")
        check_disk_stat(disk_chk)
    elif choice == "3":
        if refresh_disks():
            print("Updated the list of available disks")
        else:
            print("No changes made")
    elif choice == "4":
        display_all_disks()
    elif choice == "5":
        exit(0)
    else:
        print("Invalid choice. Recheck your input : ")
