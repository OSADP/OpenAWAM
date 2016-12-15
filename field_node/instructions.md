================================
OpenAWAM Field Node Instructions
================================

The OpenAWAM field node software stack is based completely on open-source
software. The only piece that is not readily available from software
repositories is the *bluelog* program; but its source code is published,
and 

Hardware required to bench test field node:
-------------------------------------------
- Raspberry Pi
- SD card--4GB minimum, 8GB preferred
- Micro USB power cable--get the minimum length needed;
  longer cables cause voltage drops and unreliable operation
- USB power supply rated for 750 mA or greater (check against
  most current requirements for Raspberry Pi)
- Bluetooth adapter--use the one recommended for deployment if the
  bench-test equipment is planned for deployment

(Please refer to the complete field node parts list to assemble a PoE-capable
field node together with enclosure.)

Software:
---------
Obtain and install "Raspbian"--Debian for Raspberry Pi. 
(Other Linux distributions are available, e.g. Arch Linux; but as I am not
familiar with them, I cannot provide support.)

Get Raspbian installed and working before proceeding further. Instructions for
this are readily available from multiple sources including the Raspberry Pi
homepage, and the Raspbian project homepage.

Once you've booted the machine and logged in e.g. via SSH, you'll be asked to
configure the device. Normally the following should be done:

- Expand the filesystem to use the entire SD card.
- Change the password.
- Set timezone.
- Set locale. Default is Great Britain; U.S. users should instead use
  EN-US-UTF8.

Although it's not essential to set the timezone properly (all the central
software requires is that the clock be accurate relative to UTC--a goal that
is achieved by synchronizing with an NTP server), setting the timezone helps
ensure sane data is provided to the central software.

After finishing with the configurator:
--------------------------------------
Install ntpdate and ntp if they are not already installed (ntp is probably
  already there--but it doesn't hurt to make sure):

	$ sudo apt-get install ntpdate ntp

  These will work together to keep the Raspberry Pi's clock synced with 
  standard time sources, assuming the Pi can reach the Internet.

  If the Pi can't reach the Internet but there is a time source available on
  the local network, these programs can be configured to use the local time
  source instead. Please refer to the program documentation.

Install "bluez" package from repository:

	$ sudo apt-get install bluez

Bluez provides the Bluetooth stack needed by Bluelog to use the Bluetooth
adapter.

If Bluelog not already compiled for Raspberry Pi:
    - Install "libbluetooth-dev" package from repository 
    - Download current version of bluelog (currently at 1.1.0; under active
      development) from www.digifail.com or mirror site
    - Compile bluelog (run "make")

Install bluelog (copy executable to /usr/local/bin)
Edit /etc/rc.local to run bluelog as a daemon on startup. Sample line:
(place above "exit 0" in that file)
  
      (for logging to a local file)
      sudo -u pi /usr/local/bin/bluelog -dte -a 1 -o /home/pi/bluelog.log || exit 1

      (for logging over the network)
      sudo -u pi /usr/local/bin/bluelog -dtes -a 1 || exit 1

  (-e implies build of bluelog version dated February 2013 or later, which is
   why compiling from source is necessary.)

- If you will be using syslog to forward log messages, put this in /etc/rsyslog.conf:
  (replace WW.XX.YY.ZZ with wherever you want these messages to go--a computer
  that is available on the network, and is running the OpenAWAM server)

      # Use high-resolution timestamps for syslog messages forwarded over
      # the network
      $ActionForwardDefaultTemplate RSYSLOG_ForwardFormat

      # All user messages to be forwarded over UDP to comm server port 50101
      # (bluelog logs to facility user)
      user.*	@WW.XX.YY.ZZ:50101
      #     ^^^ [There is a TAB here]


----------------
Static Addresses
----------------

Use of static addresses, together with nonprovision of DHCP service, are a security
best practice for ITS since it makes it harder for an unauthorized user to determine
network resources and configuration. If you plan to deploy OpenAWAM units in the field,
consideration should be given to using static addresses.

Versions of Debian prior to Jessie
----------------------------------

If necessary, adjust /etc/network/interfaces to provide static IP address.
  Example:  
  
  #iface eth0 inet dhcp
  iface eth0 inet static
      address 192.168.1.10
      netmask 255.255.255.0
      gateway 192.168.1.1
  
  Also consider disabling any lines related to configuring a wireless adapter;
  those are added by default so that a wireless adapter can plug in and just
  work; if you're not going to use one then you don't need those lines.

If you are using a static address, then edit /etc/resolvconf.conf to have
this line in the appropriate location:
      name_servers=8.8.8.8
(And resolvconf will generate resolv.conf correctly to allow DNS resolution.)

Debian Jessie and Later
-----------------------

Debian Jessie uses dhcpcd to configure network resources by default. Therefore,
configuration of static addresses has changed. Add the following lines to the
file /etc/dhcpcd.conf:

interface eth0
static ip_address=192.168.0.10/24	
static routers=192.168.0.1
static domain_name_servers=192.168.0.1 8.8.8.8

Leave the file /etc/network/interfaces alone.

------------
Set Hostname
------------

A hostname is nothing more than a user-defined name for a computer on a
network.

Setting the hostname is important for proper operation of OpenAWAM, because
the hostname is tied to the location. Specifically, the hostname is included
in the syslog message forwarded to the central server, and the central server
matches the hostname to the location field of the nodes table when storing
the observation to the database.

It's suggested that hostname generation be standardized. The author uses
four characters for the north/south street, a dash, then four characters for
the east/west street. So, for example:

    elsw-ales
    fred-cact

Hostnames must only contain lowercase letters, dashes, and/or numbers.
Spaces and periods are specifically excluded. 

The following files need to be changed, if they exist:
  /etc/hostname
  /etc/hosts
  /etc/ssh/ssh/ssh_host_ecdsa_key.pub
  /etc/ssh/ssh/ssh_host_rsa_key.pub
  /etc/ssh/ssh/ssh_host_dsa_key.pub

Here is a script that can do it (adapted from http://wiki.debian.org/HowTo/ChangeHostname):

This script is meant to be run from the device. Run as root, and be sure to reboot afterward.
The script takes one parameter, which is the new hostname. If the default (or current)
hostname is not "raspberrypi", then edit the script to replace "raspberrypi" with the actual
hostname.

------------------------
  
#!/bin/bash
# 
usage() {
   echo "usage : $0 new_hostname"
   exit 1
}

[ -z $1 ] && usage

ancien="raspberrypi" # This is the default hostname; change if necessary
nouveau=$1

for file in \
   /etc/hostname \
   /etc/hosts \
   /etc/ssh/ssh_host_ecdsa_key.pub \
   /etc/ssh/ssh_host_rsa_key.pub \
   /etc/ssh/ssh_host_dsa_key.pub \
do
   [ -f $file ] && sed -i.old -e "s:$ancien:$nouveau:g" $file
done

----------------------

============================
Deploying the Field Node
============================

Consult the field node parts list for a suggested waterproof housing for the
field node, and for a Power over Ethernet injector/splitter. The OpenAWAM
white paper, also located on GitHub, has diagrams for installing to traffic
signal equipment. This file will be updated to provide additional installation
instructions based on user feedback.
