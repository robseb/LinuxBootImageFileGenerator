#!/usr/bin/env python
#
#            ########   ######   ##    ##  #######   ######  ########  #######                  
#            ##     ## ##    ##   ##  ##  ##     ## ##    ##    ##    ##     ##           
#            ##     ## ##          ####   ##     ## ##          ##    ##     ##        
#            ########   ######      ##    ##     ## ##          ##    ##     ##       
#            ##   ##         ##     ##    ##     ## ##          ##    ##     ##      
#            ##    ##  ##    ##     ##    ##     ## ##    ##    ##    ##     ##        
#            ##     ##  ######      ##     #######   ######     ##     #######         
#             ___          _   _      _     ___               _                 
#            | _ )  _  _  (_) | |  __| |   / __|  _  _   ___ | |_   ___   _ __  
#            | _ \ | || | | | | | / _` |   \__ \ | || | (_-< |  _| / -_) | '  \ 
#            |___/  \_,_| |_| |_| \__,_|   |___/  \_, | /__/  \__| \___| |_|_|_|
#                                                  |__/                              
#
#
# Robin Sebastian (https://github.com/robseb)
# © rsyocto GmbH & Co. KG (https://www.rsyocto.com) 2021-2025
#
# Contact:    git@robseb.de
# Repository: https://github.com/robseb/LinuxBootImageFileGenerator
#
# Python script to automatically generate a bootable image file with a 
# specified partition table for embedded Linux distributions
#
# (2020-07-17) Vers.1.0 
#   first Version 
#
# (2020-07-23) Vers.1.01
#   date code in output file names
#
# (2020-07-26) Vers. 1.02
#   delate unziped files after build
#
# (2020-08-04) Vers. 1.03
#   fixed an issue with improperly copied symbolic links
#   Bug Reporter: github.com/NignetShark
#
# (2020-08-04) Vers. 1.04
#   fixed an issue with file ownerships and adding deconstructor to unmout 
#   all open loopback devices 
#   Bug Reporter: github.com/NignetShark
#
# (2020-08-09) Vers. 1.05
#  adding u-boot script compilation feature 
#
# (2020-11-24) Vers. 1.06
#  Detection of wrong Device Tree compilation
#
# (2020-12-03) Vers. 1.07
#  Bug fix for wrong file/build detection
#
# (2024-07-11) Vers. 1.08
#  Fixing loopback device mounting issue with the new Linux Kernel
#
# (2025-02-15) Vers. 1.10
#  Performance improvements and bug fixes
#  Extended partition support
#  
version = "1.10"

import os
import sys
import time
import io
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from typing import NamedTuple
import math
import glob
from pathlib import Path
from datetime import datetime

 
class Partition:
    """
    Class for discripting a filesystem partition 
    """

    scan_mode: int 
    """
    File scan mode:
      1= List every file 
      0= List only top files and folders
    """

    id:   int 
    """
    Number of Partition (O is the lowest)
    """

    type: str 
    """
    Partition Filesystem 
    """

    type_hex: str  
    """
    Partition Filesystem as HEX value for "fdisk"
    """

    type_mkfs: str            
    """
    Partition Filesystem as MKFS value for "mkfs."
    """
    
    size_str: str            
    """
    Partition size as string with unit (KB,MB)
    """

    size : int               
    """
    Partition size in Byte (0 => dynamic file size)
    """

    offset_str: str           
    """
    Partition offset space  as string to a dynamic size 
    """

    offset: int               
    """
    Partition offset space as byte to a dynamic size 
    """
    
    fileDirectories =[]       
    """
    File directory of each file to be imported to the partition
    """
    
    totalFileSize: int        
    """
    Total file size of the partition (Byte)
    """

    totalFileSizeStr: str    
    """
    Total file size of the partition (string 1GB,1MB)
    """

    totalSize:  str           
    """
    Total size of the partition (Byte)
    """
    
    totalSizeStr:  str
    """
    Total size of the partition (string 1GB, 1MB)
    """
    
    comp_devicetree: bool    
    """
    Compile a Linux dts devicetree file if available
    """

    comp_ubootscript: str     
    """
    Compile u-boot script "boot.script" for architecture "arm" or "arm64"
    """

    unzip_file: bool          
    """
    unzip a compressed file if available 
    """

    BlockSectorSize: int      
    """
    Block size of the partition
    """

    __filesImported:bool   
    """
    Indicates that files are imported to the list 
    """

    __unzipedFiles =[]        
    """
    List of all unziped files/folder to remove in the deconstructor  
    """

    __dtsFileDir: str        
    """
    Direcortry of the DTS file to remove from the partition
    """

    __ubootscrFileDir: str   
    """
    Direcortry of the u-boot script file to remove from the partition
    """

    __uncompressedFilesDir =[]
    """
    Direcortries of the uncompressed archive files
    """

    extendedPartition: bool 
    """
    Is the partition an extended partition?
    """

    def __init__(self,diagnosticOutput=True, id=None, type=None,size_str=None,
                 offset_str=None,devicetree=False,unzip=False,ubootscript=None, operation_mode=0):
        """
        Constructor for discripting a filesystem partition
        
        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * id (int): Partition Number of the partition table (1-4)
            * type (str): Filesystem name as string  "ext[2-4], Linux, xfs, vfat, fat, none, raw, swap"
            * size_str (str): Size of the partition as string
                            Format: <no>: Byte, <no>K: Kilobyte, <no>M: Megabyte or <no>G: Gigabyte
                                    "*" dynamic file size => Size of the files2copy + offset
            * offset_str (str): In case a dynamic size is used the offset value is added to file size
            * devicetree (bool): Compile the Linux Device (.dts) inside the partition if available
            * unzip (bool): Unzip a compressed file if available
            * ubootscript (str): Compile the u-boot script "boot.script" for architecture "arm" or "arm64"
            * operation_mode (int): File scan mode: 1= List every file | 0= List only top files and folders
        **Returns:**
            *none*
        **Raises:**
            *The ubootscript input is for parrtion No X is not allowed!*
        """

        self.extendedPartition = False
        # Convert the partition number to int 
        try:
            self.id = int(id)
        except ValueError:
            raise Exception('Failed to convert "id" to integer!') 
        
        # Check that the selected filesystem is supported 
        if not re.search("^(ext[2-4]|Linux|xfs|vfat|fat|none|raw|swap|extended)$", type, re.I):
            raise Exception('Filesize "'+str(type)+'" of "type" and id '+str(id)+' is unknown!')
        # Convert type to lowercase
        self.type = type.lower()

        # Convert the format to "fdisk" HEX codes and to "mkfs" for "mkfs.xxx"
        # ext2, ext3,ext4,xfs ... -> LINUX
        if re.match('^ext[2-4]|xfs|Linux$', self.type):
            self.type_hex  = '83'                # Linux 
            self.type_mkfs = "mkfs."+self.type  # mkfs.ext3, ...
        # vfat, fat --> FAT32
        elif re.match('^vfat|fat$', self.type): 
            self.type_hex  = 'b' # FAT32 
            self.type_mkfs = 'mkfs.vfat' 
        # raw, none -> Empty
        elif re.match('^raw|none$', self.type):
            self.type_hex  = 'a2' # Empty
            self.type_mkfs = None
        # Linux swap drive (RAM -> HHD) 
        elif self.type in 'swap':
            self.type_hex = '82' # Swap
            self.type_mkfs = None
        elif self.type in 'extended':
            self.extendedPartition = True
            self.type_hex = '05'
            self.type_mkfs = 'mkfs.ext4'
        else: 
            raise Exception('Failed to decode partition type '+str(self.type))

        self.size_str = size_str
        # Convert size format to integer 
        self.size = self.__size2uint(size_str)

        # Use the offset value only by a dynamic size 
        if self.size == 0:
            if offset_str == '*':
                raise Exception('A dynamic size (*) is for the offset not allowed!')

            self.offset_str = offset_str
            self.offset = self.__size2uint(offset_str)
        else:
            self.offset = 0
            self.offset_str ='0'
            self.__print(diagnosticOutput,'NOTE: The offset value will be ignored!')

        # Should a dts Linux devicetree file be compiled?
        self.comp_devicetree = devicetree

        # Should compressed files be unziped?
        self.unzip_file = unzip
        self.scan_mode = operation_mode

        # should the u-boot script "u-boot.script" be complied?
        if not re.match('^arm|arm|$', ubootscript): 
            raise Exception('The ubootscript input is for parrtion No. '+str(self.id)+ \
            ' not allowed. Use "","arm" or "arm64" ')
        self.comp_ubootscript = ubootscript

        self.totalSize = None
        self.__dtsFileDir = None
        self.__ubootscrFileDir=None
        self.__uncompressedFilesDir=[]

    def __del__(self):
        """
        Deconstructor of discripting a filesystem partition
        """

        for it in self.__unzipedFiles:
            if os.path.isfile(it):
                try:
                    os.system('sudo rm '+it)
                except Exception:
                    raise Exception('Failed to remove the archive content file "'+str(it)+'"')
            elif os.path.isdir(it):
                try:
                    os.system('sudo rm -r '+it)
                except Exception:
                    raise Exception('Failed to remove the archive content folder "'+str(it)+'"')

    def setTotalSize(self, totalSize):
        """
         Set the total size of the partition
        
        **Parameters:**
            totalSize (int): Total size of the partition in bytes
        **Returns:**
            *none*
        **Raises:**
            *none*
        """

        self.totalSize = totalSize
        self.totalSizeStr = self.__convert_byte2str(totalSize)
 
    def importFileDirectories(self,diagnosticOutput,*fileDirectories):
        """
        Import files to the file list for the partition

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * fileDirectories (list): List of File directories to import
        **Returns:**
            *none*
        **Raises:**
            * *The file list to import must be specified*
            * *For RAW partitions are no folders allowed*
            * *File/Folder "[file]" does not exist!*
            * *Failed to find the uncompiled device tree file*
            * *Failed to find the uncompiled u-boot script*
            * *Failed to find the unzip file*
        """
        self.__print(diagnosticOutput,'--> Import files to the file list'+\
                     'for the partition No.'+str(self.id))
        if fileDirectories == None:
            raise Exception('The file list to import must be specified')
        # Check that all phases are valid
        for file in fileDirectories:
            if os.path.isdir(file):
                # In RAW partitions folders are not allowed 
                if self.type_hex =='a2':
                    raise Exception('For RAW partitions are no folders allowed')
            elif not os.path.isfile(file):
                    raise Exception(' File/Folder "'+str(file)+'" does not exist!')

            # Compile the Linux Device Tree if necessary 
            dtsFileDir = None 
            if self.comp_devicetree == True:
                dtsFileDir = self.__compileDeviceTree(diagnosticOutput,file)

            # Compile the u-boot script 
            ubootscrFileDir = None 
            if self.comp_ubootscript == "arm" or self.comp_devicetree == "arm64":
                ubootscrFileDir = self.__compileubootscript(diagnosticOutput,file)

            # Uncompress archive files if necessary
            uncompressedFilesDir =[]
            if self.unzip_file == True:
                uncompressedFilesDir = self.__uncompressArchivefiles(diagnosticOutput,file)

        # Remove the to uncompiled Linux device tree file from the list
        if not dtsFileDir == None:
            self.__print(diagnosticOutput,'   Exclute the file "'+dtsFileDir+'" from the list')
            if not dtsFileDir in self.fileDirectories:
                    raise Exception('Failed to find the uncompiled device tree file '+dtsFileDir)
            self.fileDirectories.remove(dtsFileDir)
        
        # Remove the to uncompiled u-boot script from the list
        if not ubootscrFileDir == None:
            self.__print(diagnosticOutput,'   Exclute the file "'+ubootscrFileDir+'" from the list')
            if not ubootscrFileDir in self.fileDirectories:
                    raise Exception('Failed to find the uncompiled u-boot script: '+ubootscrFileDir)
            self.fileDirectories.remove(ubootscrFileDir)


        # Remove all uncompressed archive file from the list
        if not uncompressedFilesDir == None:
            for arch in uncompressedFilesDir:
                self.__print(diagnosticOutput,'   Exclute the archive file "'+arch+'" from the list')
                if not arch in self.fileDirectories:
                    raise Exception('Failed to find the unzip file '+arch)
                self.fileDirectories.remove(arch)
        self.__filesImported = True
        self.fileDirectories=fileDirectories

    def findFileDirectories(self,diagnosticOutput=True,searchPath = None, \
                            compileDevTreeUboot = True, unzipArchive=True):
        """
        Find files in a directory and add them to the file list for the partition

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * searchPath (str): Directory to search
            * compileDevTreeUboot (bool): Do complie the devicetree and a u-boot script
            * unzipArchive (bool): Do unzip archvie files (such as the rootfs)
        **Returns:**
            *none*
        **Raises:**
            * *Device Tree complation Failed! Please check this file!*
            * *U-boot script complation Failed! Please check this file!*
            * *For RAW partitions are no folders allowed!*
            * *Failed process a file for importing!*
            * *Failed to find the uncompliled device tree file!*
            * *Failed to find the uncompiled u-boot script*
            * *Failed to find the unzip file*
        """

        self.__print(diagnosticOutput,'--> Scan path "'+str(searchPath)+'" to find a files inside it')
        
        if len(os.listdir(searchPath)) == 0:
            # Folder has no content
            self.__print(diagnosticOutput,'    Has no content')
            return

        # Compile the Linux Device Tree if necessary 
        if compileDevTreeUboot:
            if self.comp_devicetree == True:
                self.__dtsFileDir = self.__compileDeviceTree(diagnosticOutput,searchPath)
                if self.__dtsFileDir==None:
                    raise Exception('Device Tree complation Failed! Please check this file!')

            # Compile the u-boot script 
            if self.comp_ubootscript == "arm" or self.comp_devicetree == "arm64":
                self.__ubootscrFileDir = self.__compileubootscript(diagnosticOutput,searchPath)
                if self.__ubootscrFileDir==None:
                    raise Exception('U-boot script complation Failed! Please check this file!')

        if unzipArchive:
            # Uncompress archive files if necessary
            if self.unzip_file == True:
                self.__uncompressedFilesDir = self.__uncompressArchivefiles(diagnosticOutput,searchPath)

        fileDirectories = []
        # Scan operating mode: Scan Mode 0 -> Scan only the top folder 
        #                                      Add folders and files of the top folder to the list
        if self.scan_mode == 0:
            try:
                # Scan the top folder 
                for folder in os.listdir(searchPath):
                    if os.path.isdir(searchPath+'/'+folder):
                        # In RAW partition folders are not allowed 
                        if self.type_hex =='a2':
                            raise Exception('For RAW partitions are no folders allowed')

                        fileDirectories.append(searchPath+'/'+folder)
                    elif os.path.isfile(searchPath+'/'+folder):
                        fileDirectories.append(searchPath+'/'+folder)
            except OSError as ex:
                raise Exception('Failed process a file for importing! Msg:'+str(ex))
        
        # Scan operating mode: Scan Mode 1 -> Scan each file in every folder  
        #                                      Find every file in the top folder and in sub-folders 
        #                                      and add them to the list
        else:
        # List every file 
            # List the pathes of all folders inside the folder
            folderDirectories =[]
            scanedFolders =[]
            scanpath =searchPath
            try:
                # Scan the folder for new directories 
                while True:
                    for folder in os.listdir(scanpath):
                        if os.path.isdir(scanpath+'/'+folder):
                            folderDirectories.append(scanpath+'/'+folder)
                            self.__print(diagnosticOutput,'    Folder: '+scanpath+'/'+folder)
                    # Mark the folder as scanned 
                    scanedFolders.append(scanpath)
                    # Find a folder that is not processed jet
                    scanpath = None
                    for proc in folderDirectories:
                        if not proc in scanedFolders:
                            scanpath = proc
                    if scanpath == None:
                        # all directories are processed 
                        break
                # For RAW partitions are only files allowed
                if self.type_hex =='a2' and len(folderDirectories) >0:
                    raise Exception('For RAW partitions are no folders allowed')

                # always scan the top folder for files 
                for file in os.listdir(searchPath):
                    if os.path.isfile(searchPath+'/'+file):
                        self.__print(diagnosticOutput,'    File: '+searchPath+'/'+file)
                        fileDirectories.append(searchPath+'/'+file)
                # Find every file inside these folders 
                for folder in folderDirectories:
                    for file in os.listdir(folder):
                        if os.path.isfile(folder+'/'+file):
                            self.__print(diagnosticOutput,'    File: '+folder+'/'+file)
                            fileDirectories.append(folder+'/'+file)
        
            except OSError as ex:
                raise Exception('Failed process a file for importing! Msg:'+str(ex))
        # For every mode:
    
        # Avoid issues by removing all doubled files from the list
        self.fileDirectories =  list(set(fileDirectories))


        # Remove the uncompiled Linux device tree file from the list
        if not self.__dtsFileDir == None:
            self.__print(diagnosticOutput,'   Exclute the file "'+\
                self.__dtsFileDir+'" from the list')
            if not self.__dtsFileDir in self.fileDirectories:
                    raise Exception('Failed to find the uncompliled device tree file '+\
                        self.__dtsFileDir)
            self.fileDirectories.remove(self.__dtsFileDir)
        
        # Remove the to uncompiled u-boot script from the list
        if not self.__ubootscrFileDir == None:
            self.__print(diagnosticOutput,'   Exclute the file "'+\
                self.__ubootscrFileDir+'" from the list')
            if not self.__ubootscrFileDir in self.fileDirectories:
                    raise Exception('Failed to find the uncompiled u-boot script: '+\
                        self.__ubootscrFileDir)
            self.fileDirectories.remove(self.__ubootscrFileDir)

        # Remove all uncompressed archive files form the list
    
        if not self.__uncompressedFilesDir == None:
            for arch in self.__uncompressedFilesDir:
                self.__print(diagnosticOutput,'   Exclute the archive file "'+arch+'" from the list')
                if not arch in self.fileDirectories:
                    raise Exception('Failed to find the unzip file '+arch)
                self.fileDirectories.remove(arch)

        self.__print(diagnosticOutput,'== File processing for the folder is done')
        self.__print(diagnosticOutput,'Number of files: '+str(len(self.fileDirectories)))
        self.__filesImported = True

    def updateSectores(self,startSector=0, BlockSectorSize=0):
        """
        Update the Block and Sector sizes of the partition

        **Parameters:**
            * startSector (int): Start sector
            * BlockSectorSize (int): Block size
        **Returns:**
            *none*
        **Raises:**
            *none*
        """
        self.startSector = round(startSector)
        self.BlockSectorSize = round(BlockSectorSize)
      
    def giveWorkingFolderName(self,diagnosticOutput=True):
        """
        Return a folder name for the partition for user file import

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
        **Returns:**
            * working folder name
        **Raises:**
            *none*
        """
        working_folder_pat ='Pat_'+str(self.id)+'_'+str(self.type)
        self.__print(diagnosticOutput,'--> Working folder name:"'+working_folder_pat+'"')
        return working_folder_pat
        
    def calculatePartitionFilesize(self,diagnosticOutput=True):
        """
        Calculate the total file size of all files to import to the partition

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
        **Returns:**
            *none*
        **Raises:**
            * *Error: Import files before running the method "calculatePartitionFilesize()"!*
            * *The partition has no files to import!*
            * *The partition No. has no size!*
            * *Error: NOT ENOUGH DISK SPACE CONFIGURED ON PARTITION No. X The chosen size of is to small to fit all files*
        """

        self.totalFileSize =0
        # Files in the list to progress ?
        if self.__compileDeviceTree == None:
            raise Exception('Error: Import files before running the'+\
                            ' method "calculatePartitionFilesize()"!')

        if self.fileDirectories == None or self.fileDirectories ==[]:
            if not self.type_hex=='a2':
                raise Exception(' The partition '+str(self.id)+' has no files to import!\n'+ \
                                ' This is not allowed! Please delate the partition from the table\n'+\
                                ' or import some files!')
            else:
                self.__print(diagnosticOutput,'Warning: The partition '+str(self.id)+' has no files to import')
            return

        self.__print(diagnosticOutput,'--> Calculate the entire size of partition no.'+str(self.id))
        
        # Calculate total size of the files to add to the partition
        for file in self.fileDirectories: 
            self.__print(diagnosticOutput,'   Read file size of: '+str(file))
            if(os.path.isfile(file)):
                try:
                    self.totalFileSize += os.path.getsize(file)
                except Exception:
                    raise Exception("Failed to get size of the file: "+str(file))
            else:
                if self.scan_mode == 1:
                    self.__print(diagnosticOutput,'WARNING: File path: '+str(file)+' does not exist')
                else:
                    self.__print(diagnosticOutput,'   Calculate folder size of folder "'+file+'"')
                    # Calculate the size of a folder
                    dir = Path(file)
                    self.totalFileSize += sum(f.stat().st_size for f in dir.glob('**/*') if f.is_file())
        
        # Check that the files fit in the partition
        if self.size != 0: 
            if self.totalFileSize > self.size:
                raise Exception('ERROR: NOT ENOUGH DISK SPACE CONFIGURED ON PARTITION NO.'+str(self.id)+'\n'+ \
                                'The chosen size of '+str(self.size_str)+ \
                                ' ['+str(self.size)+'B] is to small to fit all files (total size:'+ \
                                self.__convert_byte2str(self.totalFileSize)+' ['+ \
                                str(self.totalFileSize)+'B])')
            self.totalSize= self.size
        else:
        # In dynamic file size mode: add the offset to the total size of the files
            self.totalSize = self.totalFileSize + self.offset

        if self.totalSize == 0:
            raise Exception('The partition No.'+str(self.id)+' has no size!')
        
        # Convert byte size to string (1MB, 1GB,...)
        self.totalFileSizeStr = self.__convert_byte2str(self.totalFileSize)
        self.totalSizeStr     = self.__convert_byte2str(self.totalSize)


    def __print(self,diagnosticOutput,str):
        """
        Debug Print

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * str (str): String to print
        **Returns:**
            *none*
        """
        if diagnosticOutput:
            print(str)

    def __convert_byte2str(self, size_bytes):
        """
        Convert a byte size to a string format (1GB,1MB...)
        
        **Parameters:**
            * size_bytes (int): Byte value to convert
        **Returns:**
            * Size in string format
        **Raises:**
            *none*
        """

        if size_bytes == 0:
            return "0B"
        size_name = ("B", "K", "M", "G", "T", "P", "E", "Z", "Y")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = math.ceil(size_bytes / p)
        s = round(s,0)
        s = int(s)
        ret = "%s %s" % (s, size_name[i])
        return ret.replace(" ","")

    def __size2uint(self,size_value):
        """
        Convert the size format to unsigned integer

        **Parameters:**
            * size_value (str): Size value as String to convert
        **Returns:**
            * size in byte
        **Raises:**
            * *Failed to convert size value [size_value] to integer!*
        """

        factor = 1
        # check if size contains a "*" -> return 0 to indicate dynamic 
        if size_value == "*":
            return 0

        inp = re.match("^[0-9]+[KMG]?$", size_value, re.I)
        # Is the input valid? 
        if inp == None:
            raise Exception(str(size_value)+' is not in the right format!') 
        else:
            # Decode the unit (KB,MB,GB) and the value 
            size_unit  = re.search("[KMG]+$", inp.group(0), re.I)
            size_value = re.search("^[0-9]+", inp.group(0), re.I)
            # Multiply with the depending factor of the unit
            if size_unit :
                # Read the upper character 
                unit = size_unit.group(0).upper()
                if unit == 'K':
                    factor = 1024
                elif unit == 'M':
                    factor = 1024*1024
                elif unit == 'G':
                    factor = 1024*1024*1024

        # Convert the value string to integer 
        try:
            size  = int(size_value.group(0))
        except ValueError:
            raise Exception('Failed to convert size value '+str(size_value)+' to integer!') 
        
        size = size * factor
        return size

    def __compileDeviceTree(self,diagnosticOutput=True,searchPath =None):
        """
        Compile a Linux Device Tree file (dts) if available

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * searchPath (str): Directory to search
        **Returns:**
            * File path of the compiled device tree file
        **Raises:**
            * *More than one .dts file found! This feature is not supported*
            * *No Linux Devicetree .dts file is found in the top folder!*
            * *Failed to compile the Linux Devicetree file "[dts_file_name]"*
            * *Compilation of the Linux Device Tree failed!*
        """

        singleFile = len(os.listdir(searchPath)) == 0
        self.__print(diagnosticOutput,'--> Compile a Linux Device Tree (.dts) file')
        if not singleFile:
            self.__print(diagnosticOutput,'    Looking for a .dts in the top folder')

        dts_file_name = None
        dts_file_dir = None 
        dts_file_found = False
        suffix_pos =0

        if singleFile:
            suffix_pos = searchPath.find('dts')
            if suffix_pos >=0:
                dts_file_name = searchPath
                dts_file_dir  = searchPath
        else:
            # Look for a .dts file in the top folder
            for file in os.listdir(searchPath):
                if os.path.isfile(searchPath+'/'+file):
                    suffix_pos = file.find('dts')
                    if suffix_pos >=0:
                        if dts_file_found:
                            raise Exception('More than one .dts file found!\n'+\
                                            'This feature is not supported')
                        self.__print(diagnosticOutput,'DTS File: '+file)
                        dts_file_name = file
                        dts_file_dir = searchPath+'/'+file
                        dts_file_found = True

        # Check if a dts file is found
        if dts_file_name == None:
            self.__print(diagnosticOutput,'NOTE: No Linux Devicetree '+\
                        '.dts file is found in the top folder!')
            return None

        outputfile = dts_file_name.replace('.dts','.dtb')
        if not singleFile:
            # Check that the output file is not already available
            for file in os.listdir(searchPath):
                if os.path.isfile(searchPath+'/'+file):
                    if file == outputfile:
                        self.__print(diagnosticOutput,'Remove the old output file'+file)
                        try:
                            os.remove(searchPath+'/'+file)
                        except Exception:
                            raise Exception('Failed to delete the old Linux device Tree file')

        # Compile the dts file 
        try:
            if singleFile:
                os.system('dtc -O dtb -o '+searchPath+' '+dts_file_name)
            else:
                os.system('dtc -O dtb -o '+searchPath+'/'+outputfile+' '+searchPath+'/'+dts_file_name)
    
        except subprocess.CalledProcessError:
            raise Exception('Failed to compile the Linux Devicetree file "'+dts_file_name+'"\n'+ \
                            'Is the Linux Device compiler "dtc" installed?')

        # Check that the Device Tree File exist!
        if not os.path.isfile(searchPath+'/'+outputfile):
            self.__print(diagnosticOutput,'ERROR: Compilation of the Linux Device Tree failed!')
            return None


        self.__print(diagnosticOutput,'--> Compilation of the Linux Device Tree file "'+\
                                    dts_file_name+'" done')
        self.__print(diagnosticOutput,'    Name of outputfile: "'+outputfile+'"')

        # Return the uncompiled file directory 
        return dts_file_dir

    def __compileubootscript(self,diagnosticOutput=True,searchPath =None):
        """
        Compile the u-boot script file "boot.script"

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * searchPath (str): Directory to search
        **Returns:**
            * File path of the compiled u-boot script file
        **Raises:**
            * *More than one "boot.script" file found! Only one is allowed!*
            * *No "boot.script" file is found in the top folder!*
            * *Failed to compile the u-boot script "boot.script"*
        """
        singleFile = len(os.listdir(searchPath)) == 0
        self.__print(diagnosticOutput,'--> Compile the u-boot script "boot.script"')
        if not singleFile:
            self.__print(diagnosticOutput,'    Looking for the "boot.script" file '+ \
                'in the top folder')

        ubootscr_file_dir = None 
        ubootscript_file_dir = None
        uboot_file_found = False

        if singleFile:
            pos = searchPath.find('boot.script')
            if pos ==-1:
                self.__print(diagnosticOutput,'NOTE: No "boot.script" was found '+ \
                'in the partition '+str(self.id))
            else:
                ubootscript_file_dir = searchPath
                ubootscr_file_dir = searchPath[:pos]+'boot.script'
                
        else:
            # Look for the "boot.script" file in the top folder
            for file in os.listdir(searchPath):
                if os.path.isfile(searchPath+'/'+file):
                    if file == 'boot.script':
                        if uboot_file_found:
                            raise Exception('More than one "boot.script" file found!\n'+\
                                            'Only one is allowed!')
                        self.__print(diagnosticOutput,'DTS File: '+file)
                        ubootscr_file_dir = searchPath+'/boot.scr'
                        ubootscript_file_dir = searchPath+'/'+file
                        uboot_file_found = True

        # Check if the "boot.script" is found
        if ubootscript_file_dir == None:
            self.__print(diagnosticOutput,'NOTE: No "boot.script" file '+\
                        'is found in the top folder!')
            return None

        if not singleFile:
            # Check that the output file is not already available
            for file in os.listdir(searchPath):
                if os.path.isfile(searchPath+'/'+file):
                    if file == 'boot.scr':
                        self.__print(diagnosticOutput,'Remove the old complied u-boot'+ \
                                ' script file: "'+file+'"')
                        try:
                            os.remove(searchPath+'/'+file)
                        except Exception:
                            raise Exception('Failed to delete the old complied u-boot script')

        comand = 'mkimage -A '+self.comp_ubootscript+' -O linux -T script -C none -a 0 -e 0'+ \
                 ' -n u-boot -d '+ubootscript_file_dir+' '+ubootscr_file_dir
 
        self.__print(diagnosticOutput,'--> Compile the u-boot script')
        try:
            os.system(comand)
        except Exception as ex:
            raise Exception('Failed to compile the u-boot script "boot.script"\n'+ \
                            'Are the u-boot tools installed?')
        
        if not os.path.isfile(ubootscr_file_dir):
            raise Exception('Failed to complie the u-boot script')
    
        self.__print(diagnosticOutput,'    = Done')

        # Return the uncompiled file directory 
        return ubootscript_file_dir
    
    def __uncompressArchivefiles(self,diagnosticOutput=True,searchPath =None):
        """
        Uncopress archive files if available

        Followed archive files are supported:
            * .tar.gz
            * .zip

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * searchPath (str): Directory to search
        **Returns:**
            * File path list of uncompressed archive files
        **Raises:**
            * *Failed to unzip the file "[arch]"*
        """

        singleFile = len(os.listdir(searchPath)) == 0
        self.__print(diagnosticOutput,'--> Uncompress Archive files')
        if not singleFile:
            self.__print(diagnosticOutput,'    Looking for archive files '+\
                    'inside the top folder')

        tar_files= []
        tar_gz_files =[]
        zip_files =[]
        searchPath_beforeZip =[]
        searchPath_afterZip =[]
        if singleFile:
            # Look for a archive file in the top folder
            if os.path.isfile(searchPath):
                if searchPath.find('.tar.gz') >0:
                    tar_gz_files.append(searchPath)
                elif searchPath.find('.tar') >0:
                    tar_files.append(searchPath)
                elif searchPath.find('.zip') >0:
                    zip_files.append(searchPath)
        else:
            # Look for a archive file in the top folder
            for file in os.listdir(searchPath):
                if os.path.isfile(searchPath+'/'+file):
                    if file.find('.tar.gz') >0:
                        tar_gz_files.append(searchPath+'/'+file)
                    elif file.find('.tar') >0:
                        tar_files.append(searchPath+'/'+file)
                    elif file.find('.zip') >0:
                        zip_files.append(searchPath+'/'+file)
        # Archive files for processing available ?
        if (not tar_files == None) or (not tar_gz_files == None) or (not zip_files == None):
            # List all files in the folder to notice the changes after the unziping
            if singleFile:
                searchPath_beforeZip.append(searchPath)
            else:
                searchPath_beforeZip = os.listdir(searchPath)

        # Progress all tar files 
        if not tar_files == None:
            self.__print(diagnosticOutput,'Process .tar files')
            for arch in tar_files:
                self.__print(diagnosticOutput,'Unzip the file:" '+arch+'"')
                try:
                    os.system('sudo tar --same-owner xhfv '+arch+' -C '+searchPath)
                except subprocess.CalledProcessError:
                    raise Exception('Failed to unzip the file "'+arch+'"\n')
                self.__print(diagnosticOutput,'   == Done')

        # Progress all tar.gz files 
        if not tar_gz_files == None:
            self.__print(diagnosticOutput,'Process .tar.gz files')
            for arch in tar_gz_files:
                self.__print(diagnosticOutput,'Unzip the file:" '+arch+'"')
                try:
                    os.system('sudo tar --same-owner -xzvpf '+arch+' -C '+searchPath) 
                except subprocess.CalledProcessError:
                    raise Exception('Failed to unzip the file "'+arch+'"\n')
                self.__print(diagnosticOutput,'   == Done')

        # Progress all zip files 
        if not zip_files == None:
            self.__print(diagnosticOutput,'Process .tar.gz files')
            for arch in zip_files:
                self.__print(diagnosticOutput,'Unzip the file:" '+arch+'"')
                try:
                    os.system('unzip '+arch+' -d '+searchPath)
                except subprocess.CalledProcessError:
                    raise Exception('Failed to unzip the file "'+arch+'"\n')
                self.__print(diagnosticOutput,'   == Done')
        
        # Archive files for processing available ?
        if (not tar_files == None) or (not tar_gz_files == None) or (not zip_files == None):
            # List all files in the folder to notice the changes after the unziping
            if singleFile:
                searchPath_afterZip.append(searchPath)
            else:
                searchPath_afterZip = os.listdir(searchPath)

        # Remove double files from the list
        for iteam in searchPath_afterZip:
            if not iteam in searchPath_beforeZip:
                self.__unzipedFiles.append(searchPath+'/'+iteam)

        # List the content off all unzip archive files 
        self.__print(diagnosticOutput,'    -- List of the content of all unzip files/folders --')
        for it in self.__unzipedFiles:
            self.__print(diagnosticOutput,'       '+it)

        self.__print(diagnosticOutput,'--> Uncompressing of all files is done')


        # Return the uncompiled file directories 
        return (tar_files+tar_gz_files+zip_files)
   


###################################################################

class BootImageCreator:
    """
    Class of the BootImage Creater
    """

    partitionTable=[]        
    """
    Partition list decoded from the XML file
    """

    outputFileName: str    
    """
    Name of the output image file with ".img" 
    """
    
    pathOfOutputImageDir: str   
    """
    File path of the output image file
    """

    totalImageSize : int        
    """
    Total image size of all partitions in byte 
    """

    totalImageSizeStr : str    
    """
    Total image size of all partitions as string (1MB,1GB)
    """
  
    __loopback_used = []   
    """
     list of used loopback devices 
    """

    __mounted_fs = []      
    """
    list of mounted loopback devices 
    """

    __imageFilepath : str  
    """
    Directory of the output file with name
    """

    __usedLoopback :  str  
    """
    Used loopback device 
    """

    extendedPartition = False 
    """
    Extended partition table needed?
    """

    def __init__(self, partitionTable=None,outputImageFileName=None,pathOfOutputImageDir=None):
        """
        Constructor of the BootImageCreator

        **Parameters:**
            * partitionTable (list): List of "Partition" class objects
            * outputImageFileName (str): Name of the output image file with the suffix ".img"
            * pathOfOutputImageDir (str): File path of the output image file
        **Returns:**
            *none*
        **Raises:**
            * *Partition No. 0 is not allowed; begin with 1*
            * *Run the methode "calculatePartitionFilesize()" before the constructor of "BootImageCreator"*
            * *No partition has files to copy to it*
            * *The partition number exists twice!*
            * *The selected output file path does not exist!*
            * *The name [outputImageFileName] can not be used as Linux file name!*
            * *The selected output file name has not the suffix ".img"!*
            * *The partition numbers are not in a row from [id1] to [id2]*
        """

        # Check that the partition number is only available once
        partitionTable_local = []
        id_list_local =[]

        for pat in partitionTable:
            if pat.id == 0: 
                raise Exception('Partition No. 0 is not allowed; begin with 1')
            if pat.totalSize == None:
                raise Exception('Run the methode "calculatePartitionFilesize()"'+\
                                'before the constructor of "BootImageCreator"')

        # Something to copy available ?
        temp_total_file=0
        for pat in partitionTable:
            temp_total_file =temp_total_file+ pat.totalFileSize
        if temp_total_file ==0:
            raise Exception('No partition has files to copy to it')

        for pat in partitionTable:
            for pat_loc in partitionTable_local:
                if pat_loc.id == pat.id:
                    raise Exception('The partition number '+str(pat.id)+' exists twice!')
            partitionTable_local.append(pat)
            id_list_local.append(pat.id)

        # Sort the table by the partition number 
        partitionTable_local = sorted(partitionTable_local, key=lambda x: x.id)
        id_list_local = sorted(id_list_local)

        # Check that the partition numbers are in a row 
        for i in range(0,len(id_list_local)-1):
            if not id_list_local[i]+1==id_list_local[i+1]:
                raise Exception('The partition numbers are not in a row from '+\
                    +str(id_list_local[i])+' to '+str(id_list_local[i+1]))

        self.partitionTable = partitionTable_local

        #Check that the path of file location exists
        if not os.path.isdir(pathOfOutputImageDir):
            raise Exception('The selected output file path does not exist!')

        self.pathOfOutputImageDir= pathOfOutputImageDir

        # Check that the name of output file is okay
        if not re.match("^[a-z0-9\\._]+$", outputImageFileName, re.I):
            raise Exception('The name '+str(outputImageFileName)+' can not be used as Linux file name!')
        
        if outputImageFileName.find(".img")==-1:
            raise Exception('The selected output file name has not the suffix ".img"!')

        self.outputFileName = outputImageFileName
        self.__imageFilepath = pathOfOutputImageDir + '/'+outputImageFileName 

        # Calculate the total image size
        self.totalImageSize =0
        for part in self.partitionTable:
            self.totalImageSize = self.totalImageSize + part.totalSize 

        # Increase the image size by 10MB to avoid issues
        # or increase the size by 2 times if the size is smaller than 1MB
        ######################################################################################
        if self.totalImageSize < 1_000_000:
            self.totalImageSize = self.totalImageSize+self.totalImageSize*2
        else:
            self.totalImageSize = self.totalImageSize+10_000_000
        #elif self.totalImageSize < 30_000_000:
        #    self.totalImageSize = self.totalImageSize+self.totalImageSize*0.5
        #elif self.totalImageSize < 60_000_000:
        #    self.totalImageSize = self.totalImageSize+self.totalImageSize*0.1
        #else:
        #    self.totalImageSize = self.totalImageSize+self.totalImageSize*0.01
        ######################################################################################
        
        self.totalImageSize = round(self.totalImageSize)
        self.totalImageSizeStr = self.__convert_byte2str(self.totalImageSize)

    def printPartitionTable(self):
        """
        Print the loaded partition table

        **Parameters:**
            *none*
        **Returns:**
            *none*
        **Raises:**
            *none*
        """

        print('-------------------------------------------------------------------')
        print('                    -- Partition Table -- ')
        if self.extendedPartition:
                print('     Extended Partition Mode')
        for item in self.partitionTable:
            print('                     --- Partition No. '+str(item.id)+' ---')
            if not item.extendedPartition:
                print('     Filesystem: '+ item.type+' |   Size: '+item.size_str)
                print('     Offset: '+item.offset_str)
                print('     File2copy: '+item.totalFileSizeStr+' | Total: '+item.totalSizeStr)
                if(item.totalFileSize ==0 or item.totalSize == 0):
                    print('     Filled: 0%')
                else:
                    print('     Filled: '+str(round((item.totalFileSize/item.totalSize)*100))+'%')
                print('        L--  Size: '+str(item.size)+'B | Offset: '+str(item.offset)+\
                    'B | Total: '+str(item.totalSize)+'B')
            else:
                print('     Extended Partition')
        
        print('-------------------------------------------------------------------')
        print('  Total Image size: '+self.totalImageSizeStr+'  '+str(self.totalImageSize)+'B')
        print('-------------------------------------------------------------------')
        print('  Image File Nameg1: "'+self.outputFileName+'"')
        print('-------------------------------------------------------------------')
  
    def generateImage(self, diagnosticOutput = True):
        """
        Generate a new Image file with the selected partitions

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
        **Returns:**
            *none*
        **Raises:**
            * *More than 4 partitions are available! --> Extended partition table needed*
        """
        self.__print(diagnosticOutput,'--> Start generating all partitions of the table')

        # Check if more then 4 partitions are available
        # --> Extended partition table needed
        if len(self.partitionTable) > 4:
            self.__print(diagnosticOutput,'WARNING: More than 4 partitions are available! --> Extended partition table needed')
            self.extendedPartition = True

            # insert a new parition to the table
            partitionTable_local = []
            i =1
            for pat in self.partitionTable:
                if i == 4:
                    partition = Partition(diagnosticOutput,4,'extended', '1M','0',False,False,'',0)
                    partitionTable_local.append(partition)
                
                if i< 4:
                    partitionTable_local.append(pat)
                else:
                    pat_local = pat
                    pat_local.id = i+1
                    partitionTable_local.append(pat_local)
                i = i+1

            # print the new table
            self.partitionTable = partitionTable_local
        # general or extended partition table mode

        # Step 2: Calculate partition offsets and sectors for all partitions of the table
        self._calculateTableSectores(diagnosticOutput)

        # Step 1: Create and mount a new image
        self.__createEmptyImage(diagnosticOutput)

        # Step 3: Create a loopback device 
        self.__createLoopbackDevice(diagnosticOutput,self.totalImageSize)

        # Step 4: Create the partition table with "fdisk"
        self.__createPartitonTable(diagnosticOutput, True)

        # Step 5: Clear and unmount the used loopback device
        #self.__delete_loopback(diagnosticOutput,self.__usedLoopback)

        # Step 6: Copy the files to the partition table
        for parts in self.partitionTable:
            if not parts.extendedPartition: 
                self.__prase_partition(diagnosticOutput,parts)

        # Step 7: Unmount and delate all open loopback devices 
        self.__unmountDeleteLoopbacks(diagnosticOutput)

    def compressOutput(self, diagnosticOutput=True,zipfileName=None):
        """
        Compress the output image file to ".zip" or ".tar.gz"

        Supported compress modes:
            * .zip
            * .tar.gz
        
        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * zipfileName (str): Path with name of the zip or tar.gz file
        **Returns:**
            *none*
        **Raises:**
            * *The compress mode is not supported - Only .zip and .tar.gz are allowed*
            * *The output image file does not exist*
            * *The zip file must be specified*
            * *Failed delete to old zip file MSG:[ex]*
            * *Failed to zip the image file MSG:[ex]*
            * *Remove the old zip file*
        """
        if zipfileName == None:
            raise Exception('The zip file must be specified')
        if not os.path.isfile(self.__imageFilepath):
            raise Exception('The output image file does not exist')
        
        compress_mode = ''
        if zipfileName.endswith('.zip'):
            compress_mode = 'zip'
        elif  zipfileName.endswith('.tar.gz'):
            compress_mode = 'tar.gz'
        else:
            raise Exception('The compress mode is not supported - Only .zip and .tar.gz are allowed')
       
        # delete the old zip file
        if os.path.isfile(zipfileName):
            self.__print(diagnosticOutput,'   Remove the old zip file ')
            try:
                os.remove(zipfileName)
            except Exception as ex:
                raise Exception('Failed delete to old zip file MSG:'+str(ex))

        # Compress the image file to ".zip"
        self.__print(diagnosticOutput,'--> Zip the image file with'+\
                                     ' the name "'+zipfileName+'"')
        if compress_mode == 'tar.gz':
            try:
                process = subprocess.Popen(["tar", "-czvf", zipfileName, self.outputFileName],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.communicate()
            except Exception as ex:
                raise Exception('Failed to zip the image file MSG:'+str(ex))
        elif compress_mode == 'zip':
            try:
                process = subprocess.Popen(["zip", zipfileName, self.outputFileName],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.communicate()
            except Exception as ex:
                raise Exception('Failed to zip the image file MSG:'+str(ex))
            self.__print(diagnosticOutput,'   == Done')

    def printFinalPartitionTable(self,diagnosticOutput=True):
        """
        Print the partition table of the final Image file with "fdisk"

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
        **Returns:**
            *none*
        **Raises:**
            * *The output image file does not exist*
        """
        self.__print(diagnosticOutput,' --> Print the partition table of'+\
             ' the final Image file with "fdisk"')
        if not os.path.isfile(self.__imageFilepath):
            raise Exception('The output image file does not exist')
        os.system('fdisk '+self.__imageFilepath+' -l')
        self.__print(diagnosticOutput,' ') 

    def __print(self,diagnosticOutput,str):
        """
        Debug Print

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * str (str): String to print
        **Returns:**
            *none*
        **Raises:**
            *none*
        """
        if diagnosticOutput:
            print(str)

    def __convert_byte2str(self, size_bytes):
        """
        Convert a byte size to a string format (1GB,1MB...)

        **Parameters:**
            * size_bytes (int): Byte value to convert
        **Returns:**
            * Size in string format
        **Raises:**
            *none*
        """
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "K", "M", "G", "T", "P", "E", "Z", "Y")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = math.ceil(size_bytes / p)
        s = round(s,0)
        s = int(s)
        ret = "%s %s" % (s, size_name[i])
        return ret.replace(" ","")

    def __runCmdInShell(self, diagnosticOutput = True,*popenargs, **kwargs):
        """
        Run a shell command and read the output

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * popenargs (list): command string list
            * kwargs (list): command argument string list
        **Returns:**
            * Output of the command as string
        **Raises:**
            * *Failed to execute the shell command "[cmd]"*
        """
        # Open a subprocess to run the command 

        #if diagnosticOutput:
        #    print('--> Execute the shell command "'+str(*popenargs)+'"')
        process = subprocess.Popen(stdout=subprocess.PIPE,
                                    *popenargs, **kwargs)
        # Read the shell output
        output, x = process.communicate()
        # Check that the execution was okay
        retcode = process.poll()
        if retcode:
            # Return code
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
                error = subprocess.CalledProcessError(retcode, cmd)
                error.output = output
            raise error
        #if diagnosticOutput:
        #    print(output)
        return output

    #
    #
    #
    # @brief delete a loopback device
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param device                 Linux Loopback device string 
    #
    def __delete_loopback(self,diagnosticOutput = True,device= None):
        """
        Delete a loopback device

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * device (str): Linux Loopback device string
        **Returns:**
            *none*
        **Raises:**
            * *Loopback device for deleting not specified*
            * *Failed to delete loopback device: [device]*
        """
        if(device == None):
            raise Exception('Loopback device for deleting not specified')

        self.__print(diagnosticOutput,'--> delete loopback device: '+str(device))

        try:
            self.__runCmdInShell(diagnosticOutput,["sudo","losetup", "-d", str(device)],
                                 stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise Exception('Failed to delete loopback device: '+str(device))

        self.__loopback_used.remove(device)
    
    def __unmountDeleteLoopbacks(self,diagnosticOutput = True):
        """
        Clean and unmount all open loopback devices
        
        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
        **Returns:**
            *none*
        **Raises:**
            * *Failed to unmount device:[dev]*
            * *Failed to delete device:[dev]*
        """
        self.__print(diagnosticOutput,'--> Unmount and clean all open devices')

        # 1. Step: Unmount all open loopback devices
        self.__print(diagnosticOutput,'  Unmount all open loopback devices')
        for dev in self.__mounted_fs:
            self.__print(diagnosticOutput,'unmount device: '+str(dev))

            if os.path.isdir(dev):
                try: 
                    p = subprocess.Popen(["sudo","umount", dev],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    p.wait()
                except Exception:
                    raise Exception('Failed to unmount device:'+str(dev))
                if p.returncode != 0:
                    raise Exception('Failed to unmount device:'+str(dev))
                self.__mounted_fs.remove(dev)
            else:
                self.__print(diagnosticOutput,'The device: '+str(dev)+' was not mounted')

        # 2. Step: delete all used loopback devices
        self.__print(diagnosticOutput,'--> delete all used loopback devices')
     
        for dev in self.__loopback_used: 
            self.__delete_loopback(diagnosticOutput,dev)

    def __createEmptyImage(self,diagnosticOutput = True):
        """
        Create and mount a new empty Linux image

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
        **Returns:**
            *none*
        **Raises:**
            * *Failed to create an empty Image file!*
        """
        # Check if the image file already exists
        if(os.path.isfile(self.__imageFilepath)):
            self.__print(diagnosticOutput,'--> Remove the old output file')
            try:
                os.remove(self.__imageFilepath)
            except OSError:
                raise Exception('Failed to remove the existing Image file!')
        # Create a new empty Linux image and mount it
        try:
            ret = self.__runCmdInShell(diagnosticOutput,["sudo", "dd", "if=/dev/zero", 
                                "of="+self.__imageFilepath,"bs=1",
                                 "count=0", "seek="+str(self.totalImageSize)],
                                stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise Exception('Failed to create an empty Image file!')


    def __createPartitonTable(self, diagnosticOutput = True, output2file=False):
        """
        Create the configured partition table with "fdisk"

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * output2file (bool): Write the console output of "fdisk" to a file
                * "fdisk_output.txt" on the current directory
        **Returns:**
            *none*
        **Raises:**
            * *Error during executing of "fdisk"*
            * *Invalid arguments during executing of "fdisk"*
            * *Could not reload the partition table from image*
        """
        # Step 1: Generate a loopback
        self.__print(diagnosticOutput,'--> Create Partition Table')

        #os.system('sudo kpartx -a -s '+str(self.__usedLoopback))
        
        if self.__usedLoopback == None:
            raise Exception("No loopback device exists for creating the partition table")

        # Start a new pipe with "fdisk"
        self.__print(diagnosticOutput,'   with loopback device: '+str(self.__usedLoopback))

        try:
           p = subprocess.Popen(["sudo","fdisk", self.__usedLoopback, "-u"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            self.__unmountDeleteLoopbacks(diagnosticOutput)
            raise Exception('Error during executing of "fdisk"')
        except ValueError:
            self.__unmountDeleteLoopbacks(diagnosticOutput)
            raise Exception('Invalid arguments during executing of "fdisk"')
        # device pipe is open -> fdisk command shell is open
        self.__print(diagnosticOutput,'   "fdisk" pipe is open')

        # Create a new empty MBR (DOS) partition table 
        cmd = str('o \n').encode('utf-8')
        p.stdin.write(cmd)

        # Configure every selected partition inside "fdisk"
        part_count = len(self.partitionTable)
        for i in range(0,part_count):
            parts =  self.partitionTable[i]
            # 1.Command: Create a new primary partition 
            #           With ID, First Sector and Block Size

            # n : add a new partition
            # p : Primary partition 
            #     Partition number 
            #     First Sector  
            #     Last  Sector : Block Size
            # Note: """ -> ENTER Key
            if self.extendedPartition and parts.id == 4:
                cmd = str("""\
                            n     
                            e
                        """+str(parts.startSector)+"""
                       
                        """).encode('utf-8')
            elif self.extendedPartition and parts.id > 4:
                cmd = str("""\
                            n     
                            
                    +"""+str(parts.BlockSectorSize)+"""
                """).encode('utf-8')
            else:
                cmd = str("""\
                            n     
                            p
                """+str(parts.id)+"""
                """+str(parts.startSector)+"""
                +"""+str(parts.BlockSectorSize)+"""
                """).encode('utf-8')

            # Write command
            p.stdin.write(cmd)

            # 2. Command: Select the Filesystem of the partition
            #
            # t:  Select the Filesystem 
            #     Partition number 
            #     Filesystem type as HEX value

            if parts.id == 1:
                # the first partition is not selected with the number
                cmd = str("""\
                t
                """+parts.type_hex+"""
                """).encode('utf-8')
                
                # Write command
                p.stdin.write(cmd)

            elif not (parts.id == 4 and self.extendedPartition):
                cmd = str("""\
                t
                """+str(parts.id)+"""
                """+str(parts.type_hex)+"""
                """).encode('utf-8')

                # Write command
                p.stdin.write(cmd)
            self.__print(diagnosticOutput,'    = done')

        # 3. Command: Write the settings to the loopback and leave "fdisk"
        #
        # w:  Write changes to the loopback device 
        # q:  Quite and leave "fdisk"
        self.__print(diagnosticOutput,'   Progess change with fdisk and leave')
 
        cmd = str('p \n').encode('utf-8')
        p.stdin.write(cmd)

        cmd = str('w \n').encode('utf-8')
        p.stdin.write(cmd)

        cmd = str('q \n \n').encode('utf-8')
        p.stdin.write(cmd)

        out, err = p.communicate()
        output_str = out.decode('utf-8')

        output_str = output_str.replace('Last sector,','\nLast sector,   ')
        output_str = output_str.replace('First sector,','\nFirst sector,   ')

        if output2file:
            # write the output of the fdisk command to a txt file
            with open(os.getcwd()+'/fdisk_output.txt', 'w') as f:
                f.write(output_str)

        
        self.__print(diagnosticOutput,'   fdisk work done')

        # sometimes the kernel does not reload the partition table
        if p.returncode != 0:
            try:
                self.__print(diagnosticOutput,'--> Check partition with partprobe')

                process = subprocess.Popen(['sudo', 'partprobe',self.__usedLoopback], 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
        
                if len(stdout) >1: 
                    self.__unmountDeleteLoopbacks(diagnosticOutput)
                    raise Exception("Could not reload the partition table from image")

            except subprocess.CalledProcessError:
                self.__unmountDeleteLoopbacks(diagnosticOutput)
                raise Exception("Could not reload the partition table from image")
            self.__print(diagnosticOutput,'    = Okay')

        process = subprocess.Popen(['sudo', 'partprobe',self.__usedLoopback, '-s'], 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        stdout, stderr = process.communicate()

        process = subprocess.Popen(['sudo', 'fdisk','-u=cylinders','-l', self.__usedLoopback], 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stdout = stdout.decode('utf-8')

        # Check if the partition table is okay
        if not "Device" in stdout or not "Type" in stdout:
            self.__unmountDeleteLoopbacks(diagnosticOutput)
            print("ERROR in the partition table: ")
            print(stdout)
            raise Exception("Failed to create the partition table: FDisk output is not okay\n Check the partition table and the total image offset.")

        err_not_all_pats = False
        for parts in self.partitionTable:
            if not self.__usedLoopback+'p'+str(parts.id) in stdout:
                print('Partition: '+str(parts.id)+' is not available in new partition table')
                err_not_all_pats = True
                break
        if err_not_all_pats:
            self.__unmountDeleteLoopbacks(diagnosticOutput)
            print("ERROR in the partition table: ")
            print(stdout)
            raise Exception("Failed to create the partition table: Not all partitions are available")

        self.__print(diagnosticOutput,'    = Okay')

    def __createLoopbackDevice(self, diagnosticOutput = True,size =0, offset_bytes = 0):
        """
        Create loopback device 

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * size (int): Total size of the loopback in byte
            * offset_bytes (int): Offset in byte of the loopback
        **Returns:**
            * Loopback device
        **Raises:**
            * *Failed to get a loopback device*
            * *Given loopback device is not in the right format: "[loop_dev_str]"*
            * *Failed to create loopback device*
        """
        self.__print(diagnosticOutput,'--> Create loopback device')

        # Calculate next 512 Byte sector size
        size_lb = size
        #size_lb = size +(512- (size % 512))
        #offset_bytes = offset_bytes + (512-(offset_bytes % 512))
        try:
            if offset_bytes != 0:
                loop_dev = self.__runCmdInShell(diagnosticOutput, 
                    ["sudo","losetup", "--show", "-f", "-o "+str(offset_bytes),"--sizelimit", str(size_lb),"--sector-size=512", self.__imageFilepath]) #"--partscan"
            else:
                loop_dev = self.__runCmdInShell(diagnosticOutput,
                            ["sudo","losetup","--show", "-f","--sizelimit", str(size_lb),"--sector-size=512", self.__imageFilepath])
        except subprocess.CalledProcessError:
            self.__unmountDeleteLoopbacks(diagnosticOutput)
            raise Exception("Failed to get a loopback device")
        
        # convert the loop device name as string
        loop_dev_str = str(loop_dev) 

        dev_pos = loop_dev_str.find('/dev')
        if dev_pos == -1:
            raise Exception('Given loopback device is not in the '+\
                'right format: "'+loop_dev_str)            
        
        loop_pos = loop_dev_str.find('/loop')
        if loop_pos == -1:
            raise Exception('Given loopback device is not in the '+\
                'right format: "'+loop_dev_str)      

        number_str = loop_dev_str[loop_pos+5:]
        # find digits length of the number
        digits =0
        for c in number_str:
            if re.search("^([0-9])$", c, re.I):
                digits = digits+1
            else:
                break

        if digits == 0:
            raise Exception('Given loopback device is not in '+\
                'the right format: "'+loop_dev_str)      
        
        number_str = loop_dev_str[loop_pos+5:loop_pos+5+digits]
        
        device = '/dev/loop'+number_str
        loop_name = 'loop'+number_str

        self.__loopback_used.append(device)
        
        self.__print(diagnosticOutput,'    Loopback device used:'+str(device))
        self.__print(diagnosticOutput,'Testing the loopback device')

        # Check if the loopback device is available and has the right size
        check_ret = self.__runCmdInShell(diagnosticOutput,["lsblk", "-b", "-o", "NAME,SIZE", device])
        check_ret = check_ret.decode('utf-8')
        #print(check_ret)

        if ("not a block device" in check_ret) or (not loop_name in check_ret):
            self.__unmountDeleteLoopbacks(diagnosticOutput)
            raise Exception('Failed to create loopback device: '+str(device))

        check_ret = check_ret.replace('NAME','')
        check_ret = check_ret.replace('SIZE','')
        check_ret = check_ret.replace(loop_name,'')
        check_ret = check_ret.replace(' ','')
        check_ret = check_ret.replace('\n','')
        check_ret = check_ret.replace('└─','')
        check_ret = check_ret.replace('p','')
        check_ret = check_ret.replace('\t','')

        if not check_ret.isdigit():
            self.__unmountDeleteLoopbacks(diagnosticOutput)
            self.__print(diagnosticOutput,'Error: Loopback device status is not okay')
            raise Exception('Failed to create loopback device: '+str(device))

        if int(check_ret) >0:
            self.__print(diagnosticOutput,'    = Okay')
        else:
            self.__unmountDeleteLoopbacks(diagnosticOutput)
            self.__print(diagnosticOutput,'Error: Loopback device size is not okay --> Size is 0')
            raise Exception('Failed to create loopback device: '+str(device))

        self.__usedLoopback = device
        return device
    
    def __delete_loopback(self,diagnosticOutput = True, device=None):
        """
        Delete a Linux Loopback device

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * device (str): Linux Loopback device string
        **Returns:**
            *none*
        **Raises:**
            * *Failed to delete loopback "[device]"*
        """

        self.__print(diagnosticOutput,'--> Remove the loopback "'+device+'"')
        try:
            self.__runCmdInShell(diagnosticOutput,["sudo","losetup", "-d", str(device)], stderr=subprocess.STDOUT)
        except Exception:
            raise Exception('Failed to delete loopback "'+ device+'"')

        self.__loopback_used.remove(device)

   
    def _calculateTableSectores(self, diagnosticOutput=True):
        """
        Calculate the partition table with sectors and blocks

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
        **Returns:**
            *none*
        **Raises:**
            * *none*
        """
        self.__print(diagnosticOutput,'--> Calculate partition blocks '+\
            'and sectors for the table ')
        offset       = 2048   #  Blocks of 512 bytes
        start_sector = 0
        block_size   = 0

        partitionTable_len = len(self.partitionTable)

        if self.extendedPartition:
            self.__print(diagnosticOutput,'   Extended partition table is needed')

            # Calculate the offset for the extended partition table
            ext_total_size =0
            for i in range(4,len(self.partitionTable)):
                part = self.partitionTable[i]
                ext_total_size = ext_total_size + part.totalSize
                #block_size =math.ceil(part.totalSize / 512 + ((part.totalSize % 512) != 0)*1)
                #block_size_ext = block_size_ext + block_size 
        else:
            self.__print(diagnosticOutput,'   Standard partition table is needed')
        
        for i in range(0,partitionTable_len):
            part = self.partitionTable[i]
            if not self.extendedPartition:
                # Use the last offset value as start sector  
                block_size   = math.ceil((part.totalSize / 512 + ((part.totalSize % 512) != 0)*1))
            else:
                if part.id < 4 or part.id > 4:
                    # Use the last offset value as start sector  
                    block_size = math.ceil((part.totalSize / 512 + ((part.totalSize % 512) != 0)*1))
                else:
                    # IF part.id == 4
                    part.setTotalSize(ext_total_size)
                    self.partitionTable[i].totalSize = part.totalSize
                    block_size = math.ceil((part.totalSize / 512 + ((part.totalSize % 512) != 0)*1))

            
            start_sector =math.ceil(offset)
            offset = offset + block_size + 1
            # it is handy to save the size in blocks, as this is what fdisk needs
            self.partitionTable[i].updateSectores(start_sector, block_size) 
        print('done')

    def __format_partition(self,diagnosticOutput, type_mkfs= None, loopdevice=""):
        """
        Format a partition with a filesystem and a open loopback

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * type_mkfs (str): Filesystem type in "mkfs"-format
            * loopdevice (str): Linux Loopback device string
        **Returns:**
            *none*
        **Raises:**
            *none*
        """
        self.__print(diagnosticOutput,'--> Format partition with: '+str(type_mkfs)+' and loopback: '+str(self.__usedLoopback))


        # For RAW partitions a filesystem is not needed
        if(type_mkfs == None):
            return

        cmd =""
        if(type_mkfs in "mkfs.vfat"):
            os.system('sudo mkfs.vfat -M 0xF8 -F 32 '+loopdevice)
        else:
            process = subprocess.Popen(["sudo", type_mkfs, loopdevice],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)     
       
            process.wait()
            out, err = process.communicate()
            output_str = out.decode('utf-8')
            #print(output_str)

        self.__print(diagnosticOutput,'   Execution is done')
     
    def __prase_partition(self,diagnosticOutput= True,partition=None):
        """
        Prase a partition with the selected filesystem

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * partition (Partition): partition object of the partition to prase
        **Returns:**
            *none*
        **Raises:**
           *none*
        """
        # Create a new loopback for the partition 
        self.__print(diagnosticOutput,'--> Prase partition with ID:'+str(partition.id))
        block_size = 0

        if partition.id > 4:
            offset_byte = 0
            block_size = partition.BlockSectorSize
        else:
            offset_byte = partition.startSector * 512

        # Convert offset from sectors to byte
        #self.__createLoopbackDevice(diagnosticOutput,partition.totalSize, offset_byte)

        # Loop Device for the partition
        loopdevice = self.__usedLoopback + 'p'+str(partition.id)

        # Format the partition 
        self.__print(diagnosticOutput,'--> Format partition with loopback: '+str(loopdevice))

        
        # Copy files to the partition
        self.__format_partition(diagnosticOutput, partition.type_mkfs, loopdevice)


        if not partition.extendedPartition:
            self.__copyFiles2partitison(diagnosticOutput,partition,loopdevice)


        # delete the loopback
        self.__unmount(diagnosticOutput,self.__usedLoopback)
        #self.__delete_loopback(diagnosticOutput,self.__usedLoopback)
        self.__print(diagnosticOutput,'   = Done')
 
    def __unmount(self,diagnosticOutput = True, mounting_point =None):
        """
        Unmount a mounting point

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * mounting_point (str): Linux file path of the mounting point
        **Returns:**
            *none*
        **Raises:**
            * *Failed to unmout the mounting point [mounting_point]*
            * *Failed to remove the old mounting point folder* 
        """
        self.__print(diagnosticOutput,'--> Unmount Partition with '+\
                    ' mounting point "'+str(mounting_point)+'"')
        if mounting_point == None:
            return
        if not os.path.isdir(mounting_point):
            return

        p = subprocess.Popen(["sudo", "umount", mounting_point],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        if p.returncode != 0:
            self.__unmountDeleteLoopbacks(diagnosticOutput)
            raise Exception('Failed to unmout the mounting point '+\
                            str(mounting_point))

        try:
            shutil.rmtree(mounting_point, ignore_errors=False) 
        except Exception:
            raise Exception('Failed to remove the old mounting point folder')
        self.__mounted_fs.remove(mounting_point)
 
    def __copyFiles2partitison(self,diagnosticOutput = True, partition = None, loopdevice =""):
        """
        Copy files to a partition

        **Parameters:**
            * diagnosticOutput (bool): Enable/Disable the console printout
            * partition (Partition): partition object of the partition to prase
            * loopdevice (str): Linux Loopback device string
        **Returns:**
            *none*
        **Raises:**
            * *Failed to copy file [file] to the partition*
            * *Failed to create the mounting point folder*
            * *Failed to mount the filesystem*
            * *Failed to copy the file "[file]" to the mounting point*
        """
        self.__print(diagnosticOutput,'--> Copy all files to the partition No.'+\
                                    str(partition.id))

        # Copy to a RAW partition 
        if partition.type_hex == 'a2': 
            # Go through every file of the partition
            offset_byte =0
            for file in partition.fileDirectories:
                self.__print(diagnosticOutput,'   Copy file:"'+file+'"')

                # Copy to a RAW partition 
                #os.system('sudo dd if='+file+' of='+self.__usedLoopback+" bs=1 seek="+str(offset_byte))
                process = subprocess.Popen(["sudo","dd", "if="+file, 
                                    "of="+loopdevice, "bs=1", "seek="+str(offset_byte)],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.wait()
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    self.__unmountDeleteLoopbacks(diagnosticOutput)
                    raise Exception('Failed to copy file '+str(file)+' to the partition')

                offset_byte = offset_byte + os.stat(file).st_size
            self.__print(diagnosticOutput,'   == Done')
        else:
        # Copy a VFAT/FAT partition

            #  1.Step: Mount the filesystem of the partition
            self.__print(diagnosticOutput,'--> Mount filesystem '+str(partition.type)+' to the partition')
            # Create folder to link to the mounting point 
            mounting_point = "/tmp/"+str(int(time.time()))+"_"+str(os.getpid())
            self.__print(diagnosticOutput,'   Create mounting point folder '+mounting_point)
            try:
                os.mkdir(mounting_point)
            except OSError:
                self.__unmountDeleteLoopbacks(diagnosticOutput)
                raise Exception('Failed to create the mounting point folder')
            
            #print("sudo mount -t "+str(partition.type)+" "+self.__usedLoopback+" "+mounting_point)
            #os.system("sudo mount -t "+str(partition.type)+" "+self.__usedLoopback+" "+mounting_point)
            p = subprocess.Popen(["sudo", "mount", "-t", str(partition.type), 
                        loopdevice, mounting_point], 
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.wait()
            if p.returncode != 0:
                self.__print(diagnosticOutput,'ERROR: Failed to create mounting point folder')
                self.__print(diagnosticOutput,'Partition type: '+str(partition.type))
                self.__unmountDeleteLoopbacks(diagnosticOutput)
                raise Exception('Failed to mount the filesystem')
            self.__mounted_fs.append(mounting_point)
            self.__print(diagnosticOutput,'   = done')

            # 2.Step: Copy the files to the folder
            for file in partition.fileDirectories:
                file2copy =""
                self.__print(diagnosticOutput,'   Copy file:"'+file+'"')

                if partition.type_hex == 'b':
                    # Copy to a VFAT/FAT partition
                    cp_opt = "-rt"
                else:
                    cp_opt = "-at"
                
                if os.path.isdir(file):
                    file2copy =file+"/"
                else:
                    file2copy = file
                # Copy the file to the mounting point 
                
                try:
                    process = subprocess.Popen(["sudo","cp", cp_opt, mounting_point ] +\
                                     glob.glob(file2copy), stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)

                    stdout, stderr = process.communicate()

                except Exception as ex:
                        self.__unmount(diagnosticOutput,mounting_point)
                        self.__unmountDeleteLoopbacks(diagnosticOutput)
                        raise Exception('Failed to copy the file "'+file+'" to the mounting point')
            self.__print(diagnosticOutput,'   == Done')
            

            # 3.Step: Unmount the mounting point
            self.__unmount(diagnosticOutput,mounting_point)


#   
#
#
############################################ Const ###########################################
#
#
#


default_blueprint_xml_file ='<?xml version="1.0" encoding = "UTF-8" ?>\n'+\
    '<!-- Linux Distribution Blueprint XML file -->\n'+\
    '<!-- Used by the Python script "LinuxDistro2Image.py" -->\n'+\
    '<!-- to create a custom Linux boot image file -->\n'+\
    '<!-- Description: -->\n'+\
    '<!-- item "partition" describes a partition on the final image file-->\n'+\
    '<!-- L "id"        => Partition number on the final image (1 is the lowest number) -->\n'+\
    '<!-- L "type"      => Filesystem type of partition  -->\n'+\
    '<!--   L       => ext[2-4], Linux, xfs, vfat, fat, none, raw, swap -->\n'+\
    '<!-- L "size"      => Partition size -->\n'+\
    '<!-- 	L	    => <no>: Byte, <no>K: Kilobyte, <no>M: Megabyte or <no>G: Gigabyte -->\n'+\
    '<!-- 	L	    => "*" dynamic file size => Size of the files2copy + offset  -->\n'+\
    '<!-- L "offset"    => in case a dynamic size is used the offset value is added to file size-->\n'+\
    '<!-- L "devicetree"=> compile the Linux Device (.dts) inside the partition if available (Top folder only)-->\n'+\
    '<!-- 	L 	    => Yes: Y or No: N -->\n'+\
    '<!-- L "unzip"     => Unzip a compressed file if available (Top folder only) -->\n'+\
    '<!-- 	L 	    => Yes: Y or No: N -->\n'+\
    '<!-- L "ubootscript"  => Compile the u-boot script file ("boot.script") -->\n'+\
    '<!-- 	L 	    => Yes, for the ARMv7A (32-bit) architecture ="arm" -->\n'+\
    '<!-- 	L 	    => Yes, for the ARMv8A (64-bit) architecture ="arm64" -->\n'+\
    '<!-- 	L 	    => No ="" -->\n'+\
    '<LinuxDistroBlueprint>\n'+\
    '<partition id="1" type="vfat" size="*" offset="500M" devicetree="Y" unzip="N" ubootscript="arm" />\n'+\
    '<partition id="2" type="ext3" size="*" offset="1M" devicetree="N" unzip="Y" ubootscript="" />\n'+\
    '<partition id="3" type="RAW" size="*" offset="20M"  devicetree="N" unzip="N" ubootscript="" />\n'+\
    '</LinuxDistroBlueprint>\n'
'''
Default XML Blueprint file
'''

############################################                                ############################################
############################################             MAIN               ############################################
############################################                                ############################################

if __name__ == '__main__':
    print('\n#############################################################################')
    print('#                                                                           #')
    print('#    ########   ######    ##    ##  #######   ######  ########  #######     #')        
    print('#    ##     ## ##    ##    ##  ##  ##     ## ##    ##    ##    ##     ##    #')          
    print('#    ##     ## ##           ####   ##     ## ##          ##    ##     ##    #')    
    print('#    ########   ######       ##    ##     ## ##          ##    ##     ##    #')   
    print('#    ##   ##         ##      ##    ##     ## ##          ##    ##     ##    #')  
    print('#    ##    ##  ##    ##      ##    ##     ## ##    ##    ##    ##     ##    #')    
    print('#    ##     ##  ######       ##     #######   ######     ##     #######     #') 
    print('#                                                                           #')
    print("#       AUTOMATIC SCRIPT TO COMBINE ALL FILES OF A EMBEDDED LINUX TO A      #")
    print("#                       BOOTABLE DISTRIBUTABLE IMAGE FILE                   #")
    print('#                                                                           #')
    print("#               by Robin Sebastian (https://github.com/robseb)              #")
    print('#                          Contact: git@robseb.de                           #')
    print("#                            Vers.: "+version+"                                    #")
    print('#                                                                           #')
    print('#############################################################################\n')

    ############################################ Runtime environment check ###########################################

    # Check proper Python Version
    if sys.version_info[0] < 3:
        print('ERROR: This script can not work with your Python Version!')
        print("Use Python 3.x for this script!")
        sys.exit()

    # Check that the Version runs on Linux
    if not sys.platform =='linux':
        print('ERROR: This script works only on Linux!')
        print("Please run this script on a Linux Computer!")
        sys.exit()

    ############################################ Create XML Blueprint file ###########################################
    
    if os.path.exists('DistroBlueprint.xml'):
        # Check that the DistroBlueprint XML file looks valid
        print('---> The Linux Distribution blueprint XML file exists')
    else:
        print(' ---> Creating a new Linux Distribution blueprint XML file')
        with open('DistroBlueprint.xml',"w") as f: 
            f.write(default_blueprint_xml_file)

        print('   Open the "DistroBlueprint.xml" with a text editor ')
        print('   to configure the partition table of Image file to create')

        _wait_ = input('Type anything to continue ... ')

    ############################################ Read the XML Blueprint file  ###########################################
    ####################################### & Process the settings of a partition   ####################################
    print('---> Read the XML blueprint file ')
    try:
        tree = ET.parse('DistroBlueprint.xml') 
        root = tree.getroot()
    except Exception as ex:
        print(' ERROR: Failed to prase DistroBlueprint.xml file!')
        print(' Msg.: '+str(ex))
        sys.exit()
    
    # Load the partition table of XML script 
    print('---> Load the items of XML file ')
    partitionList= []

    for part in root.iter('partition'):
        try:
            id = str(part.get('id'))
            type = str(part.get('type'))
            size = str(part.get('size'))
            offset = str(part.get('offset'))
            devicetree = str(part.get('devicetree'))
            unzip_str = str(part.get('unzip'))
            comp_ubootscr = str(part.get('ubootscript'))
        except Exception as ex:
            print(' ERROR: XML File decoding failed!')
            print(' Msg.: '+str(ex))
            sys.exit()

        comp_devicetree =False
        if devicetree == 'Y' or devicetree == 'y':
            comp_devicetree = True
        
        unzip =False
        if unzip_str == 'Y' or unzip_str == 'y':
            unzip = True

        try:
            partitionList.append(Partition(True,id,type,size,offset,comp_devicetree,unzip,comp_ubootscr))
        except Exception as ex:
            print(' ERROR: Partition data import failed!')
            print(' Msg.: '+str(ex))
            sys.exit()

    # Add a datecode to the output file names
    now = datetime.now()
    dt_string = now.strftime("%Y%m%d_%H%M")

    # Use the default name "LinuxDistro.img" as output file name
    outputfileName   = "LinuxDistro"+dt_string+".img"
    #outputZipFileName= "LinuxDistro"+dt_string+".tar.gz"
    outputZipFileName= "LinuxDistro"+dt_string+".zip"

    ####################################### Check if the partition folders are already available  #######################################

    # Generate working folder names for every partition
    working_folder_pat = []
    for part in partitionList:
        working_folder_pat.append(part.giveWorkingFolderName(True))

    image_folder_name = 'Image_partitions'
    create_new_folders = True

    # Check if the primary partition folder exists
    if os.path.isdir(image_folder_name):
        if not len(os.listdir(image_folder_name)) == 0:
            # Check that all partition folders exist
            for file in os.listdir(image_folder_name):
                if not file in working_folder_pat:
                    print('ERROR:  The existing "'+image_folder_name+'" Folder is not compatible with this configuration!')
                    print('        Please delete or rename the folder "'+image_folder_name+'" to allow the script')
                    print('         to generate a matching folder structure for your configuration')
                    sys.exit()  
            create_new_folders = False
    else: 
        try:
            os.makedirs(image_folder_name)
        except Exception as ex:
            print(' ERROR: Failed to create the image import folder on this directory!')
            print(' Msg.: '+str(ex))
            sys.exit()

###################################### Create new import folders for every partition   #######################################
    if create_new_folders:
        for folder in working_folder_pat:
            try:
                os.makedirs(image_folder_name+'/'+folder)
            except Exception as ex:
                print(' ERROR: Failed to create the partition import folder on this directory!')
                print(' Msg.: '+str(ex))
                sys.exit()
 
#################################  Allow the user to import files to the partition folders  ###################################
    print('\n#############################################################################')
    print('#    Copy files to the partition folders to allow the pre-installment         #')
    print('#                    to the depending image partition                         #')
    print('#                                                                             #')
    print('#                     === Folders for every partition ===                     #')
    for part in partitionList:
        print('# Folder: "'+image_folder_name+'/'+part.giveWorkingFolderName(False)+'"| No.: '+ \
                                str(part.id)+' Filesystem: '+part.type+' Size: '+str(part.size_str))
    print('#                                                                            #')
    print('##############################################################################')
    print('#                                                                            #')
    print('#                    Compress the output image file?                         #')
    print('#     Should the output file be compressed as .zip to reduce the size        #')
    print('#     Image creator tools like "Rufus" can directly work with .zip files     #')
    print('#                                                                            #')
    print('#        Y: Compress the output image as .zip                                #')
    print('#        Q: Quit the script                                                  #')
    print('#        Any other input: Do not compress the output image                   #')
    print('#                                                                            #')
    print('##############################################################################')
    _wait_ = input('#              Please type ...                                               #')
    if _wait_ == 'q' or _wait_ == 'Q':
        sys.exit()
    elif _wait_ =='Y' or _wait_ =='y':
        compress_output = True
    else:
        compress_output = False
    print('##############################################################################')

################################## Scan the partition folders to list all directories #######################################
    print('\n---> Scan every partition folder to find all file directories')
    print('      and calculate the total partition size')
    try:
        for part in partitionList:
            # List every file inside the folder
            part.findFileDirectories(True,os.getcwd()+'/'+image_folder_name+'/'+part.giveWorkingFolderName(False))
            # Calculate the total file size of the partition 
            part.calculatePartitionFilesize(True)
    except Exception as ex:
        print(' ERROR: Failed to calculate the total partition size')
        print(' Msg.: '+str(ex))
        sys.exit()


################################# Insert the partition table to the BootImageCreator ######################################
    print('---> Insert the partition list to the image generator') 
    try:
        bootImageCreator = BootImageCreator(partitionList,outputfileName,os.getcwd())
    except Exception as ex:
        print(' ERROR: Failed to load the items of the XML file')
        print(' Msg.: '+str(ex))
        sys.exit()

############################################# Print the partition table ###################################################
    print('-> Print the loaded Partition table')
    bootImageCreator.printPartitionTable()
    
    #print(' ...wait for 3 seconds to start the image generation ... ')
    #subprocess.call('read -t 3', shell=True)

    #_wait2_ = input('Start generating the image by typing anything to continue ... (q/Q for quite) ')
    #if _wait2_ == 'q' or _wait2_ == 'Q':
    #    sys.exit()


############################################# Create the new Image File ###################################################
    bootImageCreator.generateImage()

############################# Print the Partition table of the image file with "fdisk" #####################################
    bootImageCreator.printFinalPartitionTable()

    if compress_output:
        print('---> Compress the output image as .zip')
        bootImageCreator.compressOutput(True,outputZipFileName)


############################################################ Goodby screen  ###################################################
# EOF
