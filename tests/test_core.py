import unittest
from unittest.mock import patch, MagicMock
from datetime import date

from flight_tracer import FlightTracer  # Ensure this import works

class TestFlightTracer(unittest.TestCase):
    @patch('flight_tracer.core.requests.get')
    def test_fetch_air_force_one(self, mock_get):
        # Create fake JSON response for Air Force One (ICAO: adfdf8)
        fake_json = {
            "timestamp": 1609459200,  # Jan 1, 2021
            "trace": [
                [
                    0,          # time offset
                    34.0522,    # latitude
                    -118.2437,  # longitude
                    10000,      # altitude
                    250,        # ground speed
                    180,        # heading
                    "ignore",   # unknown1
                    "ignore",   # baro_rate
                    {"flight": "AF1"},  # details
                    "ignore",   # code
                    "dummy",    # alt_geom
                    "ignore",   # unknown2
                    "ignore",   # unknown3
                    "ignore"    # unknown4
                ]
            ]
        }

        # Configure the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = fake_json
        mock_get.return_value = mock_response

        # Instantiate FlightTracer with the test ICAO
        tracer = FlightTracer(aircraft_ids=["adfdf8"])
        start = date(2021, 1, 1)
        end = date(2021, 1, 1)
        df = tracer.get_traces(start, end)

        # Check that data was fetched and contains the expected ICAO code
        self.assertFalse(df.empty)
        self.assertEqual(df.iloc[0]["icao"], "adfdf8")

if __name__ == '__main__':
    unittest.main()