from unittest import TestCase


class OneTestCaseClass(TestCase):
    def test_test_1(self):
        print "test1"
        self.assertEqual(2, 2)

    def test_test_2(self):
        print "test2"
        self.assertEqual(3, 3)

    def test_test_3(self):
        print "test3"
        self.assertEqual(3, 4)
