from django.shortcuts import render, redirect
from django.contrib import messages
import sys
import os
from pathlib import Path

# Add parent directory to path to import root Python files
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from basic_operations import (
    create_disk as create_disk_func,
    check_disk_stat,
    refresh_disks,
    display_all_disks,
    Disk
)
from object_and_file_manipulation import load_object, file_exists
from custom_exceptions import (
    DuplicateDiskNameError,
    InvalidDiskSizeError,
    InvalidPermissionNotationError
)


def home(request):
    """Main dashboard view"""
    all_disks = {}
    if file_exists(".fsmdata"):
        try:
            all_disks = load_object(".fsmdata")
        except:
            all_disks = {}
    
    # Convert disk objects to dictionaries for template
    disks_data = []
    for name, disk in all_disks.items():
        disks_data.append({
            'name': disk.name,
            'size_in_bytes': disk.size_in_bytes,
            'size_mb': round(disk.size_in_bytes / (1024 * 1024), 2),
            'cluster_size': disk.cluster_size,
            'num_of_cluster': disk.num_of_cluster,
            'num_of_empty_cluster': disk.num_of_empty_cluster,
            'num_of_filled_cluster': disk.num_of_filled_cluster,
            'owner': disk.owner,
            'files_count': len(disk.files) if hasattr(disk, 'files') else 0
        })
    
    return render(request, 'core/home.html', {
        'disks': disks_data,
        'disks_count': len(disks_data)
    })


def create_disk_view(request):
    """View for creating a new disk"""
    if request.method == 'POST':
        disk_name = request.POST.get('disk_name', '').strip()
        disk_size = request.POST.get('disk_size', '').strip()
        disk_unit = request.POST.get('disk_unit', 'MB')
        
        if not disk_name:
            messages.error(request, 'Disk name is required!')
            return redirect('core:home')
        
        if not disk_size or not disk_size.isdigit():
            messages.error(request, 'Valid disk size is required!')
            return redirect('core:home')
        
        disk_size_int = int(disk_size)
        if disk_size_int <= 0:
            messages.warning(request, f'Disk size must be greater than 0 {disk_unit}! Please enter a valid size.')
            return redirect('core:home')
        
        # Format the disk size input as expected by create_disk function
        disk_size_input = f"{disk_size} {disk_unit}"
        
        try:
            # We need to modify the create_disk function to work without input()
            # For now, let's create the disk directly
            import re
            from object_and_file_manipulation import register_disk
            
            disk_bytes = 0
            if disk_unit == "KB":
                disk_bytes = int(disk_size) * 1024
            elif disk_unit == "MB":
                disk_bytes = int(disk_size) * 1024 * 1024
            elif disk_unit == "GB":
                disk_bytes = int(disk_size) * 1024 * 1024 * 1024
            
            if file_exists(disk_name + '.bin'):
                raise DuplicateDiskNameError(disk_name)
            
            # Create disk file
            with open(disk_name + '.bin', 'wb') as f:
                disk_obj = Disk(disk_name, disk_bytes)
                f.seek(disk_obj.size_in_bytes - 1)
                f.write(b"\0")
                register_disk(disk_obj)
            
            messages.success(request, f'Disk "{disk_name}" created successfully!')
        except DuplicateDiskNameError as e:
            messages.error(request, str(e))
        except InvalidDiskSizeError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('core:home')
    
    return redirect('core:home')


def disk_stats_view(request, disk_name):
    """View for displaying disk statistics"""
    all_disks = {}
    disk_data = None
    
    if file_exists(".fsmdata"):
        try:
            all_disks = load_object(".fsmdata")
            if disk_name in all_disks:
                disk = all_disks[disk_name]
                disk_data = {
                    'name': disk.name,
                    'size_in_bytes': disk.size_in_bytes,
                    'size_mb': round(disk.size_in_bytes / (1024 * 1024), 2),
                    'size_gb': round(disk.size_in_bytes / (1024 * 1024 * 1024), 2),
                    'cluster_size': disk.cluster_size,
                    'num_of_cluster': disk.num_of_cluster,
                    'num_of_empty_cluster': disk.num_of_empty_cluster,
                    'num_of_filled_cluster': disk.num_of_filled_cluster,
                    'owner': disk.owner,
                    'files': list(disk.files.keys()) if hasattr(disk, 'files') else [],
                    'files_count': len(disk.files) if hasattr(disk, 'files') else 0
                }
        except Exception as e:
            messages.error(request, f'Error loading disk: {str(e)}')
    
    if not disk_data:
        messages.error(request, f'Disk "{disk_name}" not found!')
        return redirect('core:home')
    
    return render(request, 'core/disk_stats.html', {'disk': disk_data})


def refresh_disks_view(request):
    """View for refreshing the disk list"""
    try:
        if refresh_disks():
            messages.success(request, 'Disk list updated successfully!')
        else:
            messages.info(request, 'No changes made to disk list.')
    except Exception as e:
        messages.error(request, f'Error refreshing disks: {str(e)}')
    
    return redirect('core:home')
