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
[FEATURE]
- Replace hardcoded occupancy strings with configurable mapping
- Add parameter existence validation before write
- Add optional UI summary report
- Allow user to select which occupancies to aggregate
- Move aggregation logic into reusable function

[IMPROVEMENT]
- Add StorageType validation before Set()
- Avoid rounding before internal unit conversion
- Add transaction rollback handling
- Optimize for large projects (performance profiling)

[BUG]
- No protection if "Building" or "Flat" parameters are missing
- No validation of output parameter types
________________________________________________________________
Last Updates:
- [02.23.2026] v0.2
  - Added flat-level room counting logic
  - Added occupancy validation with console warnings
  - Improved aggregation structure
  - Writes additional RoomCount parameter
- [02.22.2026] v1.0 Initial proof-of-concept flat aggregation logic
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


# 1️⃣ Get All Rooms
all_rooms = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()

# 2️⃣ Sort Rooms By Apartments
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

# Crate Transaction to Allow API Changes
t = Transaction(doc, 'Flat Summarizer')
t.Start()  # 🔓 Allow Changes

# 3️⃣ Calculate Sums
for key, list_of_rooms in dict_flats.items():

    # SUM/COUNT Placeholders
    SUM_M2_BALCONY = 0.0
    SUM_M2_LIVING = 0.0
    ROOM_COUNT = 0

    # Calculate Sums/Counts
    for room in list_of_rooms:
        occupancy = room.get_Parameter(BuiltInParameter.ROOM_OCCUPANCY).AsString()
        if not occupancy:
            link_room = output.linkify(room.Id)
            print(
                'Room is missing Occupancy parameter for correct calculation. Please verify room: {}'.format(link_room))
            continue

        area_m2 = UnitUtils.ConvertFromInternalUnits(room.Area, UnitTypeId.SquareMeters)
        area_m2 = round(area_m2, 2)

        if occupancy.lower() == 'balcony':
            SUM_M2_BALCONY += area_m2

        elif occupancy.lower() == 'living':
            SUM_M2_LIVING += area_m2

        room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString().lower()
        if 'living' in room_name or 'bed' in room_name:
            ROOM_COUNT += 1

    # Convert SUMS to Internal Units
    sum_ft2_balcony = UnitUtils.ConvertToInternalUnits(SUM_M2_BALCONY, UnitTypeId.SquareMeters)
    sum_ft2_living = UnitUtils.ConvertToInternalUnits(SUM_M2_LIVING, UnitTypeId.SquareMeters)

    # Write Output Values
    for room in list_of_rooms:
        # Get Parameters
        p_out_balcony = room.LookupParameter('[Sum m²] - Balcony')
        p_out_living = room.LookupParameter('[Sum m²] - Living')
        p_out_count = room.LookupParameter('RoomCount')

        # 🚨 Ensure Output Parameters Exist
        if not p_out_living or not p_out_balcony or not p_out_count:
            forms.alert('Rooms missing output parameters [...]', exitscript=True)

        # Write Output Sums
        p_out_living.Set(sum_ft2_living)
        p_out_balcony.Set(sum_ft2_balcony)
        p_out_count.Set(str(ROOM_COUNT))

    print('---')

t.Commit()  # 🔒 Accept Changes

# ███████████████████████████████████████████████████████████████████████████
# Happy Coding!