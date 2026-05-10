# -*- coding: utf-8 -*-
__title__   = "Workset Grabber"
__doc__     = """Version = 2.0
Date    = 05.10.2026
________________________________________________________________
Description:
Pick one or more worksets, get every element on those worksets
selected in Revit's UI. Skips Type definitions and view-specific
elements so the selection only contains modeled instances.

Real use: bulk-edit by workset (e.g., move all "Existing" 
elements to a new phase, isolate "Site" elements for a
landscape review, audit "Architecture" element counts).
________________________________________________________________
How-To:
1. Click Workset Grabber.
2. Pick one or more worksets from the list.
3. Tool selects all matching elements in Revit's UI.
4. Optional: pair with a follow-up action (move, edit, tag).
________________________________________________________________
To-Do:
[FEATURE] - Optional category filter (e.g., "all Walls on the
            Architecture workset" not just "all elements")
[FEATURE] - Save the selection as a SelectionSet for later reuse
[FEATURE] - Optional: scope to "in active view" vs whole project
________________________________________________________________
Last Updates:
- [05.10.2026] v2 Composite filter + defensive guards + report
- [03.17.2026] v1 POC — basic per-workset accumulator
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 15)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script

# .NET Imports
import clr
clr.AddReference('System')
from System.Collections.Generic import List


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()


# ╔═╗╦═╗╔═╗╔═╗╔═╗  ╔═╗╔═╗  ╔═╗╔═╗╔╗╔╔═╗╔═╗╔═╗╔╦╗
# ╠═╝╠╦╝║ ║║ ║╠╣   ║ ║╠╣   ║  ║ ║║║║║  ║╣ ╠═╝ ║
# ╩  ╩╚═╚═╝╚═╝╚    ╚═╝╚    ╚═╝╚═╝╝╚╝╚═╝╚═╝╩   ╩
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 🚨 Guard #1: workshared model required
# Worksets only exist in workshared models. Bail clean if the
# active doc isn't workshared.
if not doc.IsWorkshared:
    forms.alert(
        'This project is not workshared.\n\n'
        'Workset tools only apply to multi-user workshared models. '
        'Open a workshared project and try again.',
        exitscript=True,
    )


# 1️⃣ Collect all user-defined worksets
# WorksetKind.UserWorkset filters out the system worksets
# (Views, Families, Project Standards) that the user can't
# meaningfully assign elements to.
worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets()
dict_worksets = {w.Name: w for w in worksets}

if not dict_worksets:
    forms.alert(
        'No user worksets found in this project. There must be at '
        'least one user workset to use this tool.',
        exitscript=True,
    )


# 2️⃣ User picks which worksets to grab from
sel_workset_names = forms.SelectFromList.show(
    sorted(dict_worksets.keys()),
    title='Select Workset(s) to Grab',
    button_name='Grab Elements',
    multiselect=True,
)

# 🚨 Guard #2: ensure user selected something
if not sel_workset_names:
    forms.alert('No worksets selected.\nPlease try again.', exitscript=True)

sel_worksets = [dict_worksets[name] for name in sel_workset_names]


# 3️⃣ Build the composite filter and query the model
# 🎯 CS PATTERN: filter composition with logical OR.
# Build one filter per workset, then combine into a single
# LogicalOrFilter. The final query runs the model walk ONCE
# and lets each element through if it passes ANY of the
# component filters. Far faster than walking once per workset.
list_workset_filters = [ElementWorksetFilter(w.Id) for w in sel_worksets]
wk_filter = LogicalOrFilter(list_workset_filters)

# 🎯 CS PATTERN: narrow the query before it runs.
# WhereElementIsNotElementType: drops Type definitions
# (WallType, FloorType, etc.) — we only want placed instances.
# WhereElementIsViewIndependent: drops view-specific things
# (tags, dimensions, detail lines on individual views).
el_ids = (FilteredElementCollector(doc)
          .WhereElementIsNotElementType()
          .WhereElementIsViewIndependent()
          .WherePasses(wk_filter)
          .ToElementIds())

# 🚨 Guard #3: ensure we found something
if not el_ids:
    forms.alert(
        'No elements found on the selected workset(s).\n'
        'They may be empty or contain only view-specific elements.',
        exitscript=True,
    )


# 4️⃣ Update Revit's UI selection
# 🎯 .NET-Python bridge: SetElementIds expects List[ElementId],
# not a Python list. Same conversion pattern from Day 6.
List_el_ids = List[ElementId](el_ids)
uidoc.Selection.SetElementIds(List_el_ids)


# 5️⃣ Report
output.print_md('# Workset Grabber Report')
output.print_md('- **Worksets selected:** {}'.format(len(sel_worksets)))
for name in sorted(sel_workset_names):
    output.print_md('  - {}'.format(name))
output.print_md('- **Elements grabbed:** {}'.format(len(el_ids)))
output.print_md('---')
output.print_md(
    "All matching elements are now selected in Revit. Use any "
    "Modify-tab tool, the Properties panel, or pyRevit's selection "
    "shortcuts to act on them."
)

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!