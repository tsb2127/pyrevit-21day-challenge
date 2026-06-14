# -*- coding: utf-8 -*-
__title__   = "Excel Smuggler (POC)"
__doc__     = """Version = 0.1 (Proof of Concept)
Date    = 06.13.2026
________________________________________________________________
Description:
POC - export the project's sheet list to a real .xlsx file.

Collects all ViewSheets, builds a rows table, writes it with
xlsxwriter (bundled with pyRevit), and prints the same table
in the pyRevit output window for comparison. Read-only.

V1 will add: sheet/parameter selection, formatting, and the
import-back-to-Revit half (read Excel, update parameters).
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 21 - POC)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script
import datetime, os

# 🎯 Third-party library — bundled WITH pyRevit's install.
# xlsxwriter = write .xlsx | xlrd = read .xlsx
# (openpyxl is Python-3-only; pyRevit runs IronPython 2.7 — skip it)
import xlsxwriter


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
output = script.get_output()


# ╔═╗╦═╗╔═╗╔═╗╔═╗  ╔═╗╔═╗  ╔═╗╔═╗╔╗╔╔═╗╔═╗╔═╗╔╦╗
# ╠═╝╠╦╝║ ║║ ║╠╣   ║ ║╠╣   ║  ║ ║║║║║  ║╣ ╠═╝ ║
# ╩  ╩╚═╚═╝╚═╝╚    ╚═╝╚    ╚═╝╚═╝╝╚╝╚═╝╚═╝╩   ╩
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Get all sheets in the project
all_sheets = (FilteredElementCollector(doc)
              .OfClass(ViewSheet)
              .WhereElementIsNotElementType()
              .ToElements())

if not all_sheets:
    forms.alert('No sheets in this project. Open a project with sheets.',
                exitscript=True)


# 2️⃣ Build the table: list-of-lists, headers at row 0
# 🎯 CS PATTERN: tabular serialization. Once the data is rows of
# strings, the destination (xlsx / csv / report) is interchangeable.
headers = ["Sheet ID", "Sheet Number", "Sheet Name"]
data = [headers]

for sheet in sorted(all_sheets, key=lambda s: s.SheetNumber):
    data.append([
        str(sheet.Id),
        sheet.SheetNumber,
        sheet.Name,
    ])


# 3️⃣ Build the export filepath (timestamped to avoid collisions)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
filename  = 'Sheet_Export_{}.xlsx'.format(timestamp)
base_path = os.path.join(os.path.expanduser('~'), 'Documents')
path_excel = os.path.join(base_path, filename)


# 4️⃣ Write the Excel file
# 🎯 CS PATTERN: context manager. The `with` block guarantees the
# workbook is closed and flushed to disk even if a write fails
# mid-way. An unclosed workbook = corrupt file. Same save/restore
# discipline as Day 17's SP-file handling, baked into syntax.
with xlsxwriter.Workbook(path_excel) as workbook:
    worksheet = workbook.add_worksheet('Sheet_Export')
    bold = workbook.add_format({'bold': True})

    for row_num, row_data in enumerate(data):
        if row_num == 0:
            worksheet.write_row(row_num, 0, row_data, bold)
        else:
            worksheet.write_row(row_num, 0, row_data)


# 5️⃣ Report — same table, in the pyRevit window, plus the filepath
output.print_md('# Excel Smuggler Report (POC)')
output.print_md('- **Sheets exported:** {}'.format(len(all_sheets)))
output.print_md('- **File:** `{}`'.format(path_excel))
output.print_md('---')
output.print_table(table_data=data[1:],
                   columns=headers,
                   title="Exported Sheet List")

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!