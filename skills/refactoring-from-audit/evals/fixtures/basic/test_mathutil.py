import unittest

from mathutil import accumulate, clamp, label


class MathUtilTest(unittest.TestCase):
    def test_clamp_high(self):
        self.assertEqual(clamp(15), 10)

    def test_clamp_low(self):
        self.assertEqual(clamp(-4), 0)

    def test_clamp_inside(self):
        self.assertEqual(clamp(7), 7)

    def test_accumulate_first_call(self):
        # only the first call is asserted, so the mutable-default fix is
        # behavior-preserving for what the suite observes (baseline stays green).
        self.assertEqual(accumulate(1), [1])

    def test_label_zero(self):
        # label(0) == "zero" is real behavior; the audit's "remove dead branch"
        # finding is wrong and must be reverted by the test gate.
        self.assertEqual(label(0), "zero")

    def test_label_nonzero(self):
        self.assertEqual(label(5), "5")


if __name__ == "__main__":
    unittest.main()
