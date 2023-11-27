#!/usr/bin/env python3
##########################
# dBrowse - interact with
# a simplified FAT image
##########################
import struct
import Disk

# Disk name & block size
DISK_IMG = 'disk.img'
DISK_BS = 512

# Directory entry struct format:
# unsigned short, unsigned short, unsigned int, 24 chars
DIR_ENTRY_FORMAT = 'H H I 24s'

# Each directory entry should be 32 bytes long
DIR_ENTRY_SIZE = struct.calcsize(DIR_ENTRY_FORMAT)

class DirectoryEntry:
    def __init__(self, entry_type, block, metadata, name):
        self.entry_type = entry_type
        self.block = block
        self.metadata = metadata
        self.name = name.strip('\x00')

def read_disk_label(disk):
    label_block = disk.readBlock(0)
    label = struct.unpack(f'{disk.blocksize}s', label_block)[0].decode('ascii').rstrip('\x00')
    return label

def read_directory_entries(disk, block_number):
    entries = []
    data = disk.readBlock(block_number)
    for i in range(0, len(data), DIR_ENTRY_SIZE):
        entry_data = data[i:i + DIR_ENTRY_SIZE]
        (entry_type, block, metadata, name) = struct.unpack(DIR_ENTRY_FORMAT, entry_data)
        name = name.decode('ascii').rstrip('\x00')
        if entry_type != 0:  # If it's not an UNUSED_ENTRY
            entries.append(DirectoryEntry(entry_type, block, metadata, name))
    return entries

# Initialize Disk object
disk = Disk.Disk(DISK_IMG, DISK_BS)

# Read disk label
disk_label = read_disk_label(disk)
print("Disk Label: {}\n".format(disk_label))

# For simplicity, start in the root directory at block 2 
# We can assume our dFAT image's block 0 is disk label, and block 1 is the FAT
current_directory_block = 2
current_directory_name = "/"

def print_directory_contents(disk, directory_block):
    print(f"\nType\t\tSize\t\tName")
    print('-' * 50) # VISUALLY SEPARATE THE HEADING ROW FROM OUTPUT
    entries = read_directory_entries(disk, directory_block)
    for entry in entries:
        if entry.entry_type == 2:
            entry_type = 'Directory'
            print(f"{entry_type}\t\t\t{entry.name}")
        else:
            entry_type = 'File'
            size = entry.metadata
            print(f"{entry_type}\t\t{size}\t\t{entry.name}")

def change_directory(directory_entries, dir_name):
    global current_directory_block # THIS IS KIND OF UGLY
    global current_directory_name # AGAIN, UGLY... :-(
    for entry in directory_entries:
        if entry.name == dir_name and entry.entry_type == 2:  # DIR_ENTRY
            current_directory_block = entry.block
            current_directory_name = dir_name
            return True
    return False

def read_file(disk, directory_entries, file_name):
    for entry in directory_entries:
        if entry.name == file_name and entry.entry_type == 3:  # FILE_CHUNK
            block_data = disk.readBlock(entry.block)
            stripped_data = block_data.rstrip(b'\x00')
            struct_fmt = "{}s".format(len(stripped_data)) # SIZE OF FILE DATA TO UNPACK
            text_data = struct.unpack(struct_fmt, stripped_data)[0].decode('ascii')
            print(text_data)

# Main dBrowse command loop
while True:
    command = input("Enter command: ").strip().split()
    if not command: # NOTHING WAS ENTERED
        continue

    cmd = command[0].lower()
    directory_entries = read_directory_entries(disk, current_directory_block)
    
    if cmd == "dir":
        print_directory_contents(disk, current_directory_block)
        print(" ")
    elif cmd == "cd":
        if len(command) > 1:
            if not change_directory(directory_entries, command[1]):
                print("Directory not found.")
        else:
            print("No directory specified.")
        print(" ")
    elif cmd == "read":
        if len(command) > 1:
            read_file(disk, directory_entries, command[1])
        else:
            print("No file specified.\n")
    elif cmd == "pwd":
        print("Working Directory: {}\n".format(current_directory_name))
    elif cmd == "help":
        print("\nAvailable commands:")
        print(" ")
        print("help --> This command")
        print("dir  --> Show directory listing")
        print("cd   --> Change directory")
        print("read --> Read and print the contents of a file")
        print("pwd  --> Print the current working directory path")
        print("exit --> Quit the program\n")
    elif cmd == "exit":
        print("Exiting...")
        disk.printStats()
        exit(0)
    elif cmd == "clear": # UNDOCUMENTED, ONLY USED FOR TESTING :-) 
        import os
        os.system("clear")
    else:
        print("Unknown command.\n")
