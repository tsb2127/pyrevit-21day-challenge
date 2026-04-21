# -*- coding: utf-8 -*-
__title__   = "10 - Lazy Sheets"
__doc__     = """Version = 1.0
Date    = 04.19.2026
________________________________________________________________
Description:
Select unplaced views and a titleblock, and this tool creates a
new sheet for each view with the view auto-centered on the sheet.
Reports everything in an interactive table with clickable links
to each sheet and view.

Solves the "I need to create 50 sheets and place views on them"
problem that otherwise takes an hour of repetitive clicking.
________________________________________________________________
How-To:
1. Click the Lazy Sheets button.
2. Select the views you want placed on sheets (only unplaced
   views appear in the list — placed ones are filtered out).
3. Select a titleblock from the list.
4. Wait for the progress bar (or cancel to roll back).
5. Review the interactive report of created sheets.
________________________________________________________________
To-Do:
[FEATURE] - Auto-assign sheet numbers/names from view name
[FEATURE] - Support placing multiple views per sheet
[BUG]     - No viewports/sheets in project causes silent fail
________________________________________________________________
Last Updates:
- [04.19.2026] v1.0 Initial working version
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 10)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script
from pyrevit.forms import ProgressBar


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

def is_unplaced(view):
    """Filter function passed to pyrevit.forms.select_views.
    Returns True only for views that are eligible to be placed on a new sheet."""
    all_viewports = FilteredElementCollector(doc).OfClass(Viewport).ToElements()
    random_sheet_id = FilteredElementCollector(doc).OfClass(ViewSheet).FirstElementId()

    placed_view_ids = [vp.ViewId for vp in all_viewports]
    if not Viewport.CanAddViewToSheet(doc, random_sheet_id, view.Id):
        return False

    if view.Id not in placed_view_ids and not view.IsTemplate:
        return True


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Select Unplaced Views
views = forms.select_views(title='Select Views To Place On Sheets', filterfunc=is_unplaced)

if not views:
    forms.alert('No Views Selected. Please Try Again', exitscript=True)

# 2️⃣ Select TitleBlock
tb_id = forms.select_titleblocks(title='Select TitleBlock for New Sheets')

if not tb_id:
    forms.alert('No TitleBlock Selected. Please Try Again', exitscript=True)

# 🔒 Transaction — Revit requires one for any document modification
t = Transaction(doc, 'py-Lazy Sheets')
t.Start()

with forms.ProgressBar(cancellable=True) as pb:

    table_data = []
    n_views = len(views)
    tb = None  # cache the titleblock so we only fetch it once

    for n, view in enumerate(views):

        # 3️⃣ Create New Sheet
        new_sheet = ViewSheet.Create(doc, tb_id)

        # 4️⃣ Find titleblock centroid (only compute once — it's the same per TB type)
        if not tb:
            tb = FilteredElementCollector(doc, new_sheet.Id)\
                .OfCategory(BuiltInCategory.OST_TitleBlocks)\
                .WhereElementIsNotElementType()\
                .FirstElement()
            bb = tb.BoundingBox[new_sheet]
            centroid = (bb.Min + bb.Max) / 2

        # Place the view at centroid
        new_viewport = Viewport.Create(doc, new_sheet.Id, view.Id, centroid)

        # 5️⃣ Build report row (clickable links in the output)
        sheet_name = '{} - {}'.format(new_sheet.SheetNumber, new_sheet.Name)
        link_sheet = output.linkify(new_sheet.Id, sheet_name)
        link_view  = output.linkify(view.Id, view.Name)

        view_template_id = view.ViewTemplateId
        if view_template_id == ElementId.InvalidElementId:
            vt_name = '-'
        else:
            view_template = doc.GetElement(view_template_id)
            vt_name = view_template.Name

        table_data.append([link_sheet, link_view, view.ViewType, view.Scale, view.DetailLevel, vt_name])

        # Handle user cancellation gracefully
        if pb.cancelled:
            t.RollBack()
            forms.alert('Lazy Sheets Cancelled. No changes applied.', exitscript=True)
            break
        else:
            pb.update_progress(n, n_views)

# Show Final Report
output.print_table(
    table_data = table_data,
    columns    = ['Sheet', 'View', 'ViewType', 'Scale', 'DetailLevel', 'Template'],
    title      = 'Lazy Sheets Report'
)

t.Commit()

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!