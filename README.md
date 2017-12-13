# NUCAPT Publication Manager
[![Build Status](https://travis-ci.org/materials-data-facility/nucapt.svg?branch=master)](https://travis-ci.org/materials-data-facility/nucapt)[![Coverage Status](https://coveralls.io/repos/github/materials-data-facility/nucapt/badge.svg?branch=master)](https://coveralls.io/github/materials-data-facility/nucapt?branch=master)
[![Documentation Status](https://readthedocs.org/projects/nucapt/badge/?version=latest)](http://nucapt.readthedocs.io/en/latest/?badge=latest)

The NUCAPT publication manager is designed to organize data produced by the Northwestern University Atom Probe
Tomography (NUCAPT) facility. The primary functions of this service are to create and maintain an organized filesystem,
and assist gathering metadata about each APT sample. Both of these functions will serve to make this data more
resuable and will simplify publication to the [Materials Data Facility](http://materialsdatafacility.org).

## Installation

First install the python package by calling:

```pip install -e .```

You will then need to get the client secret for this application from Logan Ward.

Once that is complete, call `python run_server.py` to start the service.

## Using NUCAPT Publication Manager

Documentation is available on [nucapt.readthedocs.io](http://nucapt.readthedocs.io/en/latest/)

## Support
This work was performed under financial assistance award 70NANB14H012 from U.S. Department of Commerce,
National Institute of Standards and Technology as part of the [Center for Hierarchical Material Design (CHiMaD)](http://chimad.northwestern.edu).
