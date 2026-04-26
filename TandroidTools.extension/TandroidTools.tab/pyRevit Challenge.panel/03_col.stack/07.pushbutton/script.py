# -*- coding: utf-8 -*-
__title__   = "07 - Tagless Shame List (POC)"
__doc__     = """Version = 0.1 (Proof of Concept)
Date    = 04.26.2026
________________________________________________________________
Description:
PROOF OF CONCEPT — single category, single view.

Looks at the active view, finds every Door, finds every Door Tag,
and reports Doors that don't have a tag pointing at them. Output
is a clickable list — click an item to jump to that door in Revit.

Teaches: FilteredElementCollector view-scoping, the set-difference
pattern (all - tagged = untagged), Tag.GetTaggedLocalElementIds().
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 7 — POC stage)"""

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

# 1️⃣ Get the active view (POC scope)
active_view = doc.ActiveView


# 2️⃣ Get all Doors and all Door Tags in this view
# ────────────────────────────────────────────────────────────────
# FilteredElementCollector(doc, view.Id) scopes the search to a
# specific view — same primitive we used on Day 9. Always prefer
# view-scoped collectors when the user means "in this view"; project-
# wide collectors are slower and often return things the user can't
# even see, which makes the result confusing.
all_doors = FilteredElementCollector(doc, active_view.Id)\
    .OfCategory(BuiltInCategory.OST_Doors)\
    .WhereElementIsNotElementType()\
    .ToElements()

all_door_tags = FilteredElementCollector(doc, active_view.Id)\
    .OfCategory(BuiltInCategory.OST_DoorTags)\
    .WhereElementIsNotElementType()\
    .ToElements()


# 3️⃣ Find untagged doors
# ────────────────────────────────────────────────────────────────
# 🎯 CS PATTERN: set difference.
#
# We have two collections: all doors, and all tags pointing at doors.
# We want: doors that aren't pointed at by any tag.
#
# The math:    untagged = all_doors - tagged_doors
#
# Step 1: ask each tag "which door do you point at?" and collect
#         all the answers. tag.GetTaggedLocalElementIds() returns
#         the IDs of elements that this tag is tagging. (Plural
#         because multi-leader tags can point at multiple elements.)
#
# Step 2: filter all_doors down to ones whose ID isn't in the
#         "tagged" pile.
tagged_door_ids = [
    door_id
    for tag in all_door_tags
    for door_id in tag.GetTaggedLocalElementIds()
]

untagged_doors = [
    door for door in all_doors
    if door.Id not in tagged_door_ids
]


# 4️⃣ Print the report
# ────────────────────────────────────────────────────────────────
print('Total doors in view: {}'.format(len(all_doors)))
print('Total door tags in view: {}'.format(len(all_door_tags)))
print('Total UNTAGGED doors: {}\n'.format(len(untagged_doors)))
print('=' * 50)

if not untagged_doors:
    print('\nAll doors in this view are tagged. Nicely done.')
else:
    for door in untagged_doors:
        link = output.linkify(door.Id, door.Name)
        print(link)

#███████████████