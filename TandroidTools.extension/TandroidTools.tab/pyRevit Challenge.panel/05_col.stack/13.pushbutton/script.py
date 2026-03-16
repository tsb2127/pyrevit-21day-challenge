# -*- coding: utf-8 -*-
__title__   = "13 - Floorify"
__doc__     = """Version = 1.0
Date    = 03.15.2026
________________________________________________________________
Description:
Creates floors automatically from room boundaries.

________________________________________________________________
How-To:
1. Run the tool from the pyRevit ribbon
2. Select a room in the model
3. The script reads the room boundary
4. A floor is automatically created matching the room outline
5. The created floor is printed in the pyRevit output window

________________________________________________________________
Last Updates:
- [01.01.2026] v1 Proof of Concept
________________________________________________________________
Author: Tanmay Bhalerao (Template by Erik Frits (from LearnRevitAPI.com))"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *

#pyRevit
from pyrevit import forms, script

#.NET Imports
import clr
clr.AddReference('System')
from System.Collections.Generic import List


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document #type:Document
uidoc  = __revit__.ActiveUIDocument          # __revit__ is internal variable in pyRevit
app    = __revit__.Application
output = script.get_output()                 # pyRevit Output Menu


# ╔═╗╦═╗╔═╗╔═╗╔═╗  ╔═╗╔═╗  ╔═╗╔═╗╔╗╔╔═╗╔═╗╔═╗╔╦╗
# ╠═╝╠╦╝║ ║║ ║╠╣   ║ ║╠╣   ║  ║ ║║║║║  ║╣ ╠═╝ ║
# ╩  ╩╚═╚═╝╚═╝╚    ╚═╝╚    ╚═╝╚═╝╝╚╝╚═╝╚═╝╩   ╩
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

#1️⃣ Select Room
from pyrevit import revit
room = revit.pick_element_by_category(BuiltInCategory.OST_Rooms)

#2️⃣ Select FloorType
floor_type_id = doc.GetDefaultElementTypeId(ElementTypeGroup.FloorType)

#3️⃣ Get Room Outline
opts            = SpatialElementBoundaryOptions()
room_boundaries = room.GetBoundarySegments(opts)

#4️⃣ Prepare List[CurveLoop]
# Room -> Boundary -> Segment -> Curve -> CurveLoop -> List[CurveLoop]
curve_loops = []
for boundary in room_boundaries:
    curve_loop = CurveLoop()
    for seg in boundary:
        curve = seg.GetCurve()
        curve_loop.Append(curve)
    curve_loops.append(curve_loop)

List_curve_loops = List[CurveLoop](curve_loops)

#🔓 Transaction To Allow Changes
t = Transaction(doc, 'Floorify')
t.Start()   # 🔓

#5️⃣ Create Floor (Different in API 21/22)
level_id = room.LevelId
new_floor = Floor.Create(doc, List_curve_loops, floor_type_id, level_id)

#6️⃣ Create Report
link_floor = output.linkify(new_floor.Id, new_floor.Name)
print(link_floor)

t.Commit()  #🔒
#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
