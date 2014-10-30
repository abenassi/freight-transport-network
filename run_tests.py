import unittest
import os


def main():

    # load all tests in package
    test_suite = unittest.TestLoader().discover(os.path.dirname(__file__))

    # run all tests in package
    unittest.TextTestRunner().run(test_suite)


if __name__ == '__main__':
    main()
