# -*- coding: utf-8 -*-
__title__   = "14 - Workset Police"
__doc__     = """Version = 1.0
Date    = 03.16.2026
________________________________________________________________
Description:
Automatically assigns model elements to correct worksets based on predefined category rules.

________________________________________________________________
How-To:
1. Ensure correct worksets exist (Architecture, Structure, MEP, Group)
2. Click the tool
3. Elements will be reassigned automatically

Notes:
- Only affects instance elements (not types)
- Skips elements without workset parameter

________________________________________________________________
Last Updates:
- [03.16.2026] v0 Proof of Concept

________________________________________________________________
Author: Erik Frits (from LearnRevitAPI.com)"""

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


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

def change_worksets(elements, target_workset):
    """Function to Set Target Workset to given elements."""

    for el in elements:
        # GroupId
        # Worksharing (taken or not)

        try:
            # Get Workset Parameter
            param_workset = el.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM)

            # Get Workset Ids (as int)
            current_workset_id = param_workset.AsInteger()
            target_workset_id = target_workset.Id.IntegerValue

            # Write Workset Id (If necessary)
            if current_workset_id != target_workset_id:
                param_workset.Set(target_workset_id)

        except:
            pass
            # print(el.Id)


# ╔═╗╦═╗╔═╗╔═╗╔═╗  ╔═╗╔═╗  ╔═╗╔═╗╔╗╔╔═╗╔═╗╔═╗╔╦╗
# ╠═╝╠╦╝║ ║║ ║╠╣   ║ ║╠╣   ║  ║ ║║║║║  ║╣ ╠═╝ ║
# ╩  ╩╚═╚═╝╚═╝╚    ╚═╝╚    ╚═╝╚═╝╝╚╝╚═╝╚═╝╩   ╩
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

#1️⃣ Worksets & Containers
# CONTAINERS
ARC_ELEMENTS = []
STR_ELEMENTS = []
MEP_ELEMENTS = []
GROUPS       = FilteredElementCollector(doc).OfClass(Group).ToElements()

# WORKSETS
worksets      = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets()
workset_arc   = [w    for w in worksets       if 'architecture' in w.Name.lower()][0]
workset_str   = [w    for w in worksets       if 'structure'    in w.Name.lower()][0]
workset_mep   = [w    for w in worksets       if 'mep'          in w.Name.lower()][0]
workset_group = [w    for w in worksets       if 'group'        in w.Name.lower()][0]

#2️⃣ Workset - Category Rules

# ARCHITECTURE
ARC_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType().ToElements())
ARC_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType().ToElements())
ARC_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture).WhereElementIsNotElementType().ToElements())
ARC_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_FurnitureSystems).WhereElementIsNotElementType().ToElements())
ARC_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Casework).WhereElementIsNotElementType().ToElements())
ARC_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Railings).WhereElementIsNotElementType().ToElements())
ARC_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StairsRailing).WhereElementIsNotElementType().ToElements())
ARC_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RailingSystem).WhereElementIsNotElementType().ToElements())
ARC_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Stairs).WhereElementIsNotElementType().ToElements())
ARC_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MultistoryStairs).WhereElementIsNotElementType().ToElements())
ARC_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_LightingFixtures).WhereElementIsNotElementType().ToElements())

# STRUCTURE
STR_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralFraming).WhereElementIsNotElementType().ToElements())
STR_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralColumns).WhereElementIsNotElementType().ToElements())
STR_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Columns).WhereElementIsNotElementType().ToElements())
STR_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralFoundation).WhereElementIsNotElementType().ToElements())

# MEP
MEP_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ElectricalFixtures).WhereElementIsNotElementType().ToElements())
MEP_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ElectricalEquipment).WhereElementIsNotElementType().ToElements())
MEP_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures).WhereElementIsNotElementType().ToElements())
MEP_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingEquipment).WhereElementIsNotElementType().ToElements())
MEP_ELEMENTS += list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MechanicalEquipment).WhereElementIsNotElementType().ToElements())


#🔓 Transaction to Allow Changes
with Transaction(doc,'Workset Police') as t:
    t.Start()

    # 3️⃣ Change Worksets
    change_worksets(ARC_ELEMENTS, workset_arc)
    change_worksets(STR_ELEMENTS, workset_str)
    change_worksets(MEP_ELEMENTS, workset_mep)
    change_worksets(GROUPS, workset_group)

    t.Commit()


#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
