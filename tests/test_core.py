import unittest
from datetime import date
from flight_tracer import FlightTracer

class TestFlightTracer(unittest.TestCase):
    def test_generate_urls_single_day(self):
        # Create a FlightTracer instance with a dummy ICAO list
        tracer = FlightTracer(aircraft_ids=["0d086e"])
        # Using a single day: Jan 1, 2025 to Jan 1, 2025
        urls = tracer.generate_urls(date(2025, 1, 1), date(2025, 1, 1))
        # Expect 1 URL for a single day
        self.assertEqual(len(urls), 1)
        # Verify that the URL contains the correct date parts and ICAO code
        expected_url = "https://globe.adsbexchange.com/globe_history/2025/01/01/traces/6e/trace_full_0d086e.json"
        self.assertEqual(urls[0][0], expected_url)
    
    def test_generate_urls_multiple_days(self):
        tracer = FlightTracer(aircraft_ids=["0d086e"])
        # Using two days: Jan 1, 2025 to Jan 2, 2025
        urls = tracer.generate_urls(date(2025, 1, 1), date(2025, 1, 2))
        # Expect 2 URLs (one for each day)
        self.assertEqual(len(urls), 2)

if __name__ == '__main__':
    unittest.main()