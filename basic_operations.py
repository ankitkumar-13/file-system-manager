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
        # Memory allocation tracking
        self.allocation_type = None  # 'contiguous' or 'non-contiguous'
        self.allocated_clusters = []  # List of cluster indices allocated to this file
        self.start_cluster = -1  # Starting cluster for contiguous allocation
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
        self.FAT = [-1] * self.num_of_cluster  # -1 means free, -2 means end of file, >=0 means next cluster
        self.num_of_empty_cluster = self.num_of_cluster
        self.num_of_filled_cluster = 0
        self.files = dict()
    
    def add_file(self, file_name, file_size_in_bytes):
        self.files[file_name] = File(file_name, file_size_in_bytes)
    
    def format(self):
        for i in range(self.num_of_cluster):
            self.FAT[i] = -1
        self.num_of_empty_cluster = self.num_of_cluster
        self.num_of_filled_cluster = 0
        self.files = dict()
    
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
    
    # ========== Memory Allocation Methods ==========
    
    def _calculate_required_clusters(self, file_size_in_bytes):
        """Calculate the number of clusters needed for a file."""
        return (file_size_in_bytes + self.cluster_size - 1) // self.cluster_size
    
    def _is_cluster_free(self, cluster_index):
        """Check if a cluster is free."""
        return self.FAT[cluster_index] == -1
    
    def _find_free_clusters(self):
        """Find all free clusters in the disk."""
        return [i for i in range(self.num_of_cluster) if self._is_cluster_free(i)]
    
    def _find_contiguous_free_block(self, start_index, required_clusters):
        """Find a contiguous block of free clusters starting from start_index."""
        if start_index >= self.num_of_cluster:
            return None
        
        count = 0
        end_index = start_index
        for i in range(start_index, self.num_of_cluster):
            if self._is_cluster_free(i):
                count += 1
                if count == required_clusters:
                    end_index = i
                    return (start_index, end_index)
            else:
                count = 0
                start_index = i + 1
        
        return None
    
    # ========== Contiguous Allocation Methods ==========
    
    def allocate_contiguous(self, file_name, file_size_in_bytes):
        """
        Allocate memory using First Fit contiguous allocation strategy.
        :param file_name: Name of the file
        :param file_size_in_bytes: Size of the file in bytes
        :return: Starting cluster index if successful, None if failed
        """
        required_clusters = self._calculate_required_clusters(file_size_in_bytes)
        
        if required_clusters > self.num_of_empty_cluster:
            raise InsufficientMemoryError(required_clusters, self.num_of_empty_cluster)
        
        # Search for first fit
        for start in range(self.num_of_cluster):
            block = self._find_contiguous_free_block(start, required_clusters)
            if block:
                start_cluster, end_cluster = block
                # Allocate the clusters
                for i in range(start_cluster, end_cluster + 1):
                    if i == end_cluster:
                        self.FAT[i] = -2  # End of file marker
                    else:
                        self.FAT[i] = i + 1  # Point to next cluster
                
                # Update file information
                if file_name not in self.files:
                    self.files[file_name] = File(file_name, file_size_in_bytes)
                
                file = self.files[file_name]
                file.allocation_type = 'contiguous'
                file.start_cluster = start_cluster
                file.allocated_clusters = list(range(start_cluster, end_cluster + 1))
                
                # Update disk statistics
                self.num_of_empty_cluster -= required_clusters
                self.num_of_filled_cluster += required_clusters
                
                return start_cluster
        
        raise InsufficientMemoryError(required_clusters, self.num_of_empty_cluster)
    
    # ========== Non-Contiguous Allocation Methods ==========
    
    def allocate_non_contiguous(self, file_name, file_size_in_bytes):
        """
        Allocate memory using non-contiguous (linked list/FAT) allocation strategy.
        :param file_name: Name of the file
        :param file_size_in_bytes: Size of the file in bytes
        :return: Starting cluster index if successful, None if failed
        """
        required_clusters = self._calculate_required_clusters(file_size_in_bytes)
        
        if required_clusters > self.num_of_empty_cluster:
            raise InsufficientMemoryError(required_clusters, self.num_of_empty_cluster)
        
        # Find free clusters
        free_clusters = self._find_free_clusters()
        
        if len(free_clusters) < required_clusters:
            raise InsufficientMemoryError(required_clusters, len(free_clusters))
        
        # Allocate clusters (take first available clusters)
        allocated_clusters = free_clusters[:required_clusters]
        start_cluster = allocated_clusters[0]
        
        # Link clusters using FAT
        for i in range(len(allocated_clusters)):
            if i == len(allocated_clusters) - 1:
                self.FAT[allocated_clusters[i]] = -2  # End of file marker
            else:
                self.FAT[allocated_clusters[i]] = allocated_clusters[i + 1]  # Point to next cluster
        
        # Update file information
        if file_name not in self.files:
            self.files[file_name] = File(file_name, file_size_in_bytes)
        
        file = self.files[file_name]
        file.allocation_type = 'non-contiguous'
        file.start_cluster = start_cluster
        file.allocated_clusters = allocated_clusters
        
        # Update disk statistics
        self.num_of_empty_cluster -= required_clusters
        self.num_of_filled_cluster += required_clusters
        
        return start_cluster
    
    # ========== Deallocation Methods ==========
    
    def deallocate_file(self, file_name):
        """
        Deallocate memory for a file.
        :param file_name: Name of the file to deallocate
        :return: True if successful, False if file not found
        """
        if file_name not in self.files:
            raise FileNotFoundError(file_name)
        
        file = self.files[file_name]
        allocated_clusters = file.allocated_clusters
        
        # Free all allocated clusters
        for cluster in allocated_clusters:
            self.FAT[cluster] = -1  # Mark as free
        
        # Update disk statistics
        num_clusters_freed = len(allocated_clusters)
        self.num_of_empty_cluster += num_clusters_freed
        self.num_of_filled_cluster -= num_clusters_freed
        
        # Remove file from files dictionary
        del self.files[file_name]
        
        return True
    
    def get_file_allocation_info(self, file_name):
        """
        Get allocation information for a file.
        :param file_name: Name of the file
        :return: Dictionary with allocation information
        """
        if file_name not in self.files:
            raise FileNotFoundError(file_name)
        
        file = self.files[file_name]
        return {
            'file_name': file_name,
            'allocation_type': file.allocation_type,
            'start_cluster': file.start_cluster,
            'allocated_clusters': file.allocated_clusters,
            'num_clusters': len(file.allocated_clusters),
            'file_size': file.size_in_bytes
        }
    
    # ========== File I/O Methods ==========
    
    def _get_cluster_chain(self, start_cluster):
        """
        Get the chain of clusters for a file starting from start_cluster.
        :param start_cluster: Starting cluster index
        :return: List of cluster indices in order
        """
        cluster_chain = []
        current = start_cluster
        
        while current != -1 and current != -2:
            cluster_chain.append(current)
            if self.FAT[current] == -2:
                break
            current = self.FAT[current]
        
        return cluster_chain
    
    def write_file_data(self, file_name, file_data):
        """
        Write file data to the disk's binary file.
        :param file_name: Name of the file
        :param file_data: Bytes data to write
        :return: True if successful
        """
        if file_name not in self.files:
            raise FileNotFoundError(file_name)
        
        file = self.files[file_name]
        
        # Ensure file size matches
        if len(file_data) > file.size_in_bytes:
            raise Exception(f"File data size ({len(file_data)} bytes) exceeds allocated size ({file.size_in_bytes} bytes)")
        
        # Get cluster chain
        if file.allocation_type == 'contiguous':
            cluster_chain = file.allocated_clusters
        else:
            cluster_chain = self._get_cluster_chain(file.start_cluster)
        
        # Write data to disk binary file
        disk_file_path = self.name + '.bin'
        with open(disk_file_path, 'r+b') as f:
            data_written = 0
            for cluster_idx in cluster_chain:
                cluster_offset = cluster_idx * self.cluster_size
                f.seek(cluster_offset)
                
                # Calculate how much data to write in this cluster
                remaining_data = len(file_data) - data_written
                data_to_write = min(remaining_data, self.cluster_size)
                
                if data_to_write > 0:
                    f.write(file_data[data_written:data_written + data_to_write])
                    data_written += data_to_write
                
                # Pad remaining cluster space with zeros if needed
                if data_to_write < self.cluster_size and data_written < len(file_data):
                    padding = self.cluster_size - data_to_write
                    f.write(b'\x00' * padding)
        
        return True
    
    def read_file_data(self, file_name):
        """
        Read file data from the disk's binary file.
        :param file_name: Name of the file
        :return: Bytes data of the file
        """
        if file_name not in self.files:
            raise FileNotFoundError(file_name)
        
        file = self.files[file_name]
        
        # Get cluster chain
        if file.allocation_type == 'contiguous':
            cluster_chain = file.allocated_clusters
        else:
            cluster_chain = self._get_cluster_chain(file.start_cluster)
        
        # Read data from disk binary file
        disk_file_path = self.name + '.bin'
        file_data = bytearray()
        
        with open(disk_file_path, 'rb') as f:
            for cluster_idx in cluster_chain:
                cluster_offset = cluster_idx * self.cluster_size
                f.seek(cluster_offset)
                
                # Read cluster data
                cluster_data = f.read(self.cluster_size)
                file_data.extend(cluster_data)
        
        # Trim to actual file size
        return bytes(file_data[:file.size_in_bytes])
    
    # ========== Defragmentation Methods ==========
    
    def defragment(self):
        """
        Defragment the entire disk by reorganizing all files to create contiguous blocks and consolidate free space.
        This reorganizes the entire disk layout for optimal space utilization.
        :return: Dictionary with defragmentation statistics
        """
        defrag_stats = {
            'files_moved': 0,
            'files_skipped': 0,
            'total_files': len(self.files),
            'clusters_reorganized': 0
        }
        
        if not self.files:
            return defrag_stats
        
        disk_file_path = self.name + '.bin'
        
        # Step 1: Read all file data and store temporarily
        file_data_map = {}
        file_info_map = {}
        
        for file_name, file_obj in self.files.items():
            try:
                file_data = self.read_file_data(file_name)
                file_data_map[file_name] = file_data
                file_info_map[file_name] = {
                    'size': file_obj.size_in_bytes,
                    'old_clusters': file_obj.allocated_clusters.copy(),
                    'allocation_type': file_obj.allocation_type
                }
            except Exception as e:
                defrag_stats['files_skipped'] += 1
                continue
        
        # Step 2: Free all clusters (mark as available)
        total_clusters_freed = 0
        for file_name, file_info in file_info_map.items():
            old_clusters = file_info['old_clusters']
            for cluster in old_clusters:
                self.FAT[cluster] = -1
            total_clusters_freed += len(old_clusters)
        
        # Update statistics
        self.num_of_empty_cluster = self.num_of_cluster
        self.num_of_filled_cluster = 0
        
        # Step 3: Clear files dictionary
        self.files = {}
        
        # Step 4: Reallocate all files contiguously from the beginning
        # Sort files by size (largest first) for better space utilization
        sorted_files = sorted(file_data_map.items(), key=lambda x: file_info_map[x[0]]['size'], reverse=True)
        
        for file_name, file_data in sorted_files:
            try:
                file_size = file_info_map[file_name]['size']
                old_clusters = file_info_map[file_name]['old_clusters']
                
                # Try to allocate contiguously
                try:
                    new_start_cluster = self.allocate_contiguous(file_name, file_size)
                    
                    # Write file data to new location
                    self.write_file_data(file_name, file_data)
                    
                    new_clusters = self.files[file_name].allocated_clusters
                    defrag_stats['files_moved'] += 1
                    
                    # Count clusters that changed position
                    if set(old_clusters) != set(new_clusters):
                        defrag_stats['clusters_reorganized'] += len(new_clusters)
                    
                except InsufficientMemoryError:
                    # If can't allocate contiguously, use non-contiguous
                    new_start_cluster = self.allocate_non_contiguous(file_name, file_size)
                    self.write_file_data(file_name, file_data)
                    defrag_stats['files_skipped'] += 1
                    
            except Exception as e:
                defrag_stats['files_skipped'] += 1
                continue
        
        return defrag_stats



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
if __name__ == "__main__":
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
