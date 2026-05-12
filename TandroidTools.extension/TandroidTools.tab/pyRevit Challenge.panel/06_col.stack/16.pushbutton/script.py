# -*- coding: utf-8 -*-
__title__   = "16 - Crash-n-Clash (POC)"
__doc__     = """Version = 0.1 (Proof of Concept)
Date    = 05.11.2026
________________________________________________________________
Description:
POC — Hardcoded clash check.
Walks every Floor in the project, asks Revit "what Walls
physically intersect this floor?", prints clickable links to
each clashing pair.

Read-only — no transactions, no modifications.

V1 will: let user pick the two categories, use bounding-box
filtering for performance, render results in a sortable table,
and group pairs by the host element.
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 16 — POC)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script


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

# 1️⃣ Collect the "A" side of the clash check
# Floors are a great test case in Snowdon Towers — lots of them,
# and lots of walls that punch through them at level transitions.
all_floors = (FilteredElementCollector(doc)
              .OfCategory(BuiltInCategory.OST_Floors)
              .WhereElementIsNotElementType()
              .ToElements())

print("Found {} floors in the project.".format(len(all_floors)))


# 2️⃣ For each floor, find intersecting walls
# 🎯 CS PATTERN: nested-loop pairwise comparison, O(N×M).
# Outer loop: every floor. Inner "loop" is hidden inside the
# filter — Revit walks every wall in the project, asks each one
# "do you intersect this floor?", returns the matches.
#
# 🎯 CS PATTERN: slow geometric filter.
# ElementIntersectsElementFilter does exact solid-vs-solid math.
# Accurate but slow. V1 should pre-filter with bounding-boxes
# to avoid checking every floor against every wall.
clash_count = 0

for floor in all_floors:

    # Build a filter that says "intersects THIS specific floor"
    floor_filter = ElementIntersectsElementFilter(floor)

    # Run the model walk: every wall, filtered by intersection
    clashing_wall_ids = (FilteredElementCollector(doc)
                         .OfCategory(BuiltInCategory.OST_Walls)
                         .WhereElementIsNotElementType()
                         .WherePasses(floor_filter)
                         .ToElementIds())

    # 3️⃣ Print clickable links for each clash
    if clashing_wall_ids:
        floor_link = output.linkify(floor.Id, "Floor {}".format(floor.Id))
        wall_links = [output.linkify(wall_id, "Wall {}".format(wall_id))
                      for wall_id in clashing_wall_ids]

        print("{}  clashes with:  {}".format(floor_link, ", ".join(wall_links)))
        clash_count += len(clashing_wall_ids)


# 4️⃣ Summary
print("\n" + "=" * 60)
print("Total clash pairs found: {}".format(clash_count))

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!