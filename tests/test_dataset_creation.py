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

    def test_create(self):
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


if __name__ == '__main__':
    unittest.main()
