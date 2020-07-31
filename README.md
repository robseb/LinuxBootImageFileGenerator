
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
    <partition id="1" type="vfat" size="*" offset="1M" devicetree="Y" unzip="N" />
    <partition id="2" type="ext3" size="*" offset="500M" devicetree="N" unzip="Y" />
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
    
    The script will generate a image file with name "*LinuxDistroYYYYMMDD_HHMM.img*". Additionally, it is possible to generate a "*.zip*" archive file with the name "LinuxDistro.zip". Tools, like "*rufus*" can process this "*.zip*" file directly and can bring it onto a SD-Card. 
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

## Link it to your repository for designing a custom build system

Use following commands inside your repository to link this Python library to your build system:

````bash
git submodule https://github.com/robseb/LinuxBootImageFileGenerator.git & git submodule update --init
````
<br>    

<br>
<details>
<summary><strong>Example output after an execution</strong></summary>
<a name="step5"></a>

````shell
vm@vm2:~/Desktop/LinuxBootImageFileGenerator$ python3 LinuxBootImageGenerator.py 

##############################################################################
#                                                                            #
#    ########   ######     ##    ##  #######   ######  ########  #######     #
#    ##     ## ##    ##     ##  ##  ##     ## ##    ##    ##    ##     ##    #
#    ##     ## ##            ####   ##     ## ##          ##    ##     ##    #
#    ########   ######        ##    ##     ## ##          ##    ##     ##    #
#    ##   ##         ##       ##    ##     ## ##          ##    ##     ##    #
#    ##    ##  ##    ##       ##    ##     ## ##    ##    ##    ##     ##    #
#    ##     ##  ######        ##     #######   ######     ##     #######     #
#                                                                            #
#       AUTOMATIC SCRIPT TO COMBINE ALL FILES OF A EMBEDDED LINUX TO A       #
#                       BOOTABLE DISTRIBUTABLE IMAGE FILE                    #
#                                                                            #
#               by Robin Sebastian (https://github.com/robseb)               #
#                          Contact: git@robseb.de                            #
#                            Vers.: 1.01                                     #
#                                                                            #
##############################################################################


---> The Linux Distribution blueprint XML file exists
---> Read the XML blueprint file 
---> Load the items of XML file 
--> Working folder name:"Pat_1_vfat"
--> Working folder name:"Pat_2_ext3"
--> Working folder name:"Pat_3_raw"

#############################################################################
#    Copy files to the partition folders to allow the pre-installment         #
#                    to the depending image partition                         #
#                                                                             #
#                     === Folders for every partition ===                     #
# Folder: "Image_partitions/Pat_1_vfat"| No.: 1 Filesystem: vfat Size: *
# Folder: "Image_partitions/Pat_2_ext3"| No.: 2 Filesystem: ext3 Size: *
# Folder: "Image_partitions/Pat_3_raw"| No.: 3 Filesystem: raw Size: *
#                                                                            #
##############################################################################
#                                                                            #
#                    Compress the output image file?                         #
#     Should the output file be compressed as .zip to reduce the size        #
#     Image creator tools like "Rufus" can directly work with .zip files     #
#                                                                            #
#        Y: Compress the output image as .zip                                #
#        Q: Quit the script                                                  #
#        Any other input: Do not compress the output image                   #
#                                                                            #
##############################################################################
#              Please type ...                                               #y
##############################################################################

---> Scan every partition folder to find all file directories
      and calculate the total partition size
--> Scan path "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat" to find a files inside it
--> Compile a Linux Device Tree (.dts) file
    Looking for a .dts in the top folder
DTS File: socfpga_cy5.dts
Remove the old output filesocfpga_cy5.dtb
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:86.20-92.5: Warning (simple_bus_reg): /soc/base-fpga-region: missing or empty reg/ranges property
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:770.10-789.5: Warning (simple_bus_reg): /soc/eccmgr: missing or empty reg/ranges property
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:873.13-877.5: Warning (simple_bus_reg): /soc/sdramedac: missing or empty reg/ranges property
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:994.10-999.5: Warning (simple_bus_reg): /soc/usbphy: missing or empty reg/ranges property
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:80.5-20: Warning (clocks_property): /soc/amba/pdma@ffe01000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:98.4-19: Warning (clocks_property): /soc/can@ffc00000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:107.4-19: Warning (clocks_property): /soc/can@ffc01000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:150.6-21: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/main_pll@40:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:157.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/main_pll@40/mpuclk@48:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:166.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/main_pll@40/mainclk@4c:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:175.7-26: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/main_pll@40/dbg_base_clk@50:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:175.7-26: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/main_pll@40/dbg_base_clk@50:clocks: cell 1 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:184.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/main_pll@40/main_qspi_clk@54:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:192.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/main_pll@40/main_nand_sdmmc_clk@58:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:200.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/main_pll@40/cfg_h2f_usr0_clk@5c:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:211.6-29: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/periph_pll@80:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:211.6-29: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/periph_pll@80:clocks: cell 1 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:211.6-29: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/periph_pll@80:clocks: cell 2 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:218.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/periph_pll@80/emac0_clk@88:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:226.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/periph_pll@80/emac1_clk@8c:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:234.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/periph_pll@80/per_qsi_clk@90:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:242.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/periph_pll@80/per_nand_mmc_clk@94:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:250.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/periph_pll@80/per_base_clk@98:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:258.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/periph_pll@80/h2f_usr1_clk@9c:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:269.6-29: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/sdram_pll@c0:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:269.6-29: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/sdram_pll@c0:clocks: cell 1 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:269.6-29: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/sdram_pll@c0:clocks: cell 2 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:276.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/sdram_pll@c0/ddr_dqs_clk@c8:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:284.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/sdram_pll@c0/ddr_2x_dqs_clk@cc:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:292.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/sdram_pll@c0/ddr_dq_clk@d0:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:300.7-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/sdram_pll@c0/h2f_usr2_clk@d4:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:309.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/mpu_periph_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:317.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/mpu_l2_ram_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:325.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/l4_main_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:333.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/l3_main_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:341.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/l3_mp_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:350.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/l3_sp_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:358.6-27: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/l4_mp_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:358.6-27: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/l4_mp_clk:clocks: cell 1 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:367.6-27: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/l4_sp_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:367.6-27: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/l4_sp_clk:clocks: cell 1 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:376.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/dbg_at_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:385.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/dbg_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:394.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/dbg_trace_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:403.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/dbg_timer_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:411.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/cfg_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:419.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/h2f_user0_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:427.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/emac_0_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:435.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/emac_1_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:443.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/usb_mp_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:452.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/spi_m_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:461.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/can0_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:470.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/can1_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:479.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/gpio_db_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:488.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/h2f_user1_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:496.6-31: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/sdmmc_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:496.6-31: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/sdmmc_clk:clocks: cell 1 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:496.6-31: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/sdmmc_clk:clocks: cell 2 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:505.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/sdmmc_clk_divided:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:514.6-31: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/nand_x_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:514.6-31: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/nand_x_clk:clocks: cell 1 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:514.6-31: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/nand_x_clk:clocks: cell 2 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:522.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/nand_ecc_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:530.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/nand_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:539.6-31: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/qspi_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:539.6-31: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/qspi_clk:clocks: cell 1 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:539.6-31: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/qspi_clk:clocks: cell 2 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:547.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/ddr_dqs_clk_gate:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:555.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/ddr_2x_dqs_clk_gate:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:563.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/ddr_dq_clk_gate:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:571.6-22: Warning (clocks_property): /soc/clkmgr@ffd04000/clocks/h2f_user2_clk:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:582.4-19: Warning (clocks_property): /soc/fpga_bridge@ff400000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:590.4-19: Warning (clocks_property): /soc/fpga_bridge@ff500000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:608.4-20: Warning (clocks_property): /soc/ethernet@ff700000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:627.4-20: Warning (clocks_property): /soc/ethernet@ff702000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:658.4-20: Warning (clocks_property): /soc/gpio@ff708000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:680.4-20: Warning (clocks_property): /soc/gpio@ff709000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:702.4-20: Warning (clocks_property): /soc/gpio@ff70a000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:725.4-20: Warning (clocks_property): /soc/i2c@ffc04000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:738.4-20: Warning (clocks_property): /soc/i2c@ffc05000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:751.4-20: Warning (clocks_property): /soc/i2c@ffc06000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:763.4-20: Warning (clocks_property): /soc/i2c@ffc07000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:822.4-25: Warning (clocks_property): /soc/dwmmc0@ff704000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:822.4-25: Warning (clocks_property): /soc/dwmmc0@ff704000:clocks: cell 1 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:841.4-30: Warning (clocks_property): /soc/nand@ff900000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:841.4-30: Warning (clocks_property): /soc/nand@ff900000:clocks: cell 1 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:841.4-30: Warning (clocks_property): /soc/nand@ff900000:clocks: cell 2 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:886.4-20: Warning (clocks_property): /soc/spi@fff00000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:905.4-20: Warning (clocks_property): /soc/spi@fff01000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:921.4-20: Warning (clocks_property): /soc/timer@fffec600:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:928.4-20: Warning (clocks_property): /soc/timer0@ffc08000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:939.4-20: Warning (clocks_property): /soc/timer1@ffc09000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:950.4-19: Warning (clocks_property): /soc/timer2@ffd00000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:961.4-19: Warning (clocks_property): /soc/timer3@ffd01000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:974.4-20: Warning (clocks_property): /soc/serial0@ffc02000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:987.4-20: Warning (clocks_property): /soc/serial1@ffc03000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:1005.4-20: Warning (clocks_property): /soc/usb@ffb00000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:1019.4-20: Warning (clocks_property): /soc/usb@ffb40000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:1033.4-19: Warning (clocks_property): /soc/watchdog@ffd02000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:1042.4-19: Warning (clocks_property): /soc/watchdog@ffd03000:clocks: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:975.4-33: Warning (dmas_property): /soc/serial0@ffc02000:dmas: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:975.4-33: Warning (dmas_property): /soc/serial0@ffc02000:dmas: cell 2 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:988.4-33: Warning (dmas_property): /soc/serial1@ffc03000:dmas: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:988.4-33: Warning (dmas_property): /soc/serial1@ffc03000:dmas: cell 2 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:1009.4-18: Warning (phys_property): /soc/usb@ffb00000:phys: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:1023.4-18: Warning (phys_property): /soc/usb@ffb40000:phys: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:581.4-25: Warning (resets_property): /soc/fpga_bridge@ff400000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:589.4-25: Warning (resets_property): /soc/fpga_bridge@ff500000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:610.4-25: Warning (resets_property): /soc/ethernet@ff700000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:629.4-25: Warning (resets_property): /soc/ethernet@ff702000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:724.4-25: Warning (resets_property): /soc/i2c@ffc04000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:737.4-25: Warning (resets_property): /soc/i2c@ffc05000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:750.4-25: Warning (resets_property): /soc/i2c@ffc06000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:762.4-25: Warning (resets_property): /soc/i2c@ffc07000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:930.4-25: Warning (resets_property): /soc/timer0@ffc08000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:941.4-25: Warning (resets_property): /soc/timer1@ffc09000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:952.4-25: Warning (resets_property): /soc/timer2@ffd00000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:963.4-25: Warning (resets_property): /soc/timer3@ffd01000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:1007.4-25: Warning (resets_property): /soc/usb@ffb00000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:1021.4-25: Warning (resets_property): /soc/usb@ffb40000:resets: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:1071.4-28: Warning (gpios_property): /leds/hps0:gpios: cell 0 is not a phandle reference
/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts:1081.4-28: Warning (gpios_property): /gpio-keys/reset:gpios: cell 0 is not a phandle reference
--> Compilation of the Linux Device Tree file "socfpga_cy5.dts" done
    Name of outputfile: "socfpga_cy5.dtb"
   Exclute the file "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dts" from the list
== File processing for the folder is done
Number of files: 4
--> Calculate the entire size of partition no.1
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/uboot_a10.scr
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/zImage
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dtb
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga.rbf
--> Scan path "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3" to find a files inside it
--> Uncompress Archive files
    Looking for archive files inside the top folder
Process .tar files
Process .tar.gz files
Unzip the file:" /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/rootfs.tar.gz"
Process .tar.gz files
--> Uncompressing of all files is done
   Exclute the archive file "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/rootfs.tar.gz" from the list
== File processing for the folder is done
Number of files: 15
--> Calculate the entire size of partition no.2
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/etc
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/etc"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/sys
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/sys"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/mnt
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/mnt"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/home
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/home"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/boot
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/boot"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/tmp
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/tmp"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/media
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/media"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/run
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/run"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/proc
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/proc"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/sbin
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/sbin"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/var
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/var"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/dev
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/dev"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/usr
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/usr"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/lib
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/lib"
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/bin
   Calculate folder size of folder "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/bin"
--> Scan path "/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_3_raw" to find a files inside it
== File processing for the folder is done
Number of files: 1
--> Calculate the entire size of partition no.3
   Read file size of: /home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_3_raw/u-boot-with-spl.sfp
---> Insert the partition list to the image generator
-> Print the loaded Partition table
-------------------------------------------------------------------
                    -- Partition Table -- 
                     --- Partition No. 1 ---
     Filesystem: vfat |   Size: *
     Offset: 1M
     File2copy: 15M | Total: 16M
     Filled: 94%
        L--  Size: 0B | Offset: 1048576B | Total: 16740940B
                     --- Partition No. 2 ---
     Filesystem: ext3 |   Size: *
     Offset: 500M
     File2copy: 761M | Total: 2G
     Filled: 60%
        L--  Size: 0B | Offset: 524288000B | Total: 1321369265B
                     --- Partition No. 3 ---
     Filesystem: raw |   Size: *
     Offset: 20M
     File2copy: 826K | Total: 21M
     Filled: 4%
        L--  Size: 0B | Offset: 20971520B | Total: 21817242B
-------------------------------------------------------------------
  Total Image size: 2G  1359927447B
-------------------------------------------------------------------
  Image File Name: "LinuxDistro20200723_1334.img"
-------------------------------------------------------------------
Start generating the image by typing anything to continue ... (q/Q for quite) 
--> Start generating all partitions of the table
[sudo] password for vm: 
--> Create loopback device
/dev/loop10
losetup: /home/vm/Desktop/LinuxBootImageFileGenerator/LinuxDistro20200723_1334.img: Warning: file does not fit into a 512-byte sector; the end of the file will be ignored.
losetup: /home/vm/Desktop/LinuxBootImageFileGenerator/LinuxDistro20200723_1334.img: Warning: file does not fit into a 512-byte sector; the end of the file will be ignored.
    Loopback device used:/dev/loop11
--> Calculate partition blocks and sectors for the table 
   Pat.:1 Start: 2048 Block size: 32699
   Pat.:2 Start: 34748 Block size: 2580801
   Pat.:3 Start: 2615550 Block size: 42613
--> Create Partition Table
   with loopback device: /dev/loop11
   "fdisk" pipe is open
   Create Partition No. 1 with fdisk
   Write the Filesystem type: vfat HEX: b
    = done
   Create Partition No. 2 with fdisk
   Write the Filesystem type: ext3 HEX: 83
    = done
   Create Partition No. 3 with fdisk
   Write the Filesystem type: raw HEX: a2
    = done
   Progess change with fdisk and leave
   fdisk work done
--> Check partition with partprobe
    = Okay
--> Remove the loopback "/dev/loop11"
  + Prase partition Number 1
--> Prase partition with ID:1
--> Create loopback device
losetup: /home/vm/Desktop/LinuxBootImageFileGenerator/LinuxDistro20200723_1334.img: Warning: file does not fit into a 512-byte sector; the end of the file will be ignored.
    Loopback device used:/dev/loop11
--> Format partition
--> Format partition with: mkfs.vfat
   Execute Linux command mkfs.vfat
   Execution is done
--> Copy all files to the partition No.1
--> Mount filesystem vfat to the partition
   Create mounting point folder /tmp/1595504084_32535
   = done
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/uboot_a10.scr"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/zImage"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga_cy5.dtb"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_1_vfat/socfpga.rbf"
   == Done
--> Unmount Partition with  mounting point "/tmp/1595504084_32535"
--> Remove the loopback "/dev/loop11"
   = Done
  + Prase partition Number 2
--> Prase partition with ID:2
--> Create loopback device
losetup: /home/vm/Desktop/LinuxBootImageFileGenerator/LinuxDistro20200723_1334.img: Warning: file does not fit into a 512-byte sector; the end of the file will be ignored.
    Loopback device used:/dev/loop11
--> Format partition
--> Format partition with: mkfs.ext3
   Execute Linux command mkfs.ext3
   Execution is done
--> Copy all files to the partition No.2
--> Mount filesystem ext3 to the partition
   Create mounting point folder /tmp/1595504093_32535
   = done
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/etc"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/sys"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/mnt"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/home"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/boot"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/tmp"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/media"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/run"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/proc"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/sbin"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/var"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/dev"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/usr"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/lib"
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_2_ext3/bin"
   == Done
--> Unmount Partition with  mounting point "/tmp/1595504093_32535"
--> Remove the loopback "/dev/loop11"
   = Done
  + Prase partition Number 3
--> Prase partition with ID:3
--> Create loopback device
losetup: /home/vm/Desktop/LinuxBootImageFileGenerator/LinuxDistro20200723_1334.img: Warning: file does not fit into a 512-byte sector; the end of the file will be ignored.
    Loopback device used:/dev/loop11
--> Format partition
--> Format partition with: None
--> Copy all files to the partition No.3
   Copy file:"/home/vm/Desktop/LinuxBootImageFileGenerator/Image_partitions/Pat_3_raw/u-boot-with-spl.sfp"
   == Done
--> Remove the loopback "/dev/loop11"
   = Done
 --> Print the partition table of the final Image file with "fdisk"
Disk /home/vm/Desktop/LinuxBootImageFileGenerator/LinuxDistro20200723_1334.img: 1,27 GiB, 1359927296 bytes, 2656108 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: dos
Disk identifier: 0xacdf836b

Device                                                                     Boot   Start     End Sectors  Size Id Type
/home/vm/Desktop/LinuxBootImageFileGenerator/LinuxDistro20200723_1334.img1         2048   34747   32700   16M  b W95 
/home/vm/Desktop/LinuxBootImageFileGenerator/LinuxDistro20200723_1334.img2        34748 2615549 2580802  1,2G 83 Linu
/home/vm/Desktop/LinuxBootImageFileGenerator/LinuxDistro20200723_1334.img3      2615550 2656107   40558 19,8M a2 unkn
 
---> Compress the output image as .zip
--> Zip the image file with the name "LinuxDistro20200723_1334.zip"
   == Done

################################################################################
#                                                                              #
#                        GENERATION WAS SUCCESSFUL                             #
# -----------------------------------------------------------------------------#
#                     Output file:"Image_partitions"                     #
#                    Compressed Output file:"LinuxDistro20200723_1334.zip"                  #
#                                                                              #
#                           SUPPORT THE AUTHOR                                 #
#                                                                              #
#                            ROBIN SEBASTIAN                                   #
#                     (https://github.com/robseb/)                             #
#                            git@robseb.de                                     #
#                                                                              #
#    LinuxBootImageGenerator and rsYocto are projects, that I have fully       #
#        developed on my own. No companies are involved in these projects.     #
#        I am recently graduated as Master of Since of electronic engineering  #
#                Please support me for further development                     #
#                                                                              #
################################################################################

````
</details>

<br>
<br>

___

    

# Author

**Robin Sebastian**

*LinuxBootImageGenerator* and [*rsyocto*](https://github.com/robseb/rsyocto) are Projects, that I have fully developed on my own.
No companies are involved in these projects.
I’m recently graduated as a master in electrical engineering with the major embedded systems (*M. Sc.*).

I'm open for cooperations as a freelancer to realize your specific requirements.
Otherwise, I‘m looking for an interesting full time job offer to share and deepen my shown skills.

**[Github sponsoring is welcome.](https://github.com/sponsors/robseb)**

[![Gitter](https://badges.gitter.im/rsyocto/community.svg)](https://gitter.im/rsyocto/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![Email me!](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)](mailto:git@robseb.de)

[![GitHub stars](https://img.shields.io/github/stars/robseb/LinuxBootImageGenerator?style=social)](https://GitHub.com/robseb/LinuxBootImageGenerator/stargazers/)
[![GitHub watchers](https://img.shields.io/github/watchers/robseb/LinuxBootImageGenerator?style=social)](https://github.com/robseb/LinuxBootImageGenerator/watchers)
[![GitHub followers](https://img.shields.io/github/followers/robseb?style=social)](https://github.com/robseb)

