#!/usr/bin/env python
# encoding: utf-8

import unittest
import sys
import os
from tempfile import mkdtemp
import logging
import shutil

my_logger = logging.getLogger('TestLogger')
my_logger.setLevel(logging.DEBUG)


# Code being tested:
from situp import Generator, View


class GeneratorTest(unittest.TestCase):
    """

    """
    def setUp(self):
        self.test_gen = Generator()
        self.test_work_dir = mkdtemp()

    def tearDown(self):
        path = os.path.join(self.test_work_dir, 'testapp', 'test')
        shutil.rmtree(self.test_work_dir)

    def testCreatePath(self):
        """
        Should create the appropriate path
        """
        g_path = self.test_gen._create_path(self.test_work_dir, 'testapp', 'test')
        path = os.path.join(self.test_work_dir, 'testapp', 'interface', 'test')
        self.assertTrue(os.path.exists(path), 'did not create correct directory')
        self.assertEquals(path, g_path)

    def testPushTemplate(self):
        """
        Should not be implemented
        """
        path = os.path.join(self.test_work_dir, 'testapp', 'interface', 'test')
        self.assertRaises(NotImplementedError, self.test_gen._push_template, path)

class ViewTest(unittest.TestCase):
    """
    Test that a view is generated
    """
    def setUp(self):
        self.test_gen = View()
        self.test_work_dir = mkdtemp()

        self.reduce_path = os.path.join(self.test_work_dir, 'testapp/views/test/reduce.js')
        self.map_path = os.path.join(self.test_work_dir, 'testapp/views/test/map.js')

    def tearDown(self):
        shutil.rmtree(self.test_work_dir)

    def testCreateView(self):
        pass

    def testCreateViewWithBuiltIn(self):
        self.test_gen(self.test_work_dir, 'testapp', 'test', '_sum')
        self.assertTrue(os.path.exists(self.map_path),
                                'did not create built in map')
        self.assertTrue(os.path.exists(self.reduce_path),
                                'did not create built in reduce')

    def testCreateViewWithBuiltInShorthand(self):
        self.test_gen(self.test_work_dir, 'testapp', 'test', 'sum')
        self.assertTrue(os.path.exists(self.map_path),
                                'did not create built in map')
        self.assertTrue(os.path.exists(self.reduce_path),
                                'did not create short hand built in reduce')

    def testCreateViewWithInvalidBuiltIn(self):
        self.assertRaises(KeyError, self.test_gen, self.test_work_dir,
                                'testapp', 'test', '_foo')


if __name__ == '__main__':
    unittest.main()
