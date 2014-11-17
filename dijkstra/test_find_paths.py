import unittest
import os
import find_paths
from openpyxl import load_workbook


def compare_excels(excel1, excel2):
    """Compare two excels based on row iteration."""

    # load workbooks
    wb1 = load_workbook(excel1, use_iterators=True)
    wb2 = load_workbook(excel2, use_iterators=True)

    # check if sheets have same names
    if not wb1.get_sheet_names() == wb2.get_sheet_names():
        return False

    # iterate sheets
    for ws1, ws2 in zip(wb1.worksheets, wb2.worksheets):

        # iterate rows
        for row1, row2 in zip(ws1.iter_rows(), ws2.iter_rows()):

            # iterate cells
            for cell1, cell2 in zip(row1, row2):

                # evaluate cells value for equality
                if not cell1.value == cell2.value:
                    return False

    return True


class FindPathsModuleTestCase(unittest.TestCase):

    """Test finding shortest paths of railway mode."""

    def setUp(self):

        root_dir = os.path.dirname(__file__)

        # names of excels to be compared
        self.test_input_excel = os.path.join(root_dir, "test/test_railway_links_table.xlsx")
        self.test_compare_excel = os.path.join(root_dir, "test/test_railway_shortest_paths.xlsx")
        self.test_output_excel = os.path.join(root_dir, "test/railway_shortest_paths.xlsx")

        # run scraper method
        find_paths.main(self.test_input_excel, self.test_output_excel)

    def test_same_excels(self):
        self.assertTrue(compare_excels(self.test_compare_excel,
                                       self.test_output_excel))


def main():
    unittest.main()

if __name__ == '__main__':
    main()
