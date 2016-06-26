
# Juniper Networks vMX lwaftr Docker Container

The vmxlwaftr Docker Container contains everything thats required to successfully launch vMX 16.1 and newer images with a configuration file and license key. This document describes how that Container can be built from source. The actual vMX images is NOT part of the Container. It will be loaded from the official vMX tar file placed in the local directory from where the Container is launched.

## Build instructions

The Container vmxlwaftr is based on the official Ubuntu Docker 14.04.4 base Container and includes the following elements:

* Qemu 2.4.1 with reconnect patch downloaded and built from source in qemu/
* Snabb, downloaded and built from source in snabb/
* JET toolkit 16.1 (jet-1.tar.gz)
* JET application in the directory jetapp/

The build process requires a Docker Engine, ideally on a Linux based host. It is however possible to build it entirely on Docker for OS/X.

The individual steps are:

### 1. Build qemu

```
$ cd qemu
$ make
$ ls qemu-*tgz
qemu-v2.4.1-snabb.tgz
cd ..
```

This will clone branch v2.4.1-snabb from a private qemu repository, build the Docker Container *buildqemu* to compile and create a binary tar file for qemu into the current directory, from where it will be copied during the final step into the toplevel build directory by the top level Makefile.
In case the qemu must be cloned from a public qemu repository, its imperative to apply the patch qemu/qemu-snabb.diff to allow Snabb to re-connect to the VhostUser Socket after it terminated. The patch works also on v2.5.0 but needs adjustements for v2.6.0

### 2. Build Snabb

```
$ cd snabb
$ make
. . .
make[1]: Leaving directory `/build/src'
c18e43a1bbc434860275618d446c1eef  src/snabb
c18e43a1bbc434860275618d446c1eef  /u/src/snabb
cp build/src/snabb .
$ md5sum snabb
c18e43a1bbc434860275618d446c1eef  snabb
$ cd ..
```

This will clone the branch 1to1_mapping from a private Snabb repository, build the Docker Container *buildsnabb* to compile snabb and place it in the current directory. Snabb is a single application that will be placed in /usr/local/bin/ in the vmxlwaftr Docker Container further below.

### 3. Download JET Toolkit

The toplevel Makefile will automatically download the jet-1.tar.gz from Juniper's internal /volume/build/ folder for 16.1. This is a temporary solution until the toolkit can be downloaded from an external/public repository.

For a manual download, use:

```
scp svpod1-vmm.englab.juniper.net:/volume/build/junos/16.1/release/16.1R1.6/ship/jet-1.tar.gz .
```

### 4. Build the vmxlwaftr Container

Edit the name and version of the Container in the toplevel file VERSION:

```
$ cat VERSION
vmxlwaftr:v0.9
```

If the Container is to be pushed onto docker hub, then the name will probably be something like *juniper/vmxlwaftr:vx.y*

Run the toplevel Makefile to build the Container:

```
$ make
. . .
Step 15 : CMD -h
 ---> Running in f98dc81620c9
 ---> aa7e281472e4
Removing intermediate container f98dc81620c9
Successfully built aa7e281472e4

$ mwiget@st:~/vmxlwaftr$ docker images
REPOSITORY                       TAG                 IMAGE ID            CREATED             SIZE
vmxlwaftr                        v0.9                aa7e281472e4        13 minutes ago      431.4 MB
buildsnabb                       latest              d633187d8dfc        29 minutes ago      358.8 MB
buildqemu                        latest              5c8eace386ab        35 minutes ago      447.2 MB
. . .
```

The images buildsnabb and buildqemu can be removed via 'make clean' from the qemu, respectively snabb directory. Only the 'vmxlwaftr' Container is required.

### 5. Save vmxlwaftr Container to file

To save the vmxlwaftr Container into an image file use:

```
$ docker save -o vmxlwaftr-v0.9.img vmxlwaftr:v0.9
$ ls -l vmxlwaftr-v0.9.img
-rw------- 1 mwiget mwiget 447854592 Jun 26 18:54 vmxlwaftr-v0.9.img
```

## Running the vmxlwaftr Container

```
docker run --name <name> --rm -v \$PWD:/u:ro \\
   --privileged -i -t marcelwiget/vmxlwaftr[:version] \\
   -c <junos_config_file> -i identity [-l license_file]\\
   [-V <# of cores>] [-W <# of cores>] [-P <cores>] [-R <cores>] \\
   [-m <kbytes>] [-M <kBytes>] \\
   <image> <pci-address/core> [<pci-address/core> ...]

[:version]       Container version. Defaults to :latest

 -v \$PWD:/u:ro   Required to access a file in the current directory
                 docker is executed from (ro forces read-only access)
                 The file will be copied from this location

 <image>         vMX distribution tar file, e.g. vmx-bundle-16.1R1.6.tgz

 <pci-address/core> [<pci-address/core> ..]
                 One or more PCI addresses and physical core to lock
                 the Snabb process to. For simulation purposes use
                 'tap' instead of the pci-address. 

 -i  username,password for the JETapp to communicate with the Junos
     control plane. Must also be configured in the Junos config with
     super-user privileges

 -c  Junos configuration file

 -l  Junos license key file

 -m  Specify the amount of memory for the vRE/VCP (default $VCPMEM kB)
 -M  Specify the amount of memory for the vPFE/VFP (default $VFPMEM kB)

 -P  Cores to pin the VFP to via numactl --physcpubind <cores>
 -R  Cores to pin the VCP to via numactl --physcpubind <cores>
 
 -V  number of virtual cores to assign to VCP (default 1)
 -W  number of virtual cores to assign to VFP (default 3)

 -d  launch debug shell before launching vMX and before existing the container

```

See tests/run1.sh and tests/run2.sh for examples on how to launch. The 
vMX distribution tar file must be on the local directory from which the container
is launched.

