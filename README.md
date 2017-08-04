# NUCAPT Publication Manager
[![Build Status](https://travis-ci.org/materials-data-facility/nucapt.svg?branch=master)](https://travis-ci.org/materials-data-facility/nucapt)[![Coverage Status](https://coveralls.io/repos/github/materials-data-facility/nucapt/badge.svg?branch=master)](https://coveralls.io/github/materials-data-facility/nucapt?branch=master)

The NUCAPT publication manager is designed to organize data produced by the Northwestern Univeristy Atom Probe
Tomography facilty. The primary functions of this service is to create an maintain an organized filesystem, and
to gather metadata about each APT sample in a consistent format. Both of these functions will serve to make this data
more resuable and to simplify publication to the [Materials Data Facility](http://materialsdatafacility.org).

## Installation

To install and start this service, first install the python package by calling:

```pip install -e .```

Then, define the configuration for Flask by first setting the environmental variable, FLASK_APP, to `nucapt`.
For Linux, this command is:i `export FLASK_APP=nucapt`

For Windows, the environmental can be set variable using: `set FLASK_APP=nucapt`

Once the environment variable is set, run Flask by calling: `flask run`

## Using NUCAPT Publication Manager

Documentation TBD

## Support
This work was performed under financial assistance award 70NANB14H012 from U.S. Department of Commerce,
National Institute of Standards and Technology as part of the [Center for Hierarchical Material Design (CHiMaD)](http://chimad.northwestern.edu).
