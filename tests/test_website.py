from __future__ import print_function

import os
import shutil
import tempfile
import unittest
from io import BytesIO
from datetime import date

from bs4 import BeautifulSoup

import nucapt
from nucapt import manager
from nucapt.manager import APTSampleDirectory, APTReconstruction, APTAnalysisDirectory


class TestWebsite(unittest.TestCase):
    def setUp(self):
        # Make a temporary directory
        manager.data_path = tempfile.mkdtemp()
        nucapt.app.config['WORKING_PATH'] = manager.data_path

        # Set us to testing mode
        nucapt.app.testing = True
        nucapt.app.config['DEBUG_SKIP_AUTH'] = True
        nucapt.app.config['DEBUG_SKIP_PUB'] = True

        # Make the client
        self.app = nucapt.app.test_client()
        with self.app.session_transaction() as sess:
            sess.update({
                'is_authenticated': True,
                'name': 'Test User',
                'email': 'test@test.edu'
            })

    def tearDown(self):
        shutil.rmtree(manager.data_path)

    def test_home(self):
        rv = self.app.get('/')
        self.assertEquals(200, rv.status_code)

    def test_dataset_methods(self):
        rv = self.app.get('/create')
        self.assertEquals(200, rv.status_code)

        data, rv, name = self.create_dataset()

        # Check to make sure we're on the right page
        soup = BeautifulSoup(rv.data, 'html.parser')
        self.assertTrue(name in str(soup.head.title))

        # Check to make sure the directory exists and has proper metadata
        self.assertEquals(1, len(os.listdir(manager.data_path)))
        self.assertTrue(os.path.isdir(os.path.join(manager.data_path, name)))
        dataset = manager.APTDataDirectory.load_dataset_by_name(name)
        metadata = dataset.get_metadata()
        self.assertEquals(data['abstract'], metadata['abstract'])

        # Make a second dataset with another author
        data['authors-1-first_name'] = 'Ben'
        data['authors-1-last_name'] = 'Blaiszik'
        data['authors-1-affiliation'] = 'UChicago'

        rv = self.app.post('/create', data=data, follow_redirects=True)

        name = '%s_Ward_1' % (date.today().strftime("%d%b%y"))
        soup = BeautifulSoup(rv.data, 'html.parser')
        self.assertTrue(name in str(soup.head.title))

        self.assertTrue(os.path.isdir(os.path.join(manager.data_path, name)))
        dataset = manager.APTDataDirectory.load_dataset_by_name(name)
        metadata = dataset.get_metadata()
        self.assertEquals(data['authors-1-affiliation'], metadata['authors'][1]['affiliation'])

        # Test the listing
        datasets = os.listdir(manager.data_path)
        rv = self.app.get('/datasets')
        soup = BeautifulSoup(rv.data, 'html.parser')
        for dataset in datasets:
            self.assertTrue(dataset in str(rv.data))

        # Test editing a dataset
        rv = self.app.get('/dataset/%s/edit' % name)
        self.assertEquals(200, rv.status_code)

        soup = BeautifulSoup(rv.data, 'html.parser')
        #  Make sure the form values are updated
        for k,v in data.items():
            if k is not 'abstract':
                form = soup.find("input", {'name': k})
                self.assertEquals(v, form['value'])
            else:
                form = soup.find("textarea", {'name': k})
                self.assertEquals(v, form.next)

        #  Update the form and see if it updates the medata
        data['authors-0-first_name'] = 'Not Logan'
        rv = self.app.post('/dataset/%s/edit'%name, data=data, follow_redirects=True)
        self.assertEquals(200, rv.status_code)

        metadata = manager.APTDataDirectory.load_dataset_by_name(name).get_metadata()
        self.assertEquals('Not Logan', metadata['authors'][0]['first_name'])

        #  Make sure requesting a bogus dataset gets redirected
        rv = self.app.get('/dataset/bogus/edit')
        self.assertEquals(302, rv.status_code)

        # Add a empty directory to the working directory, make sure dataset listing doesn't fail
        os.mkdir(os.path.join(manager.data_path, 'empty_dir'))
        rv = self.app.get('/datasets')
        self.assertEquals(200, rv.status_code)

    def test_sample_method(self):

        # Make an initial dataset
        _, _, dataset_name = self.create_dataset()

        # Feed a bogus dataset name, make sure it is redirected
        rv = self.app.get('/dataset/bogus/sample/create')
        self.assertEquals(302, rv.status_code)

        # Get the sample form
        rv = self.app.get('/dataset/%s/sample/create'%dataset_name)
        self.assertEquals(200, rv.status_code)

        soup = BeautifulSoup(rv.data, 'html.parser')
        name_field = soup.find('input', {'id': 'sample_name'})
        self.assertEquals('Sample1', name_field['value'])

        # Create a new sample
        data, rv = self.create_sample(dataset_name)
        self.assertEquals(302, rv.status_code)

        self.assertTrue(os.path.isdir(os.path.join(manager.data_path, dataset_name, 'Sample1')))

        # Check the metadata
        sample = APTSampleDirectory.load_dataset_by_name(dataset_name, 'Sample1')
        sample_metadata = sample.load_sample_information()
        self.assertEquals('Example Sample', sample_metadata['sample_title'])
        self.assertEquals('2 hours', sample_metadata['metadata'][0]['value'])

        # Check that the file appeared
        self.assertTrue(os.path.exists(os.path.join(manager.data_path, dataset_name, 'Sample1', 'EXAMPLE.RHIT')))

        # Render the sample
        rv = self.app.get('/dataset/%s/sample/Sample1'%dataset_name)
        self.assertEquals(rv.status_code, 200)

        self.assertTrue(b'No reconstructions' in rv.data)
        self.assertTrue(b'Add Reconstruction' in rv.data)

        # Make sure creating a second sample fails
        data, rv = self.create_sample(dataset_name, 'Sample1')
        self.assertEquals(200, rv.status_code)

        self.assertTrue('Sample Sample1 already exists for dataset %s'%(dataset_name) in str(rv.data))

        # Make a second sample
        data, rv = self.create_sample(dataset_name, 'Sample2')
        self.assertEquals(302, rv.status_code)

        # Make sure both appear in dataset page
        rv = self.app.get('/dataset/%s'%dataset_name)
        self.assertIn(b'Sample1', rv.data)
        self.assertIn(b'Sample2', rv.data)

        # Edit the general metdata of Sample1
        rv = self.app.get('/dataset/%s/sample/%s/edit_info'%(dataset_name, 'Sample1'))
        self.assertEquals(200, rv.status_code)

        soup = BeautifulSoup(rv.data, 'html.parser')
        field = soup.find('input', {'id': 'sample_title'})
        self.assertEquals('Example Sample', field['value'])

        field = soup.find('input', {'id': 'metadata-0-key'})
        self.assertEquals('Aging time', field['value'])

        data = {
            'sample_title': 'new title',
            'sample_description': 'new description'
        }
        rv = self.app.post('/dataset/%s/sample/%s/edit_info'%(dataset_name, 'Sample1'), data=data)
        self.assertEquals(302, rv.status_code)
        sample = APTSampleDirectory.load_dataset_by_name(dataset_name, 'Sample1')
        sample_metadata = sample.load_sample_information()
        self.assertEquals('new title', sample_metadata['sample_title'])

        # Edit the collection information
        sample_metadata = sample.load_collection_metadata()
        self.assertEquals('A nice one', sample_metadata['leap_model'])

        rv = self.app.get('/dataset/%s/sample/%s/edit_collection' % (dataset_name, 'Sample1'))
        self.assertEquals(200, rv.status_code)

        soup = BeautifulSoup(rv.data, 'html.parser')
        field = soup.find('input', {'id': 'leap_model'})
        self.assertEquals('A nice one', field['value'])

        sample_metadata.metadata['leap_model'] = 'A super one'
        rv = self.app.post('/dataset/%s/sample/%s/edit_collection' % (dataset_name, 'Sample1'),
                           data=sample_metadata.metadata)
        self.assertEquals(302, rv.status_code)
        sample_metadata = sample.load_collection_metadata()
        self.assertEquals('A super one', sample_metadata['leap_model'])

        # Check sample preparation metadata
        prep_metadata = sample.get_preparation_metadata()
        self.assertEquals('water', prep_metadata['electropolish'][0]['solution'])

        rv = self.app.get('/dataset/%s/sample/%s/edit_preparation' % (dataset_name, 'Sample1'))

        self.assertEquals(200, rv.status_code)

        new_prep = {
            'preparation_method': 'fib_lift_out',
            'fib_lift_out-lift_out_step-capping_material': 'metal',
            'fib_lift_out-lift_out_step-ion_current': 1.,
            'fib_lift_out-lift_out_step-ion_voltage': 2,
            'fib_lift_out-lift_out_step-sample_orientation': 'up',
            'fib_lift_out-lift_out_step-wedge_dimension': 1,
            'fib_lift_out-sharpening_step-final_ion_current': 1,
            'fib_lift_out-sharpening_step-final_ion_voltage': 2,
        }

        rv = self.app.post('/dataset/%s/sample/%s/edit_preparation' % (dataset_name, 'Sample1'), data=new_prep)

        self.assertEquals(302, rv.status_code)

        prep_metadata = sample.get_preparation_metadata()
        self.assertNotIn('electropolish', prep_metadata.metadata)
        self.assertEquals('metal', prep_metadata['fib_lift_out']['lift_out_step']['capping_material'])

        # Create a sample without an RHIT file
        data, rv = self.create_sample(dataset_name, 'Sample3', no_rhit=True)
        self.assertEquals(302, rv.status_code)

        # Make sure the webpage works
        rv = self.app.get('/dataset/%s/sample/Sample3'%dataset_name)
        self.assertEquals(200, rv.status_code)

    def test_reconstructions(self):
        """Test dealing with reconstructions"""

        # Create dataset and sample
        _, _, dataset_name = self.create_dataset()
        sample_data, _ = self.create_sample(dataset_name)
        sample_name = sample_data['sample_name']

        # Make sure reconstruction page renders
        rv = self.app.get('/dataset/%s/sample/%s/recon/create'%(dataset_name, sample_name))

        self.assertEquals(200, rv.status_code)

        soup = BeautifulSoup(rv.data, 'html.parser')
        name_field = soup.find('input', {'name': 'name'})
        self.assertEquals('Reconstruction1', name_field['value'])

        # Create the reconstruction
        recon_data, rv = self.create_reconstruction(dataset_name, sample_name)

        self.assertEquals(302, rv.status_code)
        self.assertTrue(os.path.exists(
            os.path.join(manager.data_path, dataset_name, sample_name, 'Recon1')
        ))
        recon = APTReconstruction.load_dataset_by_name(dataset_name,
                                                       sample_name,
                                                       'Recon1')
        self.assertTrue(os.path.isfile(recon.get_pos_file()))
        self.assertTrue(os.path.isfile(recon.get_rrng_file()))
        self.assertTrue(os.path.isfile(os.path.join(recon.path, 'tip_image.jpg')))
        self.assertNotIn('shank_angle', recon.load_metadata().metadata.keys())
        self.assertEquals(recon.load_metadata()['tip_image'], 'tip_image.jpg')

        # Make sure the webpages update
        rv = self.app.get('/dataset/%s/sample/%s/recon/%s'%(dataset_name, sample_name, 'Recon1'))

        self.assertEquals(200, rv.status_code)
        self.assertIn(recon.get_rrng_file().encode('ascii'), rv.data)
        self.assertIn(recon.get_pos_file().encode('ascii'), rv.data)

        rv = self.app.get('/dataset/%s/sample/%s'%(dataset_name, sample_name))

        self.assertEquals(200, rv.status_code)
        self.assertIn(b'Recon1', rv.data)

    def test_add_analysis(self):
        """Test dealing with adding analysis data"""

        # Create dataset, sample, and reconstruction
        _, _, dataset_name = self.create_dataset()
        sample_data, _ = self.create_sample(dataset_name)
        sample_name = sample_data['sample_name']
        recon_data, rv = self.create_reconstruction(dataset_name, sample_name)
        recon_name = recon_data['name']

        # Make sure the recon page displays 'no analyses'
        rv = self.app.get('/dataset/%s/sample/%s/recon/%s' % (dataset_name, sample_name, recon_name))
        self.assertEquals(200, rv.status_code)
        self.assertIn(b'No analyses', rv.data)

        # Try making a new analysis
        analysis_data, rv = self.create_analysis(dataset_name, sample_name, recon_name)
        self.assertEquals(302, rv.status_code)
        analysis_name = analysis_data['folder_name']
        analysis = APTAnalysisDirectory.load_dataset_by_name(dataset_name, sample_name,
                                                             recon_name, analysis_name)

        # Check to make sure the directory was made
        self.assertTrue(os.path.isdir(os.path.join(analysis.path)))
        for f in ['data.dat', 'data.png']:
            self.assertTrue(os.path.isfile(os.path.join(analysis.path, f)))

        # Check to make sure the reconstruction page was properly updated
        rv = self.app.get('/dataset/%s/sample/%s/recon/%s' % (dataset_name, sample_name, recon_name))
        self.assertEquals(200, rv.status_code)
        self.assertIn(b'1D_Concentration_Profile', rv.data)
        self.assertIn(b'Example analysis', rv.data)

        # Make sure the editing page has the old metadata
        rv = self.app.get('/dataset/%s/sample/%s/recon/%s/analysis/%s/edit' % (dataset_name, sample_name,
                                                                               recon_name, analysis_name))

        soup = BeautifulSoup(rv.data, 'html.parser')
        name_field = soup.find('input', {'name': 'title'})
        self.assertEquals(analysis_data['title'], name_field['value'])

        # Test editing the data
        analysis_data['title'] = 'new title'
        analysis_data['files'] = [(BytesIO(b'<junk>'), 'new_data.dat')]

        rv = self.app.post('/dataset/%s/sample/%s/recon/%s/analysis/%s/edit' % (dataset_name, sample_name,
                                                                               recon_name, analysis_name),
                          data=analysis_data)
        self.assertEquals(302, rv.status_code)
        self.assertTrue(os.path.isfile(os.path.join(analysis.path, 'new_data.dat')))
        metadata = analysis.load_metadata()
        self.assertEquals(analysis_data['title'], metadata['title'])

    def test_publication(self):
        """Test dealing with reconstructions"""

        # Create dataset, sample, and reconstruction
        _, _, dataset_name = self.create_dataset()
        sample_data, _ = self.create_sample(dataset_name)
        sample_name = sample_data['sample_name']
        recon_data, rv = self.create_reconstruction(dataset_name, sample_name)

        # Test getting the request form
        rv = self.app.get('/dataset/%s/publish'%dataset_name)
        self.assertEquals(200, rv.status_code)
        soup = BeautifulSoup(rv.data, 'html.parser')
        self.assertEqual('test@test.edu', soup.find('input', {'id': 'contact_email'})['value'])

        # Test submitting the publication request
        submit_form = {
            'title': 'Sample dataset',
            'abstract': 'Dataset for unittest',
            'authors-0-first_name': 'Logan',
            'authors-0-last_name': 'Ward',
            'authors-0-affiliation': 'UChicago',
            'contact_email' : 'test@test.edu',
            'contact_person': 'Test user',
            'accept_license': True
        }
        rv = self.app.post('/dataset/%s/publish'%dataset_name, data=submit_form)
        self.assertEquals(302, rv.status_code)

        # Check that the publication file was created
        self.assertTrue(os.path.isfile(os.path.join(manager.data_path, dataset_name, 'PublicationData.yaml')))

        # Check to make sure that trying to publish again sends you back to the main page
        rv = self.app.post('/dataset/%s/publish'%dataset_name, data=submit_form, follow_redirects=True)
        self.assertEquals(200, rv.status_code)
        self.assertIn(b'has already been published', rv.data)

        # Make sure that dataset page is missing links named edit
        soup = BeautifulSoup(rv.data, 'html.parser')
        for a in soup.find_all('a'):
            self.assertNotIn('edit', a['href'])
            self.assertNotIn('create', a['href'])

        # Check that the 'edit' links from sample and reconstruction pages are also gone
        for page in ['/dataset/%s/sample/%s'%(dataset_name, sample_name),
                     '/dataset/%s/sample/%s/recon/%s'% (dataset_name, sample_name, recon_data['name'])]:
            rv = self.app.get(page)
            soup = BeautifulSoup(rv.data, 'html.parser')
            for a in soup.find_all('a'):
                self.assertNotIn('edit', a['href'])
                self.assertNotIn('edit', a['href'])

        # Check that the edit pages are blocked
        for page in ['/dataset/%s/sample/create'% dataset_name,
                     '/dataset/%s/sample/%s/recon/create'% (dataset_name, sample_name),
                     '/dataset/%s/edit' % dataset_name,
                     '/dataset/%s/sample/%s/edit_info' % (dataset_name, sample_name),
                     '/dataset/%s/sample/%s/edit_collection' % (dataset_name, sample_name),
                     '/dataset/%s/sample/%s/edit_preparation' % (dataset_name, sample_name),
                     ]:
            rv = self.app.get(page, follow_redirects=True)
            self.assertEquals(200, rv.status_code)
            self.assertIn(b'has already been published', rv.data)

    def create_reconstruction(self, dataset_name, sample_name, recon_name='Recon1'):
        """Add a reconstruction to a sample

        :param dataset_name: str, dataset name
        :param sample_name: str, sample name
        :param recon_name: str, reconstruction name
        :return:
            - dict, Data passed to form
            - Response, response form server
        """
        data = {
            'name': recon_name,
            'title': 'Example reconstruction',
            'description': 'Example reconstruction',
            'tip_radius': 1,
            'tip_image': (BytesIO(b'<image>'), 'tip.jpg'),
            'pos_file': (BytesIO(b'Contents'), 'EXAMPLE.pos'),
            'rrng_file': (BytesIO(b'Contents'), 'EXAMPLE.RRNG'),
        }
        return data, self.app.post(
            '/dataset/%s/sample/%s/recon/create'%(dataset_name,sample_name),
            data=data
        )

    def create_sample(self, dataset_name, sample_name='Sample1', no_rhit=False):
        """Create a sample

        :param no_rhit: bool, whether to submit an RHIT file
        :param dataset_name: str, Name of dataset
        :param sample_name: str, Name of sample
        :return: 
            - dict, Data passed to form
            - Response, Response from server
        """
        data = {
            'sample_name': sample_name,
            'sample_form-sample_title': 'Example Sample',
            'sample_form-sample_abstract': 'Sample description',
            'sample_form-metadata-0-key': 'Aging time',
            'sample_form-metadata-0-value': '2 hours',
            'collection_form-leap_model': 'A nice one',
            'collection_form-evaporation_mode': 'laser',
            'preparation_form-preparation_method': 'electropolish',
            'preparation_form-electropolish-0-solution': 'water',
            'preparation_form-electropolish-0-temperature': 1,
            'preparation_form-electropolish-0-voltage': 1,
        }

        # Add RHIT file, if desired
        if not no_rhit:
            data['rhit_file'] = (BytesIO(b'My RHIT file contents'), 'EXAMPLE.RHIT')
        else:
            data['rhit_file'] = (None, '')  # This is how Flask receives 'no file'
        rv = self.app.post('/dataset/%s/sample/create' % dataset_name, data=data)
        return data, rv

    def create_dataset(self):
        """Make a sample dataset

        :return:
            - dict, values given to dataset creation form
            - Response, response from NUCAPT publication
            - name, Expected dataset name <date>_Ward_0
        """
        # Make creation form
        data = {
            'title': 'Sample dataset',
            'abstract': 'Dataset for unittest',
            'authors-0-first_name': 'Logan',
            'authors-0-last_name': 'Ward',
            'authors-0-affiliation': 'UChicago'
        }
        rv = self.app.post('/create', data=data, follow_redirects=True)
        name = '%s_Ward_0' % (date.today().strftime("%d%b%y"))
        return data, rv, name

    def create_analysis(self, dataset_name, sample_name, recon_name):
        """Make a sample analysis directory"""

        data = {
            'title': 'Example analysis',
            'description': 'Example analysis data for some reason',
            'folder_name': '1D_Concentration_Profile',
            'files': [(BytesIO(b'<data>'), 'data.dat'), (BytesIO(b'<image>'), 'data.png')]
        }
        return data, self.app.post(
            '/dataset/%s/sample/%s/recon/%s/analysis/create' % (dataset_name, sample_name, recon_name),
            data=data
        )

if __name__ == '__main__':
    unittest.main()
