# -*- coding: utf-8 -*-
__title__   = "13 - Floorify"
__doc__     = """Version = 3.0
Date    = 03.15.2026
________________________________________________________________
Description:
Creates floors automatically from room boundaries.

________________________________________________________________
How-To:
1. User selects rooms
2. User selects floor type
3. Script extracts room boundary geometry
4. Boundary curves are converted to CurveLoops
5. Floors are generated on the same level
6. Offset is applied
7. A report is generated in pyRevit output

________________________________________________________________
Last Updates:
- [03.15.2026] v3 Stress Tested
- [03.15.2026] v2 Refactored
- [03.15.2026] v1 Proof of Concept
_______________________________________________________________
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
rvt_year = int(app.VersionNumber)


# ╔═╗╦╔╗╔╔═╗╦    ╔═╗╔═╗╔╦╗╔═╗
# ╠╣ ║║║║╠═╣║    ║  ║ ║ ║║║╣
# ╚  ╩╝╚╝╩ ╩╩═╝  ╚═╝╚═╝═╩╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 🔓 Transaction To Allow Changes
t = Transaction(doc, 'Floorify')
t.Start()  # 🔓


#1️⃣ Select Rooms
from pyrevit import revit
rooms = revit.pick_elements_by_category(BuiltInCategory.OST_Rooms)

#🚨 Ensure Room Bounded
rooms = [room for room in rooms if room.Area]

#🚨 Ensure Rooms
if not rooms:
    forms.alert('No Bounded Rooms Selected. Please Try Again', exitscript=True)

#2️⃣ Select FloorType
# floor_type_id = doc.GetDefaultElementTypeId(ElementTypeGroup.FloorType)
# Prompt User Selection
floor_types   = FilteredElementCollector(doc).OfClass(FloorType).ToElements()
dict_floors   = {Element.Name.GetValue(ft) : ft for ft in floor_types}
selection     = forms.SelectFromList.show(dict_floors.keys(), button_name='Select Floor Type', title='Floorify My Rooms')

#🚨 Ensure FloorType
if not selection:
    forms.alert('No FloorType Selected. Please Try Again', exitscript=True)

#  Get FloorType Based on User Input
floor_type    = dict_floors[selection]
floor_type_id = floor_type.Id


table = []

for room in rooms:
    #3️⃣ Get Room Outline
    opts = SpatialElementBoundaryOptions()
    opts.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish #Choose from (CoreBoundary, CoreCenter, Center, Finish)
    room_boundaries = room.GetBoundarySegments(opts)

    if rvt_year >= 2022:
        #4️⃣ Prepare List[CurveLoop] [RVT22+]
        # Room -> Boundary -> Segment -> Curve -> CurveLoop -> List[CurveLoop]
        curve_loops = []
        for boundary in room_boundaries:
            curve_loop = CurveLoop()
            for seg in boundary:
                curve = seg.GetCurve()
                curve_loop.Append(curve)
            curve_loops.append(curve_loop)

        List_curve_loops = List[CurveLoop](curve_loops)

        #5️⃣ Create Floor (Different in API 21/22)
        level_id = room.LevelId
        new_floor = Floor.Create(doc, List_curve_loops, floor_type_id, level_id)




    elif rvt_year < 2022:
        forms.alert('Revit older than 2022 is not supported. Please contact develooper... ', exitscript=True)

    # Optionally: Change Parameter
    offset_cm = 100
    offset_ft = UnitUtils.ConvertToInternalUnits(offset_cm, UnitTypeId.Centimeters)

    p_offset  = new_floor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)
    p_offset.Set(offset_ft)

    #6️⃣ Create Report
    room_name  = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
    link_room  = output.linkify(room.Id, room_name)
    link_floor = output.linkify(new_floor.Id, new_floor.Name)
    level      = doc.GetElement(level_id)
    area_m2    = UnitUtils.ConvertFromInternalUnits(room.Area, UnitTypeId.SquareMeters )

    data = [link_floor, link_room, area_m2,level.Name, offset_cm]
    table.append(data)

t.Commit()  #🔒


output.print_table(table_data=table,
    title="Floorify Report",
    columns=['Floor', 'Room', 'Area(m2)', 'Level', 'Offset (cm)'])

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
