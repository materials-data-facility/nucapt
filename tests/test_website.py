import os
import shutil
import tempfile
import unittest
from datetime import date

from bs4 import BeautifulSoup

import nucapt
from nucapt import manager


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

        # Make creation form
        data = {
            'title': 'Sample dataset',
            'abstract': 'Dataset for unittest',
            'authors-0-first_name': 'Logan',
            'authors-0-last_name': 'Ward',
            'authors-0-affiliation': 'UChicago'
        }
        rv = self.app.post('/create', data=data, follow_redirects=True)

        # Get the name for this dataset
        name = '%s_Ward_0' % (date.today().strftime("%d%b%y"))

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

        #  Update the form and repeat
        data['authors-0-first_name'] = 'Not Logan'
        rv = self.app.post('/dataset/%s/edit'%name, data=data)
        self.assertEquals(302, rv.status_code)

        metadata = manager.APTDataDirectory.load_dataset_by_name(name).get_metadata()
        self.assertEquals('Not Logan', metadata['authors'][0]['first_name'])

if __name__ == '__main__':
    unittest.main()
