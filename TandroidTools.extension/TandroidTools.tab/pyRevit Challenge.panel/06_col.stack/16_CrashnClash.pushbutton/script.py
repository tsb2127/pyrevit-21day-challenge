# -*- coding: utf-8 -*-
__title__   = "16 - Crash-n-Clash"
__doc__     = """Version = 1.0
Date    = 06.13.2026
________________________________________________________________
Description:
Finds clashes between two element categories in the active model.
For every element in category A, checks which elements in
category B physically intersect it, and reports the pairs in a
sortable table with clickable links and the host level.

Uses a two-phase filter: a cheap bounding-box check culls
non-overlapping candidates first, then an exact solid-vs-solid
check confirms real intersections. This is broad-phase ->
narrow-phase collision detection, the same approach game engines
and spatial databases use.

NOTE: This checks within a SINGLE model. For real coordination
across trades (pipes here vs walls in a linked architectural
model, with grouping/status/tolerance), use Navisworks or ACC
Model Coordination. This tool is an in-canvas quick check, not
a replacement for those.
________________________________________________________________
How-To:
1. Click Crash-n-Clash.
2. Read the report. Click any link to zoom to that element.

To check a different pair (e.g. Ducts vs Structural Framing),
change CATEGORY_A and CATEGORY_B at the top of the script.

Category pairs that coexist in one model (good for testing):
  - OST_PipeCurves   vs OST_PipeFitting   (plumbing model)
  - OST_DuctCurves   vs OST_DuctFitting   (mechanical model)
  - OST_Floors       vs OST_Walls         (architectural model)
________________________________________________________________
To-Do:
[FEATURE] - Cross-linked-model clash (pipes here vs walls in a
            linked model). Requires transforming each host
            element's solid into the link's coordinate space via
            the link's inverse transform, then a solid-intersect
            filter inside the link doc. MUST keep a bounding-box
            broad phase (in link space) BEFORE the solid test, or
            it runs for many minutes on models with hundreds of
            host elements. Prototyped and shelved for performance.
[FEATURE] - Category pickers instead of editing constants.
[FEATURE] - Clearance tolerance so touching geometry (a pipe
            resting on a wall) doesn't count as a clash.
[FEATURE] - Export results to Excel (pairs with Day 21).
________________________________________________________________
Last Updates:
- [06.13.2026] v1.0 Two-phase filter + table report + levels
- [05.11.2026] v0.1 POC - Floor vs Wall intersection check
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 16)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script
import traceback


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()

# 🎯 CONFIG-AS-DATA: the two categories to clash-check live here.
# Swap them to check any pairing without touching the logic below.
CATEGORY_A = BuiltInCategory.OST_PipeCurves   # the "host" we loop over
CATEGORY_B = BuiltInCategory.OST_Walls        # what we check against


# ╔═╗╔╦╗╦╔╦╗
# ║╣  ║║║ ║
# ╚═╝═╩╝╩ ╩
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Collect the "A" side (the elements we loop over)
elements_a = (FilteredElementCollector(doc)
              .OfCategory(CATEGORY_A)
              .WhereElementIsNotElementType()
              .ToElements())

if not elements_a:
    forms.alert('No elements found in category A in this model. Walls may '
                'live in a linked model (see To-Do), or change CATEGORY_A.',
                exitscript=True)


# 2️⃣ For each A element, find intersecting B elements
table = []

for elem_a in elements_a:
    try:
        bb = elem_a.get_BoundingBox(None)
        if not bb:
            continue

        # 🔹 QUICK FILTER - cheap bounding-box overlap (broad phase)
        outline = Outline(bb.Min, bb.Max)
        bb_filter = BoundingBoxIntersectsFilter(outline)

        # 🔸 SLOW FILTER - exact solid-vs-solid (narrow phase)
        exact_filter = ElementIntersectsElementFilter(elem_a)

        clashing = (FilteredElementCollector(doc)
                    .OfCategory(CATEGORY_B)
                    .WhereElementIsNotElementType()
                    .WherePasses(bb_filter)
                    .WherePasses(exact_filter)
                    .ToElements())

        # 3️⃣ Build a table row per A element that clashes
        if clashing:
            link_a = output.linkify(elem_a.Id, elem_a.Name)
            links_b = ' '.join(
                output.linkify(b.Id, b.Name) for b in clashing
            )

            try:
                level = doc.GetElement(elem_a.LevelId)
                level_name = level.Name
            except:
                level_name = 'N/A'

            table.append([link_a, links_b, level_name])

    except Exception:
        # Per-element guard: one bad element doesn't kill the report.
        print('Error on element {}:'.format(elem_a.Id))
        print(traceback.format_exc())


# 4️⃣ Report
if not table:
    output.print_md('# Crash-n-Clash Report')
    output.print_md('No clashes found between the two categories. 🎉')
else:
    output.print_table(
        table_data=table,
        title="Crash-n-Clash Report",
        columns=["Element (A)", "Intersecting Elements (B)", "Level"],
    )
    output.print_md('---')
    output.print_md('**{} element(s)** in category A have clashes.'.format(len(table)))

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!