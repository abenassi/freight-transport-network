import unittest
import os
import find_paths
from openpyxl import load_workbook


def compare_cells(wb1, wb2):
    """Compare two excels based on row iteration."""

    # compare each cell of each worksheet
    for ws1, ws2 in zip(wb1.worksheets, wb2.worksheets):
        for row1, row2 in zip(ws1.iter_rows(), ws2.iter_rows()):
            for cell1, cell2 in zip(row1, row2):

                msg = str(cell1.value) + " != " + str(cell2.value)
                assert cell1.value == cell2.value, msg

    return True


class FindPathsModuleTestCase(unittest.TestCase):

    """Test finding shortest paths of railway mode."""

    def setUp(self):

        root_dir = os.path.dirname(__file__)

        # names of excels to be compared
        XL_LINKS = "test/test_railway_links_table.xlsx"
        XL_EXPECTED_PATHS = "test/test_railway_shortest_paths.xlsx"
        XL_PATHS = "test/railway_shortest_paths.xlsx"
        self.test_input_excel = os.path.join(root_dir, XL_LINKS)
        self.test_compare_excel = os.path.join(root_dir, XL_EXPECTED_PATHS)
        self.test_output_excel = os.path.join(root_dir, XL_PATHS)

        # run scraper method
        find_paths.main(self.test_input_excel, self.test_output_excel)

    def test_same_excels(self):

        wb1 = load_workbook(self.test_compare_excel, use_iterators=True)
        wb2 = load_workbook(self.test_output_excel, use_iterators=True)

        self.assertEqual(wb1.get_sheet_names(), wb2.get_sheet_names())
        self.assertTrue(compare_cells(wb1, wb2))


class ShortestPathsMethodsTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_find_shortest_paths_with_restrictions(self):
        pass


if __name__ == '__main__':
    unittest.main()
