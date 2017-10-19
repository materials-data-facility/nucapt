.. NUCAPT-Publisher documentation master file, created by
   sphinx-quickstart on Thu Oct 19 15:52:53 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to NUCAPT-Publisher's documentation!
============================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

NUCAPT-Publisher is a tool designed to faciliate organizing and publishing Atom Probe Tomography (APT) datasets. 
This software creates a website that collects metadata about an APT sample, and organizes the data and metadata on a filesystem.
For completed datasets, NUCAPT-Publisher simplifies publishing the data to the `Materials Data Facility <http://materialsdatafacility.org>`_.



Using NUCAPT-Pub
----------------

TBD


Installation
------------

Install NUCAPT-Publisher by running:

    pip install -e .
	
This will collect all of the dependencies for the project, and install them as well.

Once installation is complete, you should configure the paths to where your data should be placed in ``manager.py``. By default, it places datasets in a folder in the installation directory.

After you have configured the tool, launch it by calling:

|	``start_flask`` if on Windows
|	``./start_flask.bs`` if on Linux (TBD, actualy)


Contribute
----------

- Issue Tracker: http://github.com/materials-data-facility/nucapt/issues
- Source Code: http://github.com/materials-data-facility/nucapt

Support
-------

If you are having issues, please let us know by posting issues on `GitHub <http://github.com/materials-data-facility/nucapt/issues>`_.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
