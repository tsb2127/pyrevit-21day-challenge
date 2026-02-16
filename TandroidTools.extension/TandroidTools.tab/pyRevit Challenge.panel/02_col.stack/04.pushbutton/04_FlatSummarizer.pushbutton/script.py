# -*- coding: utf-8 -*-
__title__   = "04 - Flat Summarizer"

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *

#pyRevit
from pyrevit import forms, script

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document #type:Document
uidoc  = __revit__.ActiveUIDocument          # __revit__ is internal variable in pyRevit
output = script.get_output()                 # pyRevit Output Menu

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
#🤖 Automate Your Boring Work Here


#1️⃣ Get All Rooms
all_rooms = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()

#2️⃣ Sort Rooms By Apartments
from collections import defaultdict
dict_flats = defaultdict(list)

for room in all_rooms:
    #🚨 Verify Parameters Exist!
    try:
        building = room.LookupParameter("Building").AsString()
        flat     = room.LookupParameter("Flat").AsString()
    except:
        forms.alert("Missing Room Parameter ['Building', 'Flat'].\nPlease Verify and try again", exitscript=True)

    if flat:
        key = "{}_{}".format(building, flat)
        dict_flats[key].append(room)


# 🚨 Ensure Apartment-Rooms in Project
if not dict_flats:
    forms.alert("No Apartment Rooms. Please Verify And Try Again", exitscript=True)


# Crate Transaction to Allow API Changes
t = Transaction(doc,'Flat Summarizer')
t.Start()       #🔓 Allow Changes


#3️⃣ Calculate Sums
for key, list_of_rooms in dict_flats.items():

    # SUM/COUNT Placeholders
    SUM_M2_BALCONY = 0.0
    SUM_M2_LIVING  = 0.0
    ROOM_COUNT     = 0

    # Calculate Sums/Counts
    for room in list_of_rooms:
        occupancy = room.get_Parameter(BuiltInParameter.ROOM_OCCUPANCY).AsString()

        #🚨 Skip/Warn Rooms Without Occupancy
        if not occupancy:
            link_room = output.linkify(room.Id)
            print('Room is missing Occupancy parameter for correct calculation. Please verify room: {}'.format(link_room))
            continue
        # PS Technically all rooms need occupancy for certain workflows.
        # e.g. Living/Balcony/Technical/Circulation/Common/Garage...


        # Get Room Area in M2
        area_m2   = UnitUtils.ConvertFromInternalUnits(room.Area, UnitTypeId.SquareMeters)
        area_m2   = round(area_m2, 2)

        # Check Occupancy
        if occupancy.lower() == 'balcony':
            SUM_M2_BALCONY += area_m2

        elif occupancy.lower() == 'living':
            SUM_M2_LIVING += area_m2

        # Count Bedrooms
        room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString().lower()
        if 'living' in room_name or 'bed' in room_name:
            ROOM_COUNT += 1

    # Convert SUMS to Internal Units
    sum_ft2_balcony = UnitUtils.ConvertToInternalUnits(SUM_M2_BALCONY, UnitTypeId.SquareMeters)
    sum_ft2_living  = UnitUtils.ConvertToInternalUnits(SUM_M2_LIVING, UnitTypeId.SquareMeters)

    # Write Output Values
    for room in list_of_rooms:
        # Get Parameters
        p_out_balcony = room.LookupParameter('[Sum m²] - Balcony')
        p_out_living  = room.LookupParameter('[Sum m²] - Living')
        p_out_count   = room.LookupParameter('RoomCount')

        # 🚨 Ensure Output Parameters Exist
        if not p_out_living or not p_out_balcony or not p_out_count:
            forms.alert('Rooms missing output parameters [...]', exitscript=True)

        # Write Output Sums
        p_out_living.Set(sum_ft2_living)
        p_out_balcony.Set(sum_ft2_balcony)
        p_out_count.Set(str(ROOM_COUNT))


t.Commit()      #🔒 Accept Changes

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!






#📦 Variables
uidoc      = __revit__.ActiveUIDocument

#👉 Get Selected Elements
el_ids = uidoc.Selection.GetElementIds()
elems  = [doc.GetElement(el_id) for el_id in el_ids]  # This is List Comprehension

#✂️ Filter Un/Grouped Elements
el_no_group = [el for el in elems if el.GroupId == ElementId.InvalidElementId]
el_group    = [el for el in elems if el.GroupId != ElementId.InvalidElementId]

#🧮 Count Elements
print('Group Elements: {}'.format(el_group))
print('No Group Elements: {}'.format(len(el_no_group)))







