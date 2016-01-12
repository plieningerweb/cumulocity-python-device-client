import unittest
import app

try:
    from unittest import mock
except ImportError:
    import mock

from Cumulocity import Cumulocity

class TestApp(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    @mock.patch('Cumulocity.Cumulocity', spec=Cumulocity)
    def testMeasurement(self, mock_cumulocity):

        Cumulocity('test-id')
        c_instance = mock_cumulocity.return_value

        app.measure(c_instance)

        expected_data = []


        #check if we got exactly two calls
        expected_calls = [
                mock.ANY,
                mock.ANY]

        self.assertEqual(c_instance.addMeasurement.mock_calls, expected_calls)
