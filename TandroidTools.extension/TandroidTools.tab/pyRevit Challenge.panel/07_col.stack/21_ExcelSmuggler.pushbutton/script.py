# -*- coding: utf-8 -*-
__title__   = "21 - Excel Smuggler"
__doc__     = """Version = 1.0
Date    = 06.15.2026
________________________________________________________________
Description:
Round-trips Revit data through Excel. Two modes:

EXPORT - pick a category and the parameters you care about,
         write one .xlsx row per element (first column is the
         ElementId, which is the key used to import back).

IMPORT - pick an edited .xlsx, match each row to its element by
         ElementId, and write the changed parameter values back
         in a single transaction.

Real use: export a door schedule, hand it to a hardware
consultant to fill in a column in Excel, import it back to
update every door at once.
________________________________________________________________
How-To:
1. Click Excel Smuggler, choose Export or Import.
2. EXPORT: pick category, pick parameters, file saves to Documents.
3. Edit the file in Excel. DO NOT change the ElementId column.
4. IMPORT: pick the edited file. Changed values are written back.
________________________________________________________________
Notes:
- The ElementId column is the join key. If it is altered or
  removed, rows can't be matched and will be skipped.
- Read-only parameters (Area, Volume, etc.) export for reference
  but are skipped on import.
- Length/area (Double) values are stored in Revit INTERNAL units
  (feet). Edit those with that in mind, or stick to text columns.
________________________________________________________________
To-Do:
[FEATURE] - Export display-unit values for Doubles with a unit
            label, and convert back on import.
[FEATURE] - Multi-category export across several sheets/tabs.
[FEATURE] - Match by a chosen key column (e.g. Mark) as an
            alternative to ElementId.
________________________________________________________________
Last Updates:
- [06.15.2026] v1.0 Export + import round-trip via ElementId key
- [06.13.2026] v0.1 POC - export sheet list to xlsx
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 21)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script
import os, datetime, traceback

# Bundled-with-pyRevit Excel libraries (IronPython 2 compatible)
import xlsxwriter   # write .xlsx
import xlrd         # read  .xlsx (needs the 1.x build pyRevit ships)

# .NET import for the ElementId Int64 fix (Revit 2025+)
from System import Int64


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()

# Curated set of commonly-scheduled categories. Add to taste.
CATEGORY_OPTIONS = {
    'Doors':                BuiltInCategory.OST_Doors,
    'Windows':              BuiltInCategory.OST_Windows,
    'Walls':                BuiltInCategory.OST_Walls,
    'Rooms':                BuiltInCategory.OST_Rooms,
    'Furniture':            BuiltInCategory.OST_Furniture,
    'Lighting Fixtures':    BuiltInCategory.OST_LightingFixtures,
    'Plumbing Fixtures':    BuiltInCategory.OST_PlumbingFixtures,
    'Mechanical Equipment': BuiltInCategory.OST_MechanicalEquipment,
}


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

def make_element_id(id_value):
    """Build an ElementId from a number, handling the 2025+ Int64 change.
    🎯 Same API-drift shim as Day 9. Try Int64 first, fall back to int."""
    try:
        return ElementId(Int64(int(id_value)))
    except:
        return ElementId(int(id_value))


def read_param_cell(p):
    """Read a parameter into a plain value for an Excel cell.
    Doubles come out in INTERNAL units (feet)."""
    st = p.StorageType
    if st == StorageType.String:
        return p.AsString() or ''
    if st == StorageType.Integer:
        return p.AsInteger()
    if st == StorageType.Double:
        return p.AsDouble()
    if st == StorageType.ElementId:
        eid = p.AsElementId()
        # Revit 2025+ uses .Value (Int64); older uses .IntegerValue
        try:
            return eid.Value
        except:
            return eid.IntegerValue
    return ''


def write_param_from_cell(p, cell_value):
    """Write an Excel cell value back into a parameter. Returns True if
    a change was actually made. Skips read-only and ElementId params."""
    if p.IsReadOnly:
        return False

    st = p.StorageType
    try:
        if st == StorageType.String:
            new = u'{}'.format(cell_value)
            if (p.AsString() or '') != new:
                p.Set(new)
                return True
        elif st == StorageType.Integer:
            new = int(cell_value)
            if p.AsInteger() != new:
                p.Set(new)
                return True
        elif st == StorageType.Double:
            new = float(cell_value)
            # tiny tolerance so float noise doesn't trigger a "change"
            if abs(p.AsDouble() - new) > 1e-9:
                p.Set(new)
                return True
        # ElementId-storage params are identity refs; don't edit from Excel
    except:
        # bad/blank cell for this type: leave the param untouched
        return False
    return False


def collect_instances(bic):
    """All placed instances of a category."""
    return (FilteredElementCollector(doc)
            .OfCategory(bic)
            .WhereElementIsNotElementType()
            .ToElements())


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

mode = forms.alert(
    'What would you like to do?',
    title=__title__,
    options=['Export to Excel', 'Import from Excel'],
)
if not mode:
    forms.alert('Nothing selected. Exiting.', exitscript=True)


# ════════════════════════════════════════════════════════════════
# EXPORT
# ════════════════════════════════════════════════════════════════
if mode == 'Export to Excel':

    # 1️⃣ Pick a category
    cat_label = forms.SelectFromList.show(
        sorted(CATEGORY_OPTIONS.keys()),
        title='Export which category?',
        button_name='Next',
        multiselect=False,
    )
    if not cat_label:
        forms.alert('No category selected. Exiting.', exitscript=True)

    instances = collect_instances(CATEGORY_OPTIONS[cat_label])
    if not instances:
        forms.alert('No "{}" instances in this model.'.format(cat_label),
                    exitscript=True)

    # 2️⃣ Pick parameters (names taken from the first instance)
    sample = instances[0]
    param_names = sorted(set(
        p.Definition.Name for p in sample.Parameters
    ))
    chosen_params = forms.SelectFromList.show(
        param_names,
        title='Which parameters to export?',
        button_name='Export',
        multiselect=True,
    )
    if not chosen_params:
        forms.alert('No parameters selected. Exiting.', exitscript=True)

    # 3️⃣ Build rows: ElementId is column 0 (the join key)
    headers = ['ElementId'] + list(chosen_params)
    rows = []
    for el in instances:
        row = [str(el.Id)]
        for name in chosen_params:
            p = el.LookupParameter(name)
            row.append(read_param_cell(p) if p else '')
        rows.append(row)

    # 4️⃣ Write the xlsx ('wb' binary mode for IronPython)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    safe = cat_label.replace(' ', '_')
    path = os.path.join(os.path.expanduser('~'), 'Documents',
                        'Export_{}_{}.xlsx'.format(safe, ts))

    with xlsxwriter.Workbook(path) as wb:
        ws = wb.add_worksheet(safe[:31])  # Excel sheet-name limit is 31
        bold = wb.add_format({'bold': True})
        ws.write_row(0, 0, headers, bold)
        for i, row in enumerate(rows, start=1):
            ws.write_row(i, 0, row)

    output.print_md('# Excel Smuggler - Export')
    output.print_md('- **Category:** {}'.format(cat_label))
    output.print_md('- **Rows:** {}'.format(len(rows)))
    output.print_md('- **Columns:** {}'.format(', '.join(headers)))
    output.print_md('- **File:** `{}`'.format(path))
    output.print_md('---')
    output.print_md('Edit the file in Excel, then run this tool again in '
                    '**Import** mode. Leave the ElementId column alone.')


# ════════════════════════════════════════════════════════════════
# IMPORT
# ════════════════════════════════════════════════════════════════
else:

    # 1️⃣ Pick the edited file
    path = forms.pick_file(file_ext='xlsx', title='Pick the edited Excel file')
    if not path:
        forms.alert('No file picked. Exiting.', exitscript=True)

    # 2️⃣ Read it (guarding the xlrd-version gotcha)
    try:
        wb = xlrd.open_workbook(path)
    except Exception as e:
        forms.alert(
            'Could not read the .xlsx file.\n\n'
            'If the error mentions "not supported", the bundled xlrd is '
            'a 2.0+ build that only reads old .xls. Re-save as .xls, or '
            'use a pyRevit build with xlrd 1.x.\n\n{}'.format(e),
            exitscript=True,
        )

    sheet = wb.sheet_by_index(0)
    if sheet.nrows < 2:
        forms.alert('The sheet has no data rows.', exitscript=True)

    headers = [sheet.cell_value(0, c) for c in range(sheet.ncols)]

    # 🎯 The join key must be column 0 and named ElementId.
    if not headers or headers[0] != 'ElementId':
        forms.alert(
            'First column must be "ElementId" (the key used to match rows '
            'back to elements). This file does not have it.',
            exitscript=True,
        )

    param_columns = headers[1:]  # everything after the key is a parameter

    # 3️⃣ Write changes back, one transaction
    updated, unchanged, skipped = 0, 0, []

    t = Transaction(doc, 'Excel Smuggler - Import')
    t.Start()

    for r in range(1, sheet.nrows):
        try:
            id_cell = sheet.cell_value(r, 0)
            el = doc.GetElement(make_element_id(id_cell))
            if el is None:
                skipped.append('Row {}: no element for id {}'.format(r, id_cell))
                continue

            row_changed = False
            for c, pname in enumerate(param_columns, start=1):
                p = el.LookupParameter(pname)
                if p is None:
                    continue
                if write_param_from_cell(p, sheet.cell_value(r, c)):
                    row_changed = True

            if row_changed:
                updated += 1
            else:
                unchanged += 1

        except Exception:
            skipped.append('Row {}: {}'.format(r, traceback.format_exc().splitlines()[-1]))

    t.Commit()

    # 4️⃣ Report
    output.print_md('# Excel Smuggler - Import')
    output.print_md('- **File:** `{}`'.format(path))
    output.print_md('- **Elements updated:** {}'.format(updated))
    output.print_md('- **Unchanged:** {}'.format(unchanged))
    output.print_md('- **Skipped:** {}'.format(len(skipped)))
    if skipped:
        output.print_md('---')
        output.print_md('### Skipped rows')
        for line in skipped:
            output.print_md('- {}'.format(line))

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!