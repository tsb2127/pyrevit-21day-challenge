# -*- coding: utf-8 -*-
__title__   = "04 - Flat Summarizer"
__doc__     = """Version = 1.0
Date    = 02.22.2026
________________________________________________________________
Description:
Groups rooms by Building + Flat parameters and calculates
aggregated area totals for specific room types (Living, Balcony).
Writes the summed values back into shared room parameters:
    - [Sum m²] - Living
    - [Sum m²] - Balcony

Proof-of-concept implementation for flat-level area summarization.

________________________________________________________________
How-To:
1. Ensure Rooms contain:
       - "Building" parameter
       - "Flat" parameter
       - Occupancy (ROOM_OCCUPANCY) properly filled
2. Ensure shared output parameters exist:
       - [Sum m²] - Living
       - [Sum m²] - Balcony
3. Run the tool from pyRevit.
4. Tool groups rooms by Building_Flat key.
5. Living and Balcony areas are summed and written back to all rooms
   belonging to that flat.

________________________________________________________________
To-Do:
[FEATURE]
- Add null-safety for missing parameters
- Add category filters for occupancy types
- Add configurable occupancy mapping (not hardcoded)
- Add reporting UI instead of print()
- Add summary preview before write

[BUG]
- No protection against missing output parameters
- No StorageType validation before Set()
- Assumes AsString() always returns value
- No check for empty Occupancy

________________________________________________________________
Last Updates:
- [01.01.2026] v1.0 Initial proof-of-concept flat aggregation logic
________________________________________________________________
Author: Tanmay Bhalerao (from Erik Frit's template @ LearnRevitAPI.com)"""

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

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░


#1️⃣ Get All Rooms
all_rooms = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()

#2️⃣ Sort Rooms By Apartments
from collections import defaultdict
dict_flats = defaultdict(list)

for room in all_rooms:
    # Get Parameters
    p_building = room.LookupParameter("Building")
    p_flat     = room.LookupParameter("Flat")

    # Reading Parameter Values
    building = p_building.AsString()
    flat     = p_flat.AsString()

    if flat:
        key = "{}_{}".format(building, flat)
        dict_flats[key].append(room)

# Preview
# for k,v in dict_flats.items():
#     print(k, v)


# Crate Transaction to Allow API Changes
t = Transaction(doc,'Flat Summarizer')
t.Start()       #🔓 Allow Changes


#3️⃣ Calculate Sums
for key, list_of_rooms in dict_flats.items():
    sum_m2_balcony = 0
    sum_m2_living  = 0

    # DEV: Skip All Flats but one
    # if '100' not in key:
    #     continue

    for room in list_of_rooms:
        occupancy = room.get_Parameter(BuiltInParameter.ROOM_OCCUPANCY).AsString()
        area_m2   = UnitUtils.ConvertFromInternalUnits(room.Area, UnitTypeId.SquareMeters)
        area_m2   = round(area_m2, 2)

        if occupancy.lower() == 'balcony':
            sum_m2_balcony += area_m2

        elif occupancy.lower() == 'living':
            sum_m2_living += area_m2


    print('Living: {}m2'.format(sum_m2_living))
    print('Balcon: {}m2'.format(sum_m2_balcony))

    sum_ft2_balcony = UnitUtils.ConvertToInternalUnits(sum_m2_balcony, UnitTypeId.SquareMeters)
    sum_ft2_living  = UnitUtils.ConvertToInternalUnits(sum_m2_living, UnitTypeId.SquareMeters)


    for room in list_of_rooms:
        p_out_balcony = room.LookupParameter('[Sum m²] - Balcony')
        p_out_living  = room.LookupParameter('[Sum m²] - Living')

        p_out_living.Set(sum_ft2_living)
        p_out_balcony.Set(sum_ft2_balcony)

    print('---')

t.Commit()      #🔒 Accept Changes


#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
