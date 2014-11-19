import unittest
from builder.components import RollingMaterial


class RollingMaterialTestCase(unittest.TestCase):

    def setUp(self):
        self.rm = RollingMaterial()

        # set parameters
        self.rm.minimum_units = 104
        self.rm.speed = 40  # (km/h)
        self.rm.availability = 6570  # (hr/year)
        self.rm.capacity = 2400  # (ton)
        self.rm.head_stops_time = 15  # (hr/head_stop)
        self.rm.turnout_time = 2  # (hr/turnout_stop)
        self.rm.turnout_freq = 200  # (km between turnouts)
        self.rm.regroup_time = 6

    def test_add_freight_service(self):
        self.rm.add_freight_service(7286620, 500)

        # running time
        self.assertEqual(self.rm.running, 37962.5)

        # idle time (hours * units)
        self.assertEqual(self.rm.idle_heads, 91110.0)
        self.assertEqual(self.rm.idle_turnout, 15185.0)
        self.assertEqual(self.rm.idle_regroup, 0)

        # idle capacity (ton)
        self.assertEqual(self.rm.idle_capacity, 1090000.0)

        # regroup saved time (hours * units)
        self.assertEqual(self.rm.saved_idle_turnout, 0)
        self.assertEqual(self.rm.saved_running, 0)

    def test_regroup(self):

        self.rm.regroup(1000, 1000)
        self.assertEqual(self.rm.running, -25000.0)

        # idle time (hours * units)
        self.assertEqual(self.rm.idle_heads, 0.0)
        self.assertEqual(self.rm.idle_turnout, -10000.0)
        self.assertEqual(self.rm.idle_regroup, 6000.0)

        # idle capacity (ton)
        self.assertEqual(self.rm.idle_capacity, -2400000000.0)

        # regroup saved time (hours * units)
        self.assertEqual(self.rm.saved_idle_turnout, 10000.0)
        self.assertEqual(self.rm.saved_running, 25000.0)

    def test_revert_regroup(self):

        self.rm.revert_regroup(1000, 1000)
        self.assertEqual(self.rm.running, 25000.0)

        # idle time (hours * units)
        self.assertEqual(self.rm.idle_heads, 0.0)
        self.assertEqual(self.rm.idle_turnout, 10000.0)
        self.assertEqual(self.rm.idle_regroup, -6000.0)

        # idle capacity (ton)
        self.assertEqual(self.rm.idle_capacity, 2400000000.0)

        # regroup saved time (hours * units)
        self.assertEqual(self.rm.saved_idle_turnout, -10000.0)
        self.assertEqual(self.rm.saved_running, -25000.0)


if __name__ == '__main__':
    unittest.main()
