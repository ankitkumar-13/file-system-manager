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
from object_and_file_manipulation import load_object, file_exists, update_disk
from custom_exceptions import (
    DuplicateDiskNameError,
    InvalidDiskSizeError,
    InvalidPermissionNotationError,
    InsufficientMemoryError,
    FileNotFoundError
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
                # Get file information with allocation details
                files_info = []
                if hasattr(disk, 'files') and disk.files:
                    for file_name, file_obj in disk.files.items():
                        # Format file size
                        size_bytes = file_obj.size_in_bytes
                        if size_bytes < 1024:
                            size_display = f"{size_bytes} B"
                        elif size_bytes < 1024 * 1024:
                            size_display = f"{round(size_bytes / 1024, 2)} KB"
                        elif size_bytes < 1024 * 1024 * 1024:
                            size_display = f"{round(size_bytes / (1024 * 1024), 2)} MB"
                        else:
                            size_display = f"{round(size_bytes / (1024 * 1024 * 1024), 2)} GB"
                        
                        file_info = {
                            'name': file_name,
                            'size': file_obj.size_in_bytes,
                            'size_display': size_display,
                            'allocation_type': getattr(file_obj, 'allocation_type', 'N/A'),
                            'start_cluster': getattr(file_obj, 'start_cluster', -1),
                            'num_clusters': len(getattr(file_obj, 'allocated_clusters', []))
                        }
                        files_info.append(file_info)
                
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
                    'files_count': len(disk.files) if hasattr(disk, 'files') else 0,
                    'files_info': files_info
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


def create_file_view(request, disk_name):
    """View for creating/adding a file to a disk"""
    all_disks = {}
    disk = None
    
    if file_exists(".fsmdata"):
        try:
            all_disks = load_object(".fsmdata")
            if disk_name in all_disks:
                disk = all_disks[disk_name]
        except Exception as e:
            messages.error(request, f'Error loading disk: {str(e)}')
            return redirect('core:home')
    
    if not disk:
        messages.error(request, f'Disk "{disk_name}" not found!')
        return redirect('core:home')
    
    if request.method == 'POST':
        uploaded_file = request.FILES.get('uploaded_file')
        file_name = request.POST.get('file_name', '').strip()
        file_size = request.POST.get('file_size', '').strip()
        file_unit = request.POST.get('file_unit', 'KB')
        allocation_type = request.POST.get('allocation_type', 'contiguous')
        
        # Check if file is uploaded or manual size is provided
        if uploaded_file:
            # Use uploaded file
            file_name = file_name or uploaded_file.name
            file_bytes = uploaded_file.size
            file_data = uploaded_file.read()
        else:
            # Manual size entry
            if not file_name:
                messages.error(request, 'File name is required!')
                return redirect('core:create_file', disk_name=disk_name)
            
            if not file_size or not file_size.replace('.', '').isdigit():
                messages.error(request, 'Either upload a file or provide a valid file size!')
                return redirect('core:create_file', disk_name=disk_name)
            
            try:
                file_size_float = float(file_size)
                if file_size_float <= 0:
                    messages.error(request, f'File size must be greater than 0 {file_unit}!')
                    return redirect('core:create_file', disk_name=disk_name)
                
                # Convert to bytes
                if file_unit == "B":
                    file_bytes = int(file_size_float)
                elif file_unit == "KB":
                    file_bytes = int(file_size_float * 1024)
                elif file_unit == "MB":
                    file_bytes = int(file_size_float * 1024 * 1024)
                elif file_unit == "GB":
                    file_bytes = int(file_size_float * 1024 * 1024 * 1024)
                else:
                    messages.error(request, 'Invalid file unit!')
                    return redirect('core:create_file', disk_name=disk_name)
                
                file_data = None  # No file data for manual creation
            except ValueError:
                messages.error(request, 'Invalid file size format!')
                return redirect('core:create_file', disk_name=disk_name)
        
        if file_name in disk.files:
            messages.error(request, f'File "{file_name}" already exists in this disk!')
            return redirect('core:create_file', disk_name=disk_name)
        
        try:
            # Allocate file based on allocation type
            if allocation_type == 'contiguous':
                start_cluster = disk.allocate_contiguous(file_name, file_bytes)
                messages.success(request, f'File "{file_name}" created successfully using contiguous allocation (starting at cluster {start_cluster})!')
            elif allocation_type == 'non-contiguous':
                start_cluster = disk.allocate_non_contiguous(file_name, file_bytes)
                messages.success(request, f'File "{file_name}" created successfully using non-contiguous allocation (starting at cluster {start_cluster})!')
            else:
                messages.error(request, 'Invalid allocation type!')
                return redirect('core:create_file', disk_name=disk_name)
            
            # Write file data if uploaded
            if file_data is not None:
                disk.write_file_data(file_name, file_data)
                messages.success(request, f'File data written to disk successfully!')
            
            # Update disk in storage
            all_disks[disk_name] = disk
            update_disk(all_disks)
            
            return redirect('core:disk_stats', disk_name=disk_name)
            
        except InsufficientMemoryError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error creating file: {str(e)}')
        
        return redirect('core:create_file', disk_name=disk_name)
    
    # GET request - show form
    disk_data = {
        'name': disk.name,
        'size_in_bytes': disk.size_in_bytes,
        'size_mb': round(disk.size_in_bytes / (1024 * 1024), 2),
        'cluster_size': disk.cluster_size,
        'num_of_cluster': disk.num_of_cluster,
        'num_of_empty_cluster': disk.num_of_empty_cluster,
        'num_of_filled_cluster': disk.num_of_filled_cluster,
    }
    
    return render(request, 'core/create_file.html', {
        'disk': disk_data
    })


def delete_file_view(request, disk_name, file_name):
    """View for deleting a file from a disk"""
    all_disks = {}
    
    if file_exists(".fsmdata"):
        try:
            all_disks = load_object(".fsmdata")
            if disk_name not in all_disks:
                messages.error(request, f'Disk "{disk_name}" not found!')
                return redirect('core:home')
            
            disk = all_disks[disk_name]
            
            try:
                disk.deallocate_file(file_name)
                all_disks[disk_name] = disk
                update_disk(all_disks)
                messages.success(request, f'File "{file_name}" deleted successfully!')
            except FileNotFoundError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error deleting file: {str(e)}')
                
        except Exception as e:
            messages.error(request, f'Error loading disk: {str(e)}')
    
    return redirect('core:disk_stats', disk_name=disk_name)


def download_file_view(request, disk_name, file_name):
    """View for downloading/extracting a file from a disk"""
    from django.http import HttpResponse
    
    all_disks = {}
    
    if file_exists(".fsmdata"):
        try:
            all_disks = load_object(".fsmdata")
            if disk_name not in all_disks:
                messages.error(request, f'Disk "{disk_name}" not found!')
                return redirect('core:home')
            
            disk = all_disks[disk_name]
            
            try:
                # Read file data from disk
                file_data = disk.read_file_data(file_name)
                file_obj = disk.files[file_name]
                
                # Create HTTP response with file data
                response = HttpResponse(file_data, content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                response['Content-Length'] = len(file_data)
                
                return response
                
            except FileNotFoundError as e:
                messages.error(request, str(e))
                return redirect('core:disk_stats', disk_name=disk_name)
            except Exception as e:
                messages.error(request, f'Error reading file: {str(e)}')
                return redirect('core:disk_stats', disk_name=disk_name)
                
        except Exception as e:
            messages.error(request, f'Error loading disk: {str(e)}')
            return redirect('core:home')
    
    messages.error(request, 'Disk not found!')
    return redirect('core:home')


def defragment_disk_view(request, disk_name):
    """View for defragmenting a disk"""
    all_disks = {}
    
    if file_exists(".fsmdata"):
        try:
            all_disks = load_object(".fsmdata")
            if disk_name not in all_disks:
                messages.error(request, f'Disk "{disk_name}" not found!')
                return redirect('core:home')
            
            disk = all_disks[disk_name]
            
            try:
                # Perform defragmentation
                stats = disk.defragment()
                
                # Update disk in storage
                all_disks[disk_name] = disk
                update_disk(all_disks)
                
                if stats['files_moved'] > 0:
                    messages.success(request, 
                        f'Disk defragmentation completed! {stats["files_moved"]} file(s) reorganized, '
                        f'{stats["clusters_reorganized"]} cluster(s) moved, '
                        f'{stats["files_skipped"]} file(s) skipped.')
                else:
                    messages.info(request, 
                        f'No defragmentation needed. Disk is already optimized or no files to defragment.')
                    
            except Exception as e:
                messages.error(request, f'Error during defragmentation: {str(e)}')
                
        except Exception as e:
            messages.error(request, f'Error loading disk: {str(e)}')
            return redirect('core:home')
    
    return redirect('core:disk_stats', disk_name=disk_name)
