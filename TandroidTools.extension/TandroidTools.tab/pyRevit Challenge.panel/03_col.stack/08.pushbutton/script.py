# -*- coding: utf-8 -*-
__title__   = "08 - Warnings Snitch"
__doc__     = """Version = 1.0
Date    = 04.26.2026
________________________________________________________________
Description:
Pulls every warning in the project, groups them by description,
lets the user pick which warning types to investigate, and
generates an interactive report with clickable selection buttons,
element counts, categories, and levels for each warning.

Replaces Revit's painful native warnings dialog (which doesn't
let you click through to the offending elements) with a one-click
audit tool that BIM coordinators can run before issuing models.
________________________________________________________________
How-To:
1. Click Warnings Snitch.
2. Tool reads all warnings, groups them by description.
3. Pick which warning types to investigate from the list.
4. Review the interactive table — click "Select Elements" to
   navigate to the offending elements in Revit.
________________________________________________________________
To-Do:
[FEATURE] - Sort table by warning count (descending) by default
[FEATURE] - Add a "Select All" / "Select None" shortcut to the
            warning type picker
[FEATURE] - Optional: export the report to CSV/Excel
[CLEANUP] - Truncated description ('...') loses info; consider
            tooltip or full text on hover
________________________________________________________________
Last Updates:
- [04.20.2026] v1.0 Group-by + UI form + interactive report
- [04.20.2026] v0.1 POC — flat list of warnings with linkify
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 8)"""

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

from collections import defaultdict


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()


# ╔═╗╦═╗╔═╗╔═╗╔═╗╔═╗╔═╗
# ╠═╝╠╦╝║ ║║  ║╣ ╚═╗╚═╗
# ╩  ╩╚═╚═╝╚═╝╚═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Get all warnings in the project
# ────────────────────────────────────────────────────────────────
all_warnings = doc.GetWarnings()


# 2️⃣ Group warnings by description
# ────────────────────────────────────────────────────────────────
# 🎯 CS PATTERN: group-by (same as Day 9's apartment grouping).
# 200 individual "Wall slightly off-axis" warnings collapse into
# one bucket so the user sees ONE row per warning type, not 200.
sorted_warnings = defaultdict(list)
for warn in all_warnings:
    desc = warn.GetDescriptionText()
    sorted_warnings[desc].append(warn)


# 🚨 Guard: ensure there are warnings to work with
if not sorted_warnings:
    forms.alert('WOW! No warnings in the project — keep it this way.', exitscript=True)


# 3️⃣ UI Form: let user pick which warning types to investigate
# ────────────────────────────────────────────────────────────────
# On big projects there can be 50+ warning types and thousands of
# instances. Showing all of them produces an unusable table. Asking
# the user to filter first keeps the report focused.
#
# 🎯 CS PATTERN: faceted filtering. Same idea as Amazon's left-rail
# checkboxes, Gmail's label filters, IDE search scope dropdowns.
# Always offer the user an upstream filter when the dataset is big.
sel_warn_names = forms.SelectFromList.show(
    sorted(sorted_warnings.keys()),
    button_name='Select',
    multiselect=True,
    title='Select Warning Types',
)

# 🚨 Guard: ensure user actually picked something
if not sel_warn_names:
    forms.alert('No Warning Types Selected.\nPlease Try Again...', exitscript=True)


# 4️⃣ Build the report data
# ────────────────────────────────────────────────────────────────
table_data = []

for warn_desc, list_warn in sorted_warnings.items():

    # Skip warning types the user didn't select
    if warn_desc not in sel_warn_names:
        continue

    for warn in list_warn:

        # Combine failing + additional elements (defensive — see
        # Day 8 POC notes for why we always combine both)
        fail_el_ids = warn.GetFailingElements()
        add_el_ids  = warn.GetAdditionalElements()
        warn_el_ids = list(fail_el_ids) + list(add_el_ids)
        warn_el     = [doc.GetElement(e_id) for e_id in warn_el_ids]

        # Get unique categories involved.
        # 🎯 CS PATTERN: set comprehension. {x for x in ...} builds
        # a set, which automatically de-duplicates. Three walls in
        # one warning would otherwise show "Walls,Walls,Walls" — the
        # set collapses that to just "Walls".
        # Guard: skip elements without a Category (e.g., model lines
        # in some contexts have no Category and would crash on .Name)
        cats = {el.Category.Name for el in warn_el if el is not None and el.Category is not None}
        cats = ', '.join(sorted(cats))

        # Get unique levels involved.
        # Same defensive pattern: only read LevelId if it exists and
        # is valid. Many Revit elements (sheets, types, system
        # families) have no Level.
        levels = set()
        for el in warn_el:
            if el is None:
                continue
            try:
                if el.LevelId and el.LevelId != ElementId.InvalidElementId:
                    lvl = doc.GetElement(el.LevelId)
                    if lvl:
                        levels.add(lvl.Name)
            except AttributeError:
                # Element type doesn't have a LevelId property — skip
                pass
        levels = ', '.join(sorted(levels))

        # Build the linkify selection button
        link = output.linkify(warn_el_ids, "Select")

        # Truncate the description so the table column doesn't blow up
        short_desc = warn_desc if len(warn_desc) <= 60 else warn_desc[:60] + '...'

        table_data.append([
            short_desc,
            link,
            len(warn_el_ids),
            cats,
            levels,
        ])


# 5️⃣ Print the interactive report
# ────────────────────────────────────────────────────────────────
output.print_table(
    table_data = table_data,
    title      = 'The Warnings Snitch Report',
    columns    = ['Warning Type', 'Select', 'Count', 'Categories', 'Levels'],
)

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!