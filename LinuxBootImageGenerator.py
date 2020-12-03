#!/usr/bin/env python
#
#            ########   ######     ##    ##  #######   ######  ########  #######                  
#            ##     ## ##    ##     ##  ##  ##     ## ##    ##    ##    ##     ##           
#            ##     ## ##            ####   ##     ## ##          ##    ##     ##        
#            ########   ######        ##    ##     ## ##          ##    ##     ##       
#            ##   ##         ##       ##    ##     ## ##          ##    ##     ##      
#            ##    ##  ##    ##       ##    ##     ## ##    ##    ##    ##     ##        
#            ##     ##  ######        ##     #######   ######     ##     #######         
#             ___          _   _      _     ___               _                 
#            | _ )  _  _  (_) | |  __| |   / __|  _  _   ___ | |_   ___   _ __  
#            | _ \ | || | | | | | / _` |   \__ \ | || | (_-< |  _| / -_) | '  \ 
#            |___/  \_,_| |_| |_| \__,_|   |___/  \_, | /__/  \__| \___| |_|_|_|
#                                                  |__/                              
#
#
# Robin Sebastian (https://github.com/robseb)
# Contact: git@robseb.de
# Repository: https://github.com/robseb/LinuxBootImageFileGenerator
#
# Python Script to automatically generate a  bootable Image file with
# a specifiable partition table for embedded Linux distributions

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

version = "1.07"

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

#
#
#
############################################ Const ###########################################
#
#
#
DELAY_MS = 3 # Delay after critical tasks in milliseconds 

# 
#
# @brief Class for discripting a filesystem partition 
#   
class Partition:
    scan_mode: int            # File scan mode: 1= List every file | 0= List only top files and folders
    id:   int                 # Number of Partition (O is the lowest)
    type: str                 # Partition Filesystem 
    type_hex: str             # Partition Filesystem as HEX value for "fdisk"
    type_mkfs: str            # Partition Filesystem as MKFS value for "mkfs."
    size_str: str             # Partition size as string with unit (KB,MB)
    size : int                # Partition size in Byte (0 => dynamic file size)
    offset_str: str           # Partition offset space  as string to a dynamic size 
    offset: int               # Partition offset space as byte to a dynamic size 
    fileDirectories =[]       # File directory of each file to be imported to the partition
    totalFileSize: int        # Total file size of the partition (Byte)
    totalFileSizeStr: str     # Total file size of the partition (string 1GB,1MB)

    totalSize:  str           # Total size of the partition (Byte)
    totalSizeStr:  str        # Total size of the partition (string 1GB, 1MB)
    
    comp_devicetree: bool     # Compile a Linux dts devicetree file if available
    comp_ubootscript: str     # Compile u-boot script "boot.script" for architecture "arm" or "arm64"
    unzip_file: bool          # unzip a compressed file if available 
    startSector: int          # Partition Start sector 
    BlockSectorSize: int      # Block size of the partition

    __filesImported:bool      # Indicates that files are imported to the list 
    __unzipedFiles =[]        # List of all unziped files/folder to remove in the deconstructor  
    __dtsFileDir: str         # Direcortry of the DTS file to remove from the partition
    __ubootscrFileDir: str    # Direcortry of the u-boot script file to remove from the partition
    __uncompressedFilesDir =[]# Direcortries of the uncompressed archive files

    #  
    # 
    #
    # @brief Constructor
    # @param diagnosticOutput  Enable/Disable the console printout
    # @param id                Partition Number of the partition table (1-4)
    # @param type              Filesystem name as string  "ext[2-4], Linux, xfs, vfat, fat, none, raw, swap"
    # @param size_str          Size of the partition as string 
    #                          Format: <no>: Byte, <no>K: Kilobyte, <no>M: Megabyte or <no>G: Gigabyte
    #                                  "*" dynamic file size => Size of the files2copy + offset
    # @param offset_str        In case a dynamic size is used the offset value is added to file size
    # @param devicetree        Compile the Linux Device (.dts) inside the partition if available 
    # @param unzip             Unzip a compressed file if available
    # @param ubootscript       Compile the u-boot script "boot.script" for architecture "arm" or "arm64"
    # @param operation_mode    File scan mode: 1= List every file | 0= List only top files and folders
    #  
    def __init__(self,diagnosticOutput=True, id=None, type=None,size_str=None,
                 offset_str=None,devicetree=False,unzip=False,ubootscript=None, operation_mode=0):
        
        # Convert the partition number to int 
        try:
            self.id = int(id)
        except ValueError:
            raise Exception('Failed to convert "id" to integer!') 
        
        # Check that the selected filesystem is supported 
        if not re.search("^(ext[2-4]|Linux|xfs|vfat|fat|none|raw|swap)$", type, re.I):
            raise Exception('Filesize "'+type+'" of "type" and id '+str(id)+' is unknown!')
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
            if not offset == '0': 
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

    #
    #
    #
    # @brief Deconstructor 
    #        Remove the content of all unziped files
    def __del__(self):
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

    #
    #
    #
    # @brief Import files to the file list
    #        These files will then be added to the partition 
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param fileDirectories       List of File directories to import 
    #
    def importFileDirectories(self,diagnosticOutput,*fileDirectories):
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

    #
    #
    #
    # @brief Find files in a directory and add them to the file list
    #        These files will then be added to the partition 
    #        Archive files will be unziped, devicetree files and u-boot
    #        scripts will be complied and the output will be added to the partition
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param searchPath             Directory to search
    # @param compileDevTreeUboot    Do complie the devicetree and a u-boot script
    # @param unzipArchive           Do unzip archvie files (such as the rootfs) 
    #
    def findFileDirectories(self,diagnosticOutput=True,searchPath = None, \
                            compileDevTreeUboot = True, unzipArchive=True):
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
    #
    #
    #     
    # @brief Update the Block and Sector sizes of the partition
    # @param startSector        start sector 
    # @param BlockSectorSize    block size
    #
    def updateSectores(self,startSector=0, BlockSectorSize=0):
        self.startSector = round(startSector)
        self.BlockSectorSize = round(BlockSectorSize)
    
    # 
    #
    # @brief Return a folder name for the partition for user file import
    # @param diagnosticOutput       Enable/Disable the console printout
    # @return                       working folder name
    #   
    def giveWorkingFolderName(self,diagnosticOutput=True):
        working_folder_pat ='Pat_'+str(self.id)+'_'+str(self.type)
        self.__print(diagnosticOutput,'--> Working folder name:"'+working_folder_pat+'"')
        return working_folder_pat
        
    # 
    #
    # @brief Calculate the total file size of all files to import to the partition 
    # @param diagnosticOutput       Enable/Disable the console printout
    #
    def calculatePartitionFilesize(self,diagnosticOutput=True):

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

    #####################################################################################################################

    #  
    # 
    #
    # @brief Debug Print 
    # @param diagnosticOutput       Enable/Disable the console printout
    def __print(self,diagnosticOutput,str):
        if diagnosticOutput:
            print(str)
    #
    #
    #
    # @brief Convert a byte size as string (1GB,1MB...)
    # @param size_bytes     Byte value to convert 
    # @retrun               Size in string format 
    #
    def __convert_byte2str(self, size_bytes):
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
    #
    #
    #
    # @brief Convert the size format to unsigned integer
    # @param size_value Size    value as String to convert 
    # @return                   size in byte
    #
    def __size2uint(self,size_value):
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

    # 
    #
    #
    # @brief Compile a Linux Device Tree file (dts) if available 
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param searchPath             Directory to search
    # @return                       File path of the compiled device tree file
    #  
    def __compileDeviceTree(self,diagnosticOutput=True,searchPath =None):
        
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

        outputfile = dts_file_name[:suffix_pos-3]+'.dtb'
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

        time.sleep(DELAY_MS)

        # Check that the Device Tree File exist!
        if not os.path.isfile(searchPath+'/'+outputfile):
            self.__print(diagnosticOutput,'ERROR: Compilation of the Linux Device Tree failed!')
            return None


        self.__print(diagnosticOutput,'--> Compilation of the Linux Device Tree file "'+\
                                    dts_file_name+'" done')
        self.__print(diagnosticOutput,'    Name of outputfile: "'+outputfile+'"')

        # Return the uncompiled file directory 
        return dts_file_dir

       # 
    #
    #
    # @brief Compile the u-boot script file "boot.script"
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param searchPath             Directory to search
    # @return                       File path of the compiled device tree file
    #  
    def __compileubootscript(self,diagnosticOutput=True,searchPath =None):
        
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

        time.sleep(DELAY_MS)

        if not os.path.isfile(ubootscr_file_dir):
            raise Exception('Failed to complie the u-boot script')
    
        self.__print(diagnosticOutput,'    = Done')

        # Return the uncompiled file directory 
        return ubootscript_file_dir
    
    # 
    #
    # @brief Uncompress archive files if available 
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param searchPath             Directory to search
    # @return                       File path list of uncompressed archive files 
    # 
    def __uncompressArchivefiles(self,diagnosticOutput=True,searchPath =None):

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

# 
#
# @brief Class of the BootImage Creater 
#  
class BootImageCreator:
    partitionTable=[]           # Partition list decoded from the XML file
    outputFileName: str    # Name of the output image file with ".img" 
    pathOfOutputImageDir: str   # Directory of the output file 
    totalImageSize : int        # Total image size of all partitions in byte 
    totalImageSizeStr : str     # Total image size of all partitions as string (1MB,1GB)
  
    __loopback_used = []   # list of used loopback devices 
    __mounted_fs = []      # list of mounted loopback devices 
    __imageFilepath : str  # Directory of the output file with name
    __usedLoopback :  str  # Used loopback device 


    #  
    # 
    #
    # @brief Constructor
    # @param partitionTable          partitionTable as list of "Partition" class objects 
    # @param outputImageFileName          Name of the output image file with the suffix ".img"
    # @param pathOfOutputImageDir    File path of the output image file 
    #  
    def __init__(self, partitionTable=None,outputImageFileName=None,pathOfOutputImageDir=None):
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

        if len(partitionTable) > 4:
            raise Exception('Not more than 4 partitions are allowed')

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
        if not re.match("^[a-z0-9\._]+$", outputImageFileName, re.I):
            raise Exception('The name '+str(outputImageFileName)+' can not be used as Linux file name!')
        
        if outputImageFileName.find(".img")==-1:
            raise Exception('The selected output file name has not the suffix ".img"!')

        self.outputFileName = outputImageFileName
        self.__imageFilepath = pathOfOutputImageDir + '/'+outputImageFileName 

        # Calculate the total image size
        self.totalImageSize =0
        for part in self.partitionTable:
            self.totalImageSize = self.totalImageSize + part.totalSize

        # Remove ".0" to avoid issues
        self.totalImageSize = round(self.totalImageSize)

        self.totalImageSizeStr = self.__convert_byte2str(self.totalImageSize)

    #
    #
    #
    # @brief Print the loaded partition table 
    #
    def printPartitionTable(self):
        print('-------------------------------------------------------------------')
        print('                    -- Partition Table -- ')
        for item in self.partitionTable:
            print('                     --- Partition No. '+str(item.id)+' ---')
            print('     Filesystem: '+ item.type+' |   Size: '+item.size_str)
            print('     Offset: '+item.offset_str)
            print('     File2copy: '+item.totalFileSizeStr+' | Total: '+item.totalSizeStr)
            if(item.totalFileSize ==0 or item.totalSize == 0):
                print('     Filled: 0%')
            else:
                print('     Filled: '+str(round((item.totalFileSize/item.totalSize)*100))+'%')
            print('        L--  Size: '+str(item.size)+'B | Offset: '+str(item.offset)+\
                'B | Total: '+str(item.totalSize)+'B')
        print('-------------------------------------------------------------------')
        print('  Total Image size: '+self.totalImageSizeStr+'  '+str(self.totalImageSize)+'B')
        print('-------------------------------------------------------------------')
        print('  Image File Name: "'+self.outputFileName+'"')
        print('-------------------------------------------------------------------')
    
    # 
    #
    #
    # @brief Generate a new Image file with the selected partitions
    # @param diagnosticOutput       Enable/Disable the console printout    
    #
    def generateImage(self, diagnosticOutput = True):
        self.__print(diagnosticOutput,'--> Start generating all partitions of the table')

        # Step 1: Create and mount a new image
        self.__createEmptyImage(diagnosticOutput)

        # Step 2: Create a loopback device 
        self.__createLoopbackDevice(diagnosticOutput,str(self.totalImageSize), 0)

        # Step 3: Calculate partition offsets and sectors for all partitions of the table
        self._calculateTableSectores(diagnosticOutput)

        # Step 4: Create the partition table with "fdisk"
        self.__createPartitonTable(diagnosticOutput)

        # Step 5: Clear and unmount the used loopback device
        self.__delete_loopback(diagnosticOutput,self.__usedLoopback)

        # Step 6: Copy the files to the partition table
        for parts in self.partitionTable:
            self.__print(diagnosticOutput,'  + Prase partition Number '+ str(parts.id))
            self.__prase_partition(diagnosticOutput,parts)

        # Step 7: Unmount and delate all open loopback devices 
        self.__unmountDeleteLoopbacks(diagnosticOutput)
    # 
    #
    #
    # @brief Compress the output image file to ".zip"
    # @param diagnosticOutput       Enable/Disable the console printout    
    # @param zipfileName            Path with name of the zip file
    #  
    def compressOutput(self, diagnosticOutput=True,zipfileName=None):
        if zipfileName == None:
            raise Exception('The zip file must be specified')
        if not os.path.isfile(self.__imageFilepath):
            raise Exception('The output image file does not exist')
       
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
        try:
            process = subprocess.Popen(["zip", zipfileName, self.outputFileName],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.communicate()
        except Exception as ex:
            raise Exception('Failed to zip the image file MSG:'+str(ex))
        self.__print(diagnosticOutput,'   == Done')

    # 
    #
    #
    # @brief Print the final image partition with fdisk
    # @param diagnosticOutput       Enable/Disable the console printout    
    #  
    def printFinalPartitionTable(self,diagnosticOutput=True):
        self.__print(diagnosticOutput,' --> Print the partition table of'+\
             ' the final Image file with "fdisk"')
        if not os.path.isfile(self.__imageFilepath):
            raise Exception('The output image file does not exist')
        os.system('fdisk '+self.__imageFilepath+' -l')
        self.__print(diagnosticOutput,' ') 

    #####################################################################################################################
    #  
    # 
    #
    # @brief Debug Print 
    # @param diagnosticOutput       Enable/Disable the console printout
    def __print(self,diagnosticOutput,str):
        if diagnosticOutput:
            print(str)

    #
    #
    #
    # @brief Convert a byte size as string (1GB,1MB...)
    # @param size_bytes  Byte value to convert 
    # @retrun               Size in string format 
    #
    def __convert_byte2str(self, size_bytes):
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

    #
    #
    #
    # @brief Run a shell command and read the output
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param popenargs              command string list
    # @param kwargs                 command argument string list
    # @return                       Output of the command as string 
    #
    def __runCmdInShell(self, diagnosticOutput = True,*popenargs, **kwargs):
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
        if(device == None):
            raise Exception('Loopback device for deleting not specified')

        self.__print(diagnosticOutput,'--> delete loopback device: '+str(device))

        try:
            self.__runCmdInShell(diagnosticOutput,["sudo","losetup", "-d", str(device)],
                                 stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise Exception('Failed to delete loopback device: '+str(device))

        self.__loopback_used.remove(device)
    
    #
    #
    #
    # @brief Clean and unmount all open loopback devices
    # @param diagnosticOutput       Enable/Disable the console printout
    # 
    def __unmountDeleteLoopbacks(self,diagnosticOutput = True):
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
                time.sleep(DELAY_MS)
            else:
                self.__print(diagnosticOutput,'The device: '+str(dev)+' was not mounted')

        # 2. Step: delete all used loopback devices
        self.__print(diagnosticOutput,'--> delete all used loopback devices')
     
        for dev in self.__loopback_used: 
            self.__delete_loopback(diagnosticOutput,dev)
    #
    #
    #
    # @brief Create and mount a new empty linux image
    # @param diagnosticOutput       Enable/Disable the console printout
    #
    def __createEmptyImage(self,diagnosticOutput = True):
        # Check if the image file already exists
        if(os.path.isfile(self.__imageFilepath)):
            self.__print(diagnosticOutput,'--> Remove the old output file')
            try:
                os.remove(self.__imageFilepath)
            except OSError:
                raise Exception('Failed to remove the existing Image file!')
        # Create a new empty Linux image and mount it
        try:
            self.__runCmdInShell(diagnosticOutput,["sudo", "dd", "if=/dev/zero", 
                                "of="+self.__imageFilepath,"bs=1",
                                 "count=0", "seek="+str(self.totalImageSize)],
                                stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise Exception('Failed to create an empty Image file!')

    #
    #
    #
    # @brief Create the configured partition table with "fdisk"
    # @param diagnosticOutput       Enable/Disable the console printout
    #
    def __createPartitonTable(self, diagnosticOutput = True):
        # Step 1: Generate a loopback
        self.__print(diagnosticOutput,'--> Create Partition Table')
        
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

        # Configure every selected partition inside "fdisk"
        part_count = len(self.partitionTable)
        for i in range(part_count):
            parts =  self.partitionTable[i]
            # 1.Command: Create a new primary partition 
            #           With ID, First Sector and Block Size

            # n : add a new partition
            # p : Primary partition 
            #     Partition number 
            #     First Sector  
            #     Last  Sector : Block Size
            # Note: """ -> ENTER Key
            
            if(i <part_count-1):
                cmd = str("""\
                            n     
                            p
                """+str(parts.id)+"""
                """+str(parts.startSector)+"""
                +"""+str(parts.BlockSectorSize)+"""
                """).encode('utf-8')
            else:
                cmd = str("""\
                            n     
                            p
                """+str(parts.id)+"""
                """+str(parts.startSector)+"""
                """+"""
                """).encode('utf-8')
            # Write command
            self.__print(diagnosticOutput,'   Create Partition No. '+\
                    str(parts.id)+' with fdisk')
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
            else:
                cmd = str("""\
                t
                """+str(parts.id)+"""
                """+str(parts.type_hex)+"""
                """).encode('utf-8')

            # Write command
            self.__print(diagnosticOutput,'   Write the Filesystem type: '\
                         +str(parts.type)+' HEX: '+str(parts.type_hex))
            p.stdin.write(cmd)
            time.sleep(DELAY_MS)
            self.__print(diagnosticOutput,'    = done')

        # 3. Command: Write the settings to the loopback and leave "fdisk"
        #
        # w:  Write changes to the loopback device 
        # q:  Quite and leave "fdisk"
        self.__print(diagnosticOutput,'   Progess change with fdisk and leave')

        cmd = str('w \n').encode('utf-8')
        p.stdin.write(cmd)
        time.sleep(DELAY_MS)
        cmd = str('o \n').encode('utf-8')
        p.stdin.write(cmd)
        cmd = str('q \n \n').encode('utf-8')
        p.stdin.write(cmd)

        p.communicate()
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

        #os.system("sudo fdisk "+self.__usedLoopback+' -l')

    #
    #
    #
    # @brief Create loopback device 
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param size                   Total size of the loopback in byte 
    # @param offset_bytes           Offset in byte of the loopback
    # @return                       loopback device
    #
    def __createLoopbackDevice(self, diagnosticOutput = True,size =0, offset_bytes = 0):
        self.__print(diagnosticOutput,'--> Create loopback device')
        # Calculate offset from sectors to byte
        try:
            if offset_bytes != 0:
                loop_dev = self.__runCmdInShell(diagnosticOutput,
                    ["sudo","losetup", "--show", "-f", "-o "+str(offset_bytes),
                    "--sizelimit",str(size), self.__imageFilepath])
            else:
                os.system('sudo losetup --show -f --sizelimit '+str(size)+' '+\
                            self.__imageFilepath)
                loop_dev = self.__runCmdInShell(diagnosticOutput,
                            ["sudo","losetup","--show", "-f",
                            "--sizelimit", str(size), self.__imageFilepath])
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

        loop_dev_str_clear = loop_dev_str[dev_pos:]
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

        self.__loopback_used.append(device)
        
        self.__print(diagnosticOutput,'    Loopback device used:'+str(device))
        self.__usedLoopback = device
        return device
    
    #
    #
    #
    # @brief delete a Linux Loopback device 
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param device                 Linux Looback device string
    #
    def __delete_loopback(self,diagnosticOutput = True, device=None):

        self.__print(diagnosticOutput,'--> Remove the loopback "'+device+'"')
        try:
            self.__runCmdInShell(diagnosticOutput,["sudo","losetup", "-d", str(device)], stderr=subprocess.STDOUT)
        except Exception:
            raise Exception('Failed to delete loopback "'+ device+'"')

        self.__loopback_used.remove(device)

    #
    #
    #
    # @brief Calculate partition offsets and sectors for all partitions of the table
    # @param diagnosticOutput       Enable/Disable the console printout
    #
    def _calculateTableSectores(self, diagnosticOutput=True):
        self.__print(diagnosticOutput,'--> Calculate partition blocks '+\
            'and sectors for the table ')
        offset = 2048   #  Blocks of 512 bytes
        start_sector =0
        block_size   =0
        for i in range(len(self.partitionTable)):
            part =self.partitionTable[i]
            # Use the last offset value as start sector  
            start_sector = offset
            block_size = ( part.totalSize / 512 + ((part.totalSize % 512) != 0)*1)
            block_size = math.ceil(block_size)
            start_sector =math.ceil(start_sector)
            #Calculate the start position for the next partition 
            offset = offset + block_size + 1
            #offset = block_size+1

            # it is handy to save the size in blocks, as this is what fdisk needs
            part.updateSectores(start_sector,block_size) 
            self.__print(diagnosticOutput,'   Pat.:'+str(part.id)+
                    ' Start: '+str(start_sector)+' Block size: '+str(block_size))

    #  
    #
    #
    # @brief Format a partition with a filesystem and a open loopback
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param type_mkfs              Filesystem type in "mkfs"-format            
    #
    def __format_partition(self,diagnosticOutput, type_mkfs= None):
        self.__print(diagnosticOutput,'--> Format partition with: '+str(type_mkfs))

        if(type_mkfs == None):
            return
        
        # Execute the Linux "mkfs." command 
        self.__print(diagnosticOutput,'   Execute Linux command '+str(type_mkfs))

        if(type_mkfs in "mkfs.vfat"):
            # Ubuntu requirers for mkfs.vfat -I
            process = subprocess.Popen(["sudo", type_mkfs, self.__usedLoopback ,'-F 32','-I'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            #os.system('sudo '+type_mkfs+' '+self.__usedLoopback)
            process = subprocess.Popen(["sudo", type_mkfs, self.__usedLoopback ],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)     
        '''
        time.sleep(DELAY_MS)
        if("mkfs.ext3" in type_mkfs):
            # Ubuntu Linux: Proceed anyway? (y,N) y -> Type Y to continue 
            b = str('y\n').encode('utf-8')
            process.stdin.write(b)     
        '''    
        time.sleep(DELAY_MS)

        # Read if a error occurs 
        process.wait()
        if process.returncode !=0: 
            self.__unmountDeleteLoopbacks(diagnosticOutput)
            raise Exception('Formating with '+str(TypeError)+' failed')

        self.__print(diagnosticOutput,'   Execution is done')
     
    # 
    #
    #
    # @brief Prase a partition 
    # @param diagnosticOutput       Enable/Disable the console printout    
    # @param partition               partition object of the partition to prase
    #  
    def __prase_partition(self,diagnosticOutput= True,partition=None ):
        # Create a new loopback for the partition 
        self.__print(diagnosticOutput,'--> Prase partition with ID:'+str(partition.id))
        # Convert offset from sectors to byte
        offset_byte = partition.startSector * 512
        self.__createLoopbackDevice(diagnosticOutput,partition.totalSize, offset_byte)
        
        # Format the partition 
        self.__print(diagnosticOutput,'--> Format partition')
        self.__format_partition(diagnosticOutput, partition.type_mkfs)

        # Copy files to the partition
        self.__copyFiles2partitison(diagnosticOutput,partition)
        time.sleep(DELAY_MS)

        # delete the loopback
        self.__unmount(diagnosticOutput,self.__usedLoopback)
        self.__delete_loopback(diagnosticOutput,self.__usedLoopback)
        self.__print(diagnosticOutput,'   = Done')

    # 
    # 
    #
    # @brief Unmount a mounting point
    # @param diagnosticOutput       Enable/Disable the console printout    
    # @param mounting_point         Linux file path of the mounting point
    #  
    def __unmount(self,diagnosticOutput = True, mounting_point =None):
        self.__print(diagnosticOutput,'--> Unmount Partition with '+\
                    ' mounting point "'+str(mounting_point)+'"')
        time.sleep(DELAY_MS)

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

    # 
    #
    #
    # @brief Copy files to a partition
    # @param diagnosticOutput       Enable/Disable the console printout    
    # @param partition               partition object of the partition to prase
    #  
    def __copyFiles2partitison(self,diagnosticOutput = True, partition = None):
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
                                    "of="+self.__usedLoopback, "bs=1", "seek="+str(offset_byte)],
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
                        self.__usedLoopback, mounting_point], 
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

#
# @brief default XML Blueprint file
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


############################################                                ############################################
############################################             MAIN               ############################################
############################################                                ############################################

if __name__ == '__main__':
    print('\n##############################################################################')
    print('#                                                                            #')
    print('#    ########   ######     ##    ##  #######   ######  ########  #######     #')        
    print('#    ##     ## ##    ##     ##  ##  ##     ## ##    ##    ##    ##     ##    #')          
    print('#    ##     ## ##            ####   ##     ## ##          ##    ##     ##    #')    
    print('#    ########   ######        ##    ##     ## ##          ##    ##     ##    #')   
    print('#    ##   ##         ##       ##    ##     ## ##          ##    ##     ##    #')  
    print('#    ##    ##  ##    ##       ##    ##     ## ##    ##    ##    ##     ##    #')    
    print('#    ##     ##  ######        ##     #######   ######     ##     #######     #') 
    print('#                                                                            #')
    print("#       AUTOMATIC SCRIPT TO COMBINE ALL FILES OF A EMBEDDED LINUX TO A       #")
    print("#                       BOOTABLE DISTRIBUTABLE IMAGE FILE                    #")
    print('#                                                                            #')
    print("#               by Robin Sebastian (https://github.com/robseb)               #")
    print('#                          Contact: git@robseb.de                            #')
    print("#                            Vers.: "+version+"                                     #")
    print('#                                                                            #')
    print('##############################################################################\n\n')

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

    _wait2_ = input('Start generating the image by typing anything to continue ... (q/Q for quite) ')
    if _wait2_ == 'q' or _wait2_ == 'Q':
        sys.exit()


############################################# Create the new Image File ###################################################
    bootImageCreator.generateImage()

############################# Print the Partition table of the image file with "fdisk" #####################################
    bootImageCreator.printFinalPartitionTable()

    if compress_output:
        print('---> Compress the output image as .zip')
        bootImageCreator.compressOutput(True,outputZipFileName)


############################################################ Goodby screen  ###################################################
    print('\n################################################################################')
    print('#                                                                              #')
    print('#                        GENERATION WAS SUCCESSFUL                             #')
    print('# -----------------------------------------------------------------------------#')
    print('#                     Output file:"'+image_folder_name+'"                     #')
    if compress_output:
        print('#                    Compressed Output file:"'+outputZipFileName+'"                  #')
    print('#                                                                              #')
    print('#                           SUPPORT THE AUTHOR                                 #')
    print('#                                                                              #')
    print('#                            ROBIN SEBASTIAN                                   #')
    print('#                     (https://github.com/robseb/)                             #')
    print('#                            git@robseb.de                                     #')
    print('#                                                                              #')
    print('#    LinuxBootImageGenerator and rsYocto are projects, that I have fully       #')
    print('#        developed on my own. No companies are involved in these projects.     #')
    print('#        I am recently graduated as Master of Since of electronic engineering  #')
    print('#                Please support me for further development                     #')
    print('#                                                                              #')
    print('################################################################################')
# EOF
