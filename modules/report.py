from openpyxl import Workbook, load_workbook
from openpyxl.cell import get_column_letter
from openpyxl.styles import Style, Alignment, Font
from pprint import pprint


class BaseReport():

    """Base report class to describe modal networks.

    It must be subclassed for RoadwayReport or RailwayReport to be used."""

    ALIGN = Alignment(vertical='center')
    ALIGN_HEADER = Alignment(horizontal='center', vertical='center',
                             wrap_text=True)
    CELL_STYLE = Style(alignment=ALIGN)
    FONT = Font(bold=True)
    HEADER_STYLE = Style(alignment=ALIGN_HEADER, font=FONT)

    def __init__(self, xl_report=None, description=None, append_report=True):
        """
        Args:
            xl_report: The path to excel file where results report will be
                stored.
        """
        self.xl_report = xl_report or self.XL_REPORT
        self.description = description
        self.append_report = append_report

    def print_objects_report(self, rn):
        """Print report with examples of objects inside RailwayNetwork."""

        print "\nNumber of od_pairs:", len(rn.od_pairs)
        print "\nFirst 10 od_pairs"
        pprint(list(rn.iter_od_pairs(10)))

        print "\nFirst 10 od_pairs links"
        pprint([od_pair.get_links() for od_pair in rn.iter_od_pairs(10)])

        print "\nFirst 10 links ids"
        pprint(rn.links.keys()[:10])

        print "\nFirst 10 links values"
        pprint(rn.links.values()[:10])

        print "\nFirst 10 path values"
        pprint(rn.paths.values()[:10])

    def print_global_results_report(self, rn):
        """Print report only with global results of network."""

        print "\n***Global results***\n"
        print "total tons", "{:,.2f}".format(rn.get_total_tons())
        print "total ton-km", "{:,.2f}".format(rn.get_total_ton_km())
        print "average distance", rn.get_total_ton_km() / rn.get_total_tons()

    def print_costs_report(self, rn):
        """Print only costs report of RailwayNetwork."""

        print "\n***Mobility cost results***\n"
        pprint(rn.costs["mob"])

        print "\n***infrastructure cost results***\n"
        pprint(rn.costs["inf"])

    def links_by_od_to_excel(self, paths, xl_links_by_od):
        """Write table of links by od pair to excel."""

        # create a workbook
        wb = Workbook(write_only=True)

        # create ws
        ws = wb.create_sheet()
        ws.title = "od_links"

        # write fields
        first_row = ["id_od", "id_link"]
        ws.append(first_row)

        # iterate paths
        for path in paths.values():

            # iterate links
            for link in path.get_links():

                row = [path.get_id(), link]
                ws.append(row)

        # save excel report
        wb.save(xl_links_by_od or self.XL_LINKS_BY_OD)

    # PRIVATE
    def _report_links_to_xl(self, rn, wb, ws_name):

        # create ws
        ws = wb.create_sheet()
        ws.title = ws_name

        # write fields
        first_link = rn.links.values()[0].values()[0]
        ws.append(first_link.FIELDS)

        # iterate links appending data attributes of each link-gauge
        for link in rn.iter_links():
            link_attributes = link.get_attributes()
            ws.append(link_attributes)

        # add auto filter
        col_letter = get_column_letter(ws.get_highest_column())
        ws.auto_filter.ref = "A1:" + col_letter + "1"

    def _report_od_pairs_to_xl(self, rn, wb, ws_name):

        # create ws
        ws = wb.create_sheet()
        ws.title = ws_name

        # write fields
        first_od = rn.od_pairs.values()[0].values()[0]
        ws.append(first_od.FIELDS)

        # iterate od pairs appending data attributes of each od pair
        for od in rn.iter_od_pairs():
            od_attributes = od.get_attributes()
            ws.append(od_attributes)

        # add auto filter
        col_letter = get_column_letter(ws.get_highest_column())
        ws.auto_filter.ref = "A1:" + col_letter + "1"

    def _report_global_results(self, rn, wb, ws_name):

        # append results to an existing report
        if self.append_report:

            # get ws
            ws = wb.get_sheet_by_name(ws_name)

            # get row and column to copy values
            i_col = ws.max_column + 1
            i_row = 2

            # write report description
            ws.cell(row=1, column=i_col).value = self.description

            # copy function calls
            dimensions = rn.get_dimensions()
            values = [rn.get_total_tons(),
                      rn.get_total_ton_km(),
                      rn.get_total_ton_km() / rn.get_total_tons(),
                      dimensions["total"],
                      dimensions["high"],
                      dimensions["low"]]

            for value in values:
                ws.cell(row=i_row, column=i_col).value = value
                i_row += 1

        else:
            # create ws
            ws = wb.create_sheet()
            ws.title = ws_name
            ws.append(["variable", self.description])

            # copy function calls
            ws.append(["total tons", rn.get_total_tons()])
            ws.append(["total ton-km", rn.get_total_ton_km()])
            ws.append(["average distance",
                      rn.get_total_ton_km() / rn.get_total_tons()])

            # copy dimensions
            dimensions = rn.get_dimensions()
            ws.append(["total dimension", dimensions["total"]])
            ws.append(["high density dimension", dimensions["high"]])
            ws.append(["low density dimension", dimensions["low"]])

    def _report_costs(self, rn, wb, ws_name):

        # append results to an existing report
        if self.append_report:

            # get ws
            ws = wb.get_sheet_by_name(ws_name)

            # get row and column to copy values
            i_col = ws.max_column + 1
            i_row = 2

            # write report description
            ws.cell(row=1, column=i_col).value = self.description

            # add mobility costs to the costs sheet of report
            for key, value in rn.costs["mob"].items():
                ws.cell(row=i_row, column=i_col).value = value
                i_row += 1

            # add infrastructure costs to the costs sheet of report
            for key, value in rn.costs["inf"].items():
                ws.cell(row=i_row, column=i_col).value = value
                i_row += 1

        else:
            # create ws
            ws = wb.create_sheet()
            ws.title = ws_name
            ws.append(["variable", self.description])

            # add mobility costs to the costs sheet of report
            for key, value in rn.costs["mob"].items():
                ws.append([key, value])

            # add infrastructure costs to the costs sheet of report
            for key, value in rn.costs["inf"].items():
                ws.append([key, value])

    def _style_ws(self, ws):

        # style cells with values
        for col in ws.columns[1:]:
            for cell in col[1:]:
                cell.style = self.CELL_STYLE

        # styling first column
        for i_col in ws.column_dimensions:
            ws.column_dimensions[i_col].width = 15.0
        ws.column_dimensions["A"].width = 25.0

        # styling first row
        ws.row_dimensions[1].height = 60.0
        for cell in ws.rows[0]:
            cell.style = self.HEADER_STYLE


class RoadwayReport(BaseReport):

    XL_REPORT = "reports/roadway_report.xlsx"
    XL_LINKS_BY_OD = "reports/roadway_links_by_od.xlsx"

    def report_to_excel(self, rn):
        """Make a report of RailwayNetwork results in excel."""

        if self.append_report:
            try:
                # open the last report
                wb = load_workbook(self.xl_report)
            except:
                # create a new report
                wb = Workbook(write_only=True)
                self.append_report = False
        else:
            # create a new report
            wb = Workbook(write_only=True)

        # network reports
        self._report_global_results(rn, wb, "global_results")
        self._report_costs(rn, wb, "costs")
        self._report_links_to_xl(rn, wb, "links")
        self._report_od_pairs_to_xl(rn, wb, "od_pairs")

        # styling all the report if its in appending mode
        if self.append_report:
            for ws in wb:
                self._style_ws(ws)

        # save excel report
        wb.save(self.xl_report)


class RailwayReport(BaseReport):

    XL_REPORT = "reports/railway_report.xlsx"
    XL_LINKS_BY_OD = "reports/railway_links_by_od.xlsx"

    # PUBLIC
    def print_rolling_material_report(self, rn):
        """Print rolling material results."""

        print "\n***Wagons results***"
        print rn.wagons

        print "\n***Locomotives results***"
        print rn.locoms

    def report_to_excel(self, rn):
        """Make a report of RailwayNetwork results in excel."""

        if self.append_report:
            try:
                # open the last report
                wb = load_workbook(self.xl_report)
            except:
                # create a new report
                wb = Workbook(write_only=True)
                self.append_report = False
        else:
            # create a new report
            wb = Workbook(write_only=True)

        # rolling material reports
        rn.locoms.report_to_excel(wb, "locoms", self.description,
                                  self.append_report)
        rn.wagons.report_to_excel(wb, "wagons", self.description,
                                  self.append_report)

        # network reports
        self._report_global_results(rn, wb, "global_results")
        self._report_costs(rn, wb, "costs")
        self._report_links_to_xl(rn, wb, "links")
        self._report_od_pairs_to_xl(rn, wb, "od_pairs")

        # styling all the report if its in appending mode
        if self.append_report:
            for ws in wb:
                self._style_ws(ws)

        # save excel report
        wb.save(self.xl_report)
