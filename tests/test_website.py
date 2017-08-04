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
from nucapt.manager import APTSampleDirectory


class TestWebsite(unittest.TestCase):
    def setUp(self):
        nucapt.app.testing = True
        manager.data_path = tempfile.mkdtemp()
        self.app = nucapt.app.test_client()

    def tearDown(self):
        shutil.rmtree(manager.data_path)

    def test_home(self):
        rv = self.app.get('/')
        self.assertEquals(200, rv.status_code)

    def test_dataset_methods(self):
        rv = self.app.get('/create')
        self.assertEquals(200, rv.status_code)

        data, rv, name = self._make_dataset()

        # Check to make sure we're on the right page
        soup = BeautifulSoup(rv.data, 'html.parser')
        self.assertTrue(name in str(soup.head.title))

        # Check to make sure the directory exists and has proper metadata
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
        rv = self.app.get('/dataset/%s/edit'%name)
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

    def _make_dataset(self):
        """Make a sample dataset

        :return: dict, values given to dataset creation form
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

    def test_sample_method(self):

        # Make an initial dataset
        _, _, dataset_name = self._make_dataset()

        # Feed a bogus dataset name, make sure it is redirected
        rv = self.app.get('/dataset/bogus/sample/create')
        self.assertEquals(302, rv.status_code)

        # Get the sample form
        rv = self.app.get('/dataset/%s/sample/create'%dataset_name)
        self.assertEquals(200, rv.status_code)

        soup = BeautifulSoup(rv.data, 'html.parser')
        name_field = soup.find('input', {'id':'sample_name'})
        self.assertEquals('Sample1', name_field['value'])

        # Create a new sample
        data = {
            'sample_name': 'Sample1',
            'sample_form-sample_title': 'Example Sample',
            'sample_form-sample_abstract': 'Sample description',
            'sample_form-metadata-0-key': 'Aging time',
            'sample_form-metadata-0-value': '2 hours',
            'collection_form-evaporation_mode': 'laser',
            'rhit_file':(BytesIO(b'My RHIT file contents'), 'EXAMPLE.RHIT')
        }
        rv = self.app.post('/dataset/%s/sample/create'%dataset_name, data=data)
        self.assertEquals(302, rv.status_code)

        self.assertTrue(os.path.isdir(os.path.join(manager.data_path, dataset_name, 'Sample1')))

        # Check the metadata
        sample = APTSampleDirectory.load_dataset_by_name(dataset_name, 'Sample1')
        sample_metadata = sample.load_sample_information()
        self.assertEquals('Example Sample', sample_metadata['sample_title'])
        self.assertEquals('2 hours', sample_metadata['metadata'][0]['value'])




if __name__ == '__main__':
    unittest.main()
