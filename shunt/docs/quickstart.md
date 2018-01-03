# Requirements
- packer (https://www.packer.io/downloads.html)
- python (3.6 or greater)
- VirtualBox (5.1.30 the 5.2.X crashes my machine , https://www.virtualbox.org/wiki/Download_Old_Builds_5_1)
- Ubuntu Server 64-bit 16.04.3 LTS (https://www.ubuntu.com/download/server/thank-you?version=16.04.3&architecture=amd64)


## Steps for requirements

- install requirements
- open virtualbox and create a new controller machine with the following specs:
  - 64-bit Ubuntu
  - 512 MB RAM
  - Create New Harddisk with VDI type
  - Dynamically Allocated disk
  - 10 GB max size
- Setup and provision the controller machine (virtualbox created above)
  - Set the cd to be the ubuntu iso and start the machine
  - install ubuntu
- Export the machine (VirtualBox File->Export Appliance)
  - Make sure it's OVF 2.0

# Create a new Project

