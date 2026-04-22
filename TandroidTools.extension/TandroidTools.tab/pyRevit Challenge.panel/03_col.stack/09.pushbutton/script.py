# -*- coding: utf-8 -*-
__title__   = "09 - Auto-Planner (POC)"
__doc__     = """Version = 0.1 (Proof of Concept)
Date    = 04.22.2026
________________________________________________________________
Description:
PROOF OF CONCEPT — not a shipping tool yet.

Takes one hard-coded element by ID, creates a new FloorPlan view,
and crops that view to the element's bounding box + a small offset.
Proves the mechanics before we generalize to "do this for every
room in the project" in v1.0.

Teaches: ElementId lookup (with Revit 2025+ Int64 quirk),
BoundingBox math, CropBox activation, internal-unit conversion.
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 9 — POC stage)"""

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
from System import Int64  # Needed for Revit 2025+ ElementId constructor


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()

# Global context
rvt_year    = int(app.VersionNumber)   # e.g., 2024, 2025, 2026
active_view = doc.ActiveView


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

def get_el_by_id(int_id):
    """Look up an element by its integer ID, handling the Revit 2025+
    Int32 → Int64 ElementId constructor change.

    CS note: this function abstracts away a version-compatibility wart
    so the rest of the code doesn't need to care which Revit version
    it's running under. This pattern — wrap the weirdness, expose a
    clean API — is the heart of software engineering.
    """
    if rvt_year > 2024:
        e_id = ElementId(Int64(int_id))
    else:
        e_id = ElementId(int_id)
    return doc.GetElement(e_id)


# ╔═╗╦═╗╔═╗╔═╗╔═╗  ╔═╗╔═╗  ╔═╗╔═╗╔╗╔╔═╗╔═╗╔═╗╔╦╗
# ╠═╝╠╦╝║ ║║ ║╠╣   ║ ║╠╣   ║  ║ ║║║║║  ║╣ ╠═╝ ║
# ╩  ╩╚═╚═╝╚═╝╚    ╚═╝╚    ╚═╝╚═╝╝╚╝╚═╝╚═╝╩   ╩
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Get one hard-coded element (REPLACE THIS ID with one from your model)
# ────────────────────────────────────────────────────────────────
# Right-click a Room (or any element) in Revit and copy its ID into
# the line below. A Room is ideal; a wall/door also works for testing.
TARGET_ID = 829853   # 🔧 REPLACE WITH YOUR OWN ELEMENT ID

element = get_el_by_id(TARGET_ID)
print("Found element:", element)

if element is None:
    forms.alert(
        "No element found with ID {}. Replace TARGET_ID in the script "
        "with a real element ID from your model.".format(TARGET_ID),
        exitscript=True,
    )


# 🔒 Transaction — Revit requires one for any doc modification
t = Transaction(doc, 'Auto-Planner POC')
t.Start()

# 2️⃣ Create a new FloorPlan view
# ────────────────────────────────────────────────────────────────
# To create a view, Revit needs a ViewFamilyType — the "template class"
# that defines what kind of view this is (floor plan vs ceiling plan,
# etc.). GetDefaultElementTypeId is a shortcut that asks the document
# for its default FloorPlan type.
viewFamilyTypeId = doc.GetDefaultElementTypeId(ElementTypeGroup.ViewTypeFloorPlan)

# Create the view scoped to the element's level
new_view = ViewPlan.Create(doc, viewFamilyTypeId, element.LevelId)


# 3️⃣ Build a CropBox around the element's bounding box + offset
# ────────────────────────────────────────────────────────────────
# BoundingBox returns a BoundingBoxXYZ with Min (bottom-left) and
# Max (top-right) corners in model coordinates. We read it FROM THE
# ACTIVE VIEW because BoundingBoxes are view-dependent (they're 2D
# projections of 3D geometry, oriented to the view).
#
# IMPORTANT: Revit's API internally uses FEET for all distances,
# regardless of what your project displays. So "50 cm of padding"
# must be converted to feet before use.
room_bb = element.BoundingBox[active_view]

# Convert 50 cm → feet (Revit's internal unit)
offset_ft = UnitUtils.ConvertToInternalUnits(50, UnitTypeId.Centimeters)

# Build a new BoundingBoxXYZ with the offset applied
# XYZ is Revit's 3D point class. Z=0 here because we don't care about
# vertical extent for a plan view crop.
new_bb = BoundingBoxXYZ()
new_bb.Min = XYZ(room_bb.Min.X - offset_ft, room_bb.Min.Y - offset_ft, 0)
new_bb.Max = XYZ(room_bb.Max.X + offset_ft, room_bb.Max.Y + offset_ft, 0)


# 4️⃣ Apply the crop and polish the view settings
# ────────────────────────────────────────────────────────────────
new_view.CropBoxActive  = True          # enable cropping
new_view.CropBoxVisible = True          # show the crop rectangle in UI
new_view.DetailLevel    = ViewDetailLevel.Fine
new_view.CropBox        = new_bb


# 5️⃣ Commit and report
# ────────────────────────────────────────────────────────────────
t.Commit()

# Create a clickable link in the pyRevit output window so you can
# jump straight to the new view by clicking.
link = output.linkify(new_view.Id, title="Open new view: " + new_view.Name)
print(link)

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!