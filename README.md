# OpenAWAM
Open Anonymous Wireless Address Matching Application 
README

OpenAWAM is an open-source project whose purpose is to allow logging and
analysis of anonymized Bluetooth addresses from multiple locations in
an area of interest (generally public streets or other public places).

OpenAWAM is divided into two components: The field component, and central.


=====================================
Field Component: OpenAWAM Field Nodes
=====================================

The field component consists of instructions to deploy inexpensive
address readers called "field nodes." The instructions assume a pre-existing
Ethernet data network, which the field nodes use to relay anonymized
addresses.

The field nodes run a standard Linux distribution on Raspberry Pi 
computers, or other hardware of the user's choice. The node runs
software freely available from other sources; therefore, the OpenAWAM
project provides field node assembly and configuration instructions.

Field nodes deployed using the OpenAWAM field node instructions cost about
$200 or less. In addition to the computer, the field nodes generally consist
of a Power over Ethernet injector/splitter pair, a Bluetooth USB adapter,
and a waterproof enclosure. A parts list is provided in this repository.

The field nodes require a 120VAC power source, and a Category 5 or better
TWP cable between the field node and the Ethernet switch. Power is carried
over the network cable.

The field node runs:

- Raspbian OS, a GNU/Linux operating system based on Debian
- Bluez, a standard package available from the Raspbian repository
  which provides Bluetooth services
- Bluelog, an open-source Bluetooth address logging program
- ntp and ntpdate, which work together to keep the node's clock
  synchronized with a time source

Bluelog is not available from the repositories but is an open-source
program. For convenience, the correct version of Bluelog (built from
the version of the source that includes the anonymization function),
compiled for the armhf architecture, is included in this repository.

In the standard OpenAWAM field node configuration, Bluelog is configured
to log Bluetooth address observations to syslog, and syslog is configured
to forward the observations (via UDP) to a user-defined location which runs
the OpenAWAM central software.


===============================
OpenAWAM Central Software
===============================

The central software runs on a computer of the user's choice, which can be
either Windows or Linux. The central software is developed in Python and
Javascript, and is designed to be cross-platform.

The central software is under active development. Currently envisioned are
the following components:

- A service that receives messages from field nodes and logs observations
  to a database of the user's choice. SQL Alchemy, a commonly used Python
  database extension, is used to provide support for multiple databases.
  OpenAWAM supports any database supported by SQL Alchemy. The OpenAWAM
  developers are currently using MySQL.

- A service that regularly interprets recent Bluetooth observations to
  provide link travel-time estimates.

- A tool that supports defining links for reporting purposes.

- A tool that allows the user to query the database to receive historical
  data for analyzing past travel patterns. Two applications planned include
  historical link speeds, and historical origin/destination data (useful
  to determine where observed devices are traveling within the network).

- Database maintenance scripts to purge old observations to avoid filling
  the disk where the database is stored.
  
==============================
CONTACT US
==============================

OpenAWAM is currently being developed by:

John Kerenyi                      Kali Fogel
City of Moreno Valley             Los Angeles County Metropolitan Transportation Authority
(951) 413-3199                    (213) 922-2665

Additional contact information can be found on the project's homepage:
https://github.com/OSADP/OpenAWAM
