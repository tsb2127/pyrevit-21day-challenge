# -*- coding: utf-8 -*-
__title__   = "09 - Auto-Planner"
__doc__     = """Version = 1.0
Date    = 04.22.2026
________________________________________________________________
Description:
Generates one cropped floor plan view per apartment by grouping
rooms using the 'Department' parameter. For every apartment
(e.g., all rooms tagged 'APT-101'), creates a new FloorPlan view
cropped tightly around the union of that apartment's rooms, with
a 50 cm border. Outputs an interactive report with links to each
view and selection of each apartment's rooms.

Real-world use: apartment buildings / residential developments
where sales teams or clients need individual unit plans. Manually
making 50–1500 of these is a multi-day task; this tool runs in
seconds.

Teaches: group-by pattern, reduce pattern (bounding box union),
Revit 2025+ ElementId quirk, parameter-driven workflows.
________________________________________________________________
How-To:
1. Click Auto-Planner.
2. Tool reads every Room, groups by Department parameter.
3. For each apartment group, a new FloorPlan view is created
   and cropped to fit all its rooms.
4. Report opens with clickable links to each view and apartment.
________________________________________________________________
To-Do:
[FEATURE] - Let user choose which parameter to group by (not
            always 'Department')
[FEATURE] - Apply a View Template to new views automatically
[FEATURE] - Add progress bar — this tool can take a while on
            large projects
[CLEANUP] - create_combined_BB implicitly depends on new_view
            from outer scope; should accept it as an argument
________________________________________________________________
Last Updates:
- [04.19.2026] v1.0 Full apartment-grouped auto-planner
- [04.19.2026] v0.1 POC — single-element view cropping
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 9)"""

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
from System import Int64   # For Revit 2025+ ElementId(Int64) constructor

from collections import defaultdict


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()

# Global context
rvt_year    = int(app.VersionNumber)
active_view = doc.ActiveView
offset_ft   = UnitUtils.ConvertToInternalUnits(50, UnitTypeId.Centimeters)


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

def get_el_by_int_id(id_int):
    """Look up an element by integer ID, handling the Revit 2025+
    Int32 → Int64 ElementId constructor change."""
    if rvt_year > 2025:
        elem_id = ElementId(Int64(id_int))
    else:
        elem_id = ElementId(id_int)
    return doc.GetElement(elem_id)


def get_sorted_app_rooms():
    """Collect all Rooms and GROUP them by their Department parameter.
    Returns: {apartment_id_string: [list_of_room_objects]}

    🎯 CS PATTERN: group-by.
    Same mental model as SQL 'GROUP BY Department' or pandas
    df.groupby('Department'). We walk every row (room), bucket it
    by key (department), and end up with one bucket per apartment.

    🎯 CS PATTERN: defaultdict(list).
    Instead of checking 'does this key exist yet?' on every
    iteration, defaultdict auto-creates an empty list the first
    time we touch a new key. Shorter, faster, and harder to bug.
    """
    all_rooms = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_Rooms)\
        .ToElements()

    f_dict_apps = defaultdict(list)

    for room in all_rooms:
        p_dept = room.get_Parameter(BuiltInParameter.ROOM_NAME)
        dept   = p_dept.AsString()

        # Guard: skip unplaced rooms (Area == 0) and rooms with no
        # Department value. A placed room always has Area > 0.
        if dept and room.Area:
            f_dict_apps[dept].append(room)

    return f_dict_apps


def create_combined_BB(f_list_rooms):
    """Given a list of rooms, return a single BoundingBoxXYZ that
    encloses ALL of them, plus the global offset.

    🎯 CS PATTERN: reduce.
    We start with extreme seed values (+infinity for min, -infinity
    for max — we use 1,000,000 ft and -1,000,000 ft as good-enough
    stand-ins since Revit projects aren't that big). Then we walk
    every room and pull the seed toward its actual bounds. After
    one pass, the seeds hold the true overall extents.

    ⚠️ This function captures `new_view` and `offset_ft` from the
    outer scope — it only works when called from inside the main
    loop below where `new_view` is defined. A cleaner V2 would
    pass both in as arguments.
    """
    BB_min = [1000000, 1000000, 0]
    BB_max = [-1000000, -1000000, 0]

    # Read each room's bounding box AS SEEN from the new view
    list_BB = [room.BoundingBox[new_view] for room in f_list_rooms]

    for BB in list_BB:
        if BB.Min.X < BB_min[0]: BB_min[0] = BB.Min.X
        if BB.Min.Y < BB_min[1]: BB_min[1] = BB.Min.Y
        if BB.Max.X > BB_max[0]: BB_max[0] = BB.Max.X
        if BB.Max.Y > BB_max[1]: BB_max[1] = BB.Max.Y

    new_BB = BoundingBoxXYZ()
    new_BB.Min = XYZ(BB_min[0] - offset_ft, BB_min[1] - offset_ft, 0)
    new_BB.Max = XYZ(BB_max[0] + offset_ft, BB_max[1] + offset_ft, 0)
    return new_BB


# ╔═╗╦═╗╔═╗╔═╗╔═╗╔═╗╔═╗
# ╠═╝╠╦╝║ ║║  ║╣ ╚═╗╚═╗
# ╩  ╩╚═╚═╝╚═╝╚═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Get rooms, grouped by apartment
dict_apps = get_sorted_app_rooms()

if not dict_apps:
    forms.alert(
        'No placed rooms with a Name value found.',
        exitscript=True,
    )


# 🔒 Transaction — Revit requires one for any doc modification
t = Transaction(doc, 'Auto-Planner')
t.Start()

table_data = []

# Iterate through each apartment group
for app_number, list_rooms in dict_apps.items():

    # 2️⃣ Create a new FloorPlan for this apartment
    #    All rooms in an apartment share a level, so we grab the
    #    first room's level and use it for the new view.
    room = list_rooms[0]
    viewFamilyTypeId = doc.GetDefaultElementTypeId(ElementTypeGroup.ViewTypeFloorPlan)
    new_view = ViewPlan.Create(doc, viewFamilyTypeId, room.LevelId)

    # 3️⃣ Compute the combined bounding box of all rooms in this apartment
    new_BB = create_combined_BB(list_rooms)

    # 4️⃣ Apply the crop
    new_view.CropBox        = new_BB
    new_view.CropBoxVisible = True
    new_view.CropBoxActive  = True

    # 5️⃣ Build the report row
    #    linkify can take either a single ElementId (to navigate to
    #    a view) or a list of ElementIds (to select those elements).
    room_ids   = [r.Id for r in list_rooms]
    link_rooms = output.linkify(room_ids, "Select {} Rooms".format(len(room_ids)))
    link_view  = output.linkify(new_view.Id, new_view.Name)

    # Sum the apartment's total area, converted to square meters
    total_m2 = 0
    for r in list_rooms:
        m2 = UnitUtils.ConvertFromInternalUnits(r.Area, UnitTypeId.SquareMeters)
        total_m2 += round(m2, 2)

    table_data.append([app_number, link_view, link_rooms, total_m2])

t.Commit()


# 6️⃣ Interactive report
output.print_table(
    table_data = table_data,
    title      = "Auto-Planner Report",
    columns    = ['Unit Type', 'New View', 'Rooms', 'Total Area m²'],
    formats    = ['**{}**', '', '', '{}m²'],
)

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!