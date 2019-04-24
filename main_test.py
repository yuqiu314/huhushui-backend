import unittest
from tornado.testing import AsyncHTTPTestCase

class MyHTTPTest(AsyncHTTPTestCase):
    def get_app(self):
        return Application(['/tor/hotel/login', HotelLoginHandler])

    def test_homepage(self):
        self.http_client.fetch(self.get_url('/tor/hotel/login'), self.stop)
        response = self.wait()
        self.assertIn("hello", response.body)

if __name__ == '__main__':
    unittest.main()
