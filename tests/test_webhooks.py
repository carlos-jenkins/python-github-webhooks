import unittest
import os
import sys
# import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from webhooks import application as app


class WebhooksTest(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.output = False

    def show_response(self, response):
        if not self.output:
            return
        print('Status Code: %s' % response.status_code)
        print(response.headers)
        print(response.data)

    def test_unit_get(self):
        response = self.app.get('/')
        self.show_response(response)
        self.assertEqual(response.status_code, 405)

    def test_unit_post(self):
        response = self.app.post('/')
        self.show_response(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'{"msg": "pong"}')

    def test_unit_notfound(self):
        response = self.app.get('/notfound')
        self.show_response(response)
        self.assertEqual(response.status_code, 404)
