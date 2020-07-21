
![GitHub](https://img.shields.io/static/v1?label=Ubuntu&message=18.04+LTS,+20.04+LTS&color=yellowgreen)
![GitHub](https://img.shields.io/static/v1?label=CentOS&message=7.0,+8.0&color=blue)
![GitHub](https://img.shields.io/static/v1?label=Python&message=3.7&color=green)
![GitHub](https://img.shields.io/github/license/robseb/LinuxBootImageGenerator)
# Python Script to automatically generate a bootable Image file with a specifiable partition table for embedded Linux distributions

![Alt text](doc/Concept.png?raw=true "Concept illustration")

<br>

**This Python script can generate an bootable image file with Kernel-,bootloader- and user-files. Tools like ["*rufus*"](https://github.com/pbatard/rufus) can write for instance a SD-card to enable the booting of a Linux Distribution.**

The script can be used inside an other Python application or it can be executed as a console task. In the console mode is a simple *XML*-file used to describe the partition table of a final image file.
Then  the script generates folders depending on the image configuration. In the next step it is enabled for the user to copy files and folders to the partitions. These files will be added to the final image file. 
The script can automatically compile Linux device tree (*.dts*)-files, unzip archive files, like "*tar.gz*" or "*zip*", and can calculate the required partition size for the entire content.

Actually, I designed this script to expand the capabilities of my custom build system for my embedded Linux  [*rsyocto*](https://github.com/robseb/rsyocto) for *Intel* *SoC-FPGAs*.
However, I noticed that the flexibility of my script allows the usage for almost all embedded Linux platform for instants the *Raspberry Pi* or *NVIDIA Jatson*.

It is designed to run on modern Linux distributions. 
___

# Features

* **Boot image *(.img)* file generation for distributing embedded Linux Distributions**
* **Up to 4 freely configurable partitions**
* **Configurable partition size in *Byte*,*Kilobyte*,*Megabyte* or *Gigabyte***
* **File structure for each partition will be generated and user files can be added**
* **Partition file size check** 
* **Dynamic mode: Partition size = Size of the files to add to the partition**
* **An offset can be added to a dynamic size (*e.g. for user space on the running Linux*)**
* **Linux device tree (*dts*) -files inside a partition can be automatically compiled and replaced with the uncompiled file**  
* **Compressed files *(e.g. "tar.gz")* containing for instance the Linux *rootfs* can be unzip and automatically added to the partition**
* **Image Sizes, Block Sizes, Start Sectors for every partition will be automatically generated for the depending configuration**
* **The final image file can be compressed to a "*zip*-archive file to reduce the image size**

* **Supported Filesystems**
    * **ext2**
    * **ext3**
    * **ext4**
    * **Linux**
    * **vfat**
    * **fat**
    * **swap**
    * **RAW**
* **Supported archive file types, that can be unzipped automatically**
    * *.tar* **-Archives**
    * *.tar.gz* **-Archives**
    * *.zip* **-Archives**
* **Tested Development Environments**
    * **Ubuntu 18.04 LTS**
    * **Ubuntu 20.04 LTS**
    * **CentOS 7.7**
    * **CentOS 8.0**


# Getting started as a console application

For generating a bootable image by executing a single Linux command please follow this step-by-step guide:
    
* Clone this repository with the following Linux console command
    ````shell
    git clone https://github.com/robseb/LinuxBootImageFileGenerator.git
    ````
    * To install "*git*"
        * Ubuntu
            ````shell
            sudo apt-get install git 
            ````
        * CentOS
            ````shell
            sudo yum install git
            ````
* For compiling Linux Device tree files install the device tree compiler
    * Ubuntu
        ````shell
        sudo apt-get install device-tree-compiler
        ````
    * CentOS
        ````shell
        sudo yum install dtc
        ````
* Navigate into the repository folder
    ````shell 
    cd LinuxBootImageGenerator
* Start the Python script and follow the instructions
    ````shell
    python3 LinuxBootImageGenerator.py
    ````
    * Note: The execution with root (*"sudo"*) privileges is not necessary

## Major activities of the script in console mode

1. **Generation of a XML configuration file**
     
    The script will generate the **XML-file** "DistroBlueprint.xml" ('*LinuxBootImageGenerator/*'). It defines the blueprint of the final image `LinuxDistroBlueprint`.
    The `partition` object characterizes a partition on the final image. 
    A description of every attribute is available inside this file, as well.
     
    The following lines show the XML file of a partition configuration for *Intel* *SoC-FPGAs*.
    ````xml
    <?xml version="1.0" encoding = "UTF-8" ?>
    <!-- Linux Distribution Blueprint XML file -->
    <!-- Used by the Python script "LinuxDistro2Image.py -->
    <!-- to create a custom Linux boot image file -->
    <!-- Description: -->
    <!-- item "partition" Describes a partition on the final image file-->
    <!-- L "id"        => Partition number on the final image (1 is the lowest number) -->
    <!-- L "type"      => Filesystem type of partition  -->
    <!--   L       => ext[2-4], Linux, xfs, vfat, fat, none, raw, swap -->
    <!-- L "size"      => Partition size -->
    <!-- 	L	    => <no>: Byte, <no>K: Kilobyte, <no>M: Megabyte or <no>G: Gigabyte -->
    <!-- 	L	    => "*" dynamic file size => Size of the files2copy + offset  -->
    <!-- L "offset"    => in case a dynamic size is used the offset value is added to file size-->
    <!-- L "devicetree"=> compile the Linux Device (.dts) inside the partition if available (Top folder only)-->
    <!-- 	L 	    => Yes: Y or No: N -->
    <!-- L "unzip"     => Unzip a compressed file if available (Top folder only) -->
    <!-- 	L 	    => Yes: Y or No: N -->
    <LinuxDistroBlueprint>
    <partition id="1" type="vfat" size="*" offset="500M" devicetree="Y" unzip="N" />
    <partition id="2" type="ext3" size="*" offset="1M" devicetree="N" unzip="Y" />
    <partition id="3" type="RAW" size="*" offset="20M"  devicetree="N" unzip="N" />
    </LinuxDistroBlueprint>
    ````
    **Customize the XML file for your Linux distribution and platform.**

2. **Generation of a directory for every configured partition**

    The script will generate for every selected partition a depending folder. At this point it is enabled to drag&drop files and folders 
    to the partition folder. This content will then be included in the final image file. 
    Linux device tree- and archive-files, copied to the partition folder, will be automatically processed by the script incase these features were enabled for the partition inside the XML file. Of cause, archive files or uncompiled device tree files will not be added to the final image. 

    The following illustration shows generated folder structure with the previous XML configuration file.

    ![Alt text](doc/FolderStrucre.png?raw=true "Example of the folder structure")
    

    **Copy or drag&drop your files/folders to these partition folders to pre-install these content to the final image.**

    *Note: On RAW partitions are only files allowed!*

3. **Generation of the bootable image file with custom configuration**
    
    The script will generate a image file with name "*LinuxDistro.img*". Additionally, it is possible to generate a "*.zip*" archive file with the name "LinuxDistro.zip". Tools, like "*rufus*" can process this "*.zip*" file directly and can bring it onto a SD-Card. 
    <br>

# Getting started as Python library 

Beside the usage of this Python script as an console application it is enabled to use it inside a other Python application.
The "*LinuxBootImageGenerator*" consists of two Python classes:

| Class | Description
|:--|:--|
| **Partition**  | Descries a filesystem partition   |
| **BootImageCreator**  | The Linux Boot image generator |


The following steps describes in the right sequence the required Python methods to generate a image file:

1. **Generation of a XML configuration file**

    Configure the image partition by creating objects of the class **"Partition"**.
    Description of the construtor of the class *"Partition"*:
    ````python
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
    # @param operation_mode    File scan mode: 1= List every file | 0= List only top files and folders
    #  
    def __init__(self,diagnosticOutput=True, id=None, type=None,size_str=None,
                    offset_str=None,devicetree=False,unzip=False, operation_mode=0):
    ````

2. **Add folders/files to the partitions**
    
    To include directories and files to a partition are two methodes available. 
    To add every file inside in file path to the partition use following methode of the class *"Partition"*:
    
    ````python
    #
    # @brief Find files in a directory and add them to the file list
    #        These files will then be added to the partition 
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param searchPath             Directory to search
    #
    def findFileDirectories(self,diagnosticOutput=True,searchPath = None):
    ````
    By using a list of file- or folder directories to add to the partition use following methode of the class *"Partition"*:
    ````python
    #
    # @brief Import files to the file list
    #        These files will then be added to the partition 
    # @param diagnosticOutput       Enable/Disable the console printout
    # @param fileDirectories       List of File directories to import 
    #
    def importFileDirectories(self,diagnosticOutput,*fileDirectories):
    ````

3. **Calculate partition sizes**

    Use following methode of the class *"Partition"* to calculate the required sizes for the partition:
    
    ````python 
    # 
    #
    # @brief Calculate the total file size of all files to import to the partition 
    # @param diagnosticOutput       Enable/Disable the console printout
    #
    def calculatePartitionFilesize(self,diagnosticOutput=True):
    ````

4. **Create a BootImage Generator object**

    Use constructor of the "*BootImageCreator*" class to create a new object:
    
    ````python 
    #
    # @brief Constructor
    # @param partitionTable          partitionTable as list of "Partition" class objects 
    # @param outputFileName          Name of the output image file with the suffix ".img"
    # @param pathOfOutputImageDir    File path of the output image file 
    #  
    def __init__(self, partitionTable=None,outputFileName=None,pathOfOutputImageDir=None):
    ````
5. **Optional: Print the final partition table**

    Use following method of the class "*BootImageCreator*" to print all sizes of the partition table to generate: 
    
    ````python 
    #
    # @brief Print the loaded partition table 
    #
    def printPartitionTable(self):
    ````

6. **Generate the output image file**

    Use following method of the Python class "*BootImageCreator*" generate the final bootable image file:
    
    ````python
    #
    # @brief Generate a new Image file with the selected partitions
    # @param diagnosticOutput       Enable/Disable the console printout    
    #
    def generateImage(self, diagnosticOutput = True):
    ````

7. **Optional: Print the partition table inside the image file**

    To back check the image generating process it is possible with following method of the class "*BootImageCreator*" to print
    the partition table of generated image file: 
    
    ````python 
    #
    # @brief Print the final image partition with fdisk
    # @param diagnosticOutput       Enable/Disable the console printout    
    #  
    def printFinalPartitionTable(self,diagnosticOutput=True):
    ````

8. **Optional: Compress the generated image file**

    Use following method of the class "*BootImageCreator*" to zip the output image file:
    
    ````python 
    #
    # @brief Compress the output image file to ".zip"
    # @param diagnosticOutput       Enable/Disable the console printout    
    # @param zipfileName            Path with name of the zip file
    #  
    def compressOutput(self, diagnosticOutput=True,zipfileName=None):
    ````
<br>

    
    

# Author

**Robin Sebastian**

*LinuxBootImageGenerator* and [*rsyocto*](https://github.com/robseb/rsyocto) are projects, that I have fully developed on my own.
No companies are involved in this projects.
I’m recently graduated as a master in electrical engineering with the major embedded systems (*M. Sc.*).

I'm open for cooperations as a freelancer to realize your specific requirements.
Otherwise, I‘m looking for an interesting full time job offer to share and deepen my shown skills.

**[Github sponsoring is welcome.](https://github.com/sponsors/robseb)**

[![Gitter](https://badges.gitter.im/rsyocto/community.svg)](https://gitter.im/rsyocto/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![Email me!](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)](mailto:git@robseb.de)

[![GitHub stars](https://img.shields.io/github/stars/robseb/LinuxBootImageGenerator?style=social)](https://GitHub.com/robseb/LinuxBootImageGenerator/stargazers/)
[![GitHub watchers](https://img.shields.io/github/watchers/robseb/LinuxBootImageGenerator?style=social)](https://github.com/robseb/LinuxBootImageGenerator/watchers)
[![GitHub followers](https://img.shields.io/github/followers/robseb?style=social)](https://github.com/robseb)

