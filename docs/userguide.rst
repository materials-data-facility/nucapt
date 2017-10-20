User Guide for NUCAPT Web Interface
===================================

This part of the documentation explains how to create, edit, and publish datasets using the web interface.

To start using this guide, you will first need to log on to the server running the publication service and find where APT data is stored at NUCAPT.
A bookmark to the webpage and a link to the data folders should be available on the desktop of your workstation.

Definitions
-----------

*Dataset*: A collection of the data and metadata from the same research study, which may include multiple samples

*Sample*: Data from a single APT data experiment, may include multiple reconstructions

*Reconstruction*: 3D data describing the atomic-scale structure of a material

Part 1: Creating a New Dataset
------------------------------

First, log on to the NUCAPT data service. You should see a greeting page similar to this:

.. figure :: _static/homepage.png
	:width: 100%
	
	Homepage for NUCAPT publication manager

To create a new dataset: Click "Create New Dataset," which will open a page prompting you for a title, abstract, and authorship information:

.. figure :: _static/dataset_creation.png
	:width: 100%
	
	Form for creating a new dataset

Once you submit this form, the web service will create you a new folder on the NUCAPT file storage system with an automatically-generated name.
This folder contains a single file ``GeneralMetadata.yaml`` that contains all of the information you just input in the form.
The web server will then read this file and generate a webpage describing your dataset.
At this point, you should be on a page with your dataset name and the location of this dataset on the web server.

.. figure :: _static/dataset_page.png
	:width: 100%
	
	Home page for a dataset
	
You can get back to this page later by either returning to the current URL, or through the "list datasets" page on the home screen.
At this point, you should familiarize yourself with the data set list. 
Click on the "NUCAPT Pub" link on the top left of the page, which brings you back to the home page. 
Then, click "List Current Datasets" to see all of the currently-active datasets.

.. figure :: _static/dataset_list.png
	:width: 100%
	
	Webpage showing active datasets
	
Part 2: Adding a Sample and Reconstruction to a Dataset
-------------------------------------------------------

At this point in the tutorial, you should have already created a dataset. 
The next step is to add an APT sample to that data. 
First, go to the dataset homepage and then click "Add Sample."
This will bring up a form for a description of this sample, measurement conditions, and the RHIT file from your APT experiment.
You must fill in all of the fields for the form to be accepted by the manager.

After the RHIT file is uploaded, you will be directed to the home page for the sample. 
Like the homepage for datasets, this page has links to forms for editing the metadata and adding new reconstructions to your webpage.

.. figure :: _static/dataset_list.png
	:width: 100%
	
	Webpage showing active datasets

To add a new reconstruction, first click the sample and then fill out the form describing how the reconstruction was performed.
As before, all fields are required and sucessfully submitting the form will bring you to a webpage describing the reconstruction.

At this point, your dataset will be organized in a similar way to the dataset shown below.
Each sample gets its own directory, which contains the RHIT file.
Reconstructions for each sample are in subdirectories of the sample directory, along with their respective RRNG and POS files. 
You will also note that each directory contains ``YAML`` files, which hold metadata about each dataset/sample/reconstruction. 
NUCAPT manager may also create folders for holding the post-processing (e.g., concentration profiles) of the reconstructions.

.. figure :: _static/folder_structure.png
	:height: 256px
	
	Example folder structure for a dataset.
	
Once the data is uploaded, you can rename any directory and edit the metadata either in a text editor (requiring you to maintain the YAML format) or through the website.
Every piece of data collected by the website is stored in text files inside of the directory, so you can move the folder containing your data elsewhere without loosing any metadata.
