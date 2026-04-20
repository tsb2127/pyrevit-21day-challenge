# -*- coding: utf-8 -*-
__title__   = "11 - Dream Picker"
__doc__     = """Version = 1.0
Date    = 04.19.2026
________________________________________________________________
Tutorial - Erik's final code
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

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# -*- coding: utf-8 -*-
__title__   = "11 - Dream Picker"

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
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


# ╦═╗╔═╗╔═╗╔═╗╔═╗╔╦╗╔═╗╦═╗╔═╗╔╦╗
# ╠╦╝║╣ ╠╣ ╠═╣║   ║ ║ ║╠╦╝║╣  ║║
# ╩╚═╚═╝╚  ╩ ╩╚═╝ ╩ ╚═╝╩╚═╚═╝═╩╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

#1️⃣ Get Selected Elements
#--------------------------------------------------
sel_elem_ids = uidoc.Selection.GetElementIds()
sel_elems    = [doc.GetElement(e_id) for e_id in sel_elem_ids]

# Quick and Simple Filter (Optionally)
filtered_elements = [el for el in sel_elems if type(el) == Wall]
print(filtered_elements)

#🚨 Ensure Elements Selected.
if not sel_elems:
    forms.alert('No Elements Selected.',exitscript=True)


#3️⃣ Pick Object
#--------------------------------------------------
from Autodesk.Revit.UI.Selection import ObjectType
with forms.WarningBar(title='Select Single Element...'):
    picked_object = None #🚨 Ensure Default Variable Value

    #🚨 Try/Except to catch user cancellation
    try:
        ref           = uidoc.Selection.PickObject(ObjectType.Element) #type: Reference
        picked_object = doc.GetElement(ref)
        print(picked_object)
    except:
        forms.alert('No Elements Selected. Please Try Again.',exitscript=True)



#4️⃣ Pick Objects (Multiple)
#--------------------------------------------------
from Autodesk.Revit.UI.Selection import ObjectType
with forms.WarningBar(title='Select Some Elements...'):
    picked_objects = None  # Ensure Default Variable Value

    try:
        refs           = uidoc.Selection.PickObjects(ObjectType.Element)
        picked_objects = [doc.GetElement(ref) for ref in refs]
    except:
        pass

if not picked_objects:
    forms.alert('No Elements Selected. Please Try Again.', exitscript=True)

for el in picked_objects:
    print(el)


# # 💪 Advanced Filtering During  Selection (ISelectionFilter)
# #--------------------------------------------------
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType

# Create Class with  Custom Rules
class ef_filter(ISelectionFilter):
    def AllowElement(self, element):
        # Logic B (Wall inside groups)
        # if type(element) == Wall and element.GroupId != ElementId.InvalidElementId:
        #     return True

        # Logic A (Room with Area less than 200SF (RevitAPI uses Square Feet internally!)
        if element.Category.Id == ElementId(BuiltInCategory.OST_Rooms):
            if element.Area < 200:
                return True

# Prompt User Selection (with custom filter)
sel_elems = None #🚨 Ensure Default Variable Value

#🚨 Try/Except to catch user cancellation
try:
    refs      = uidoc.Selection.PickObjects(ObjectType.Element, ef_filter())
    sel_elems = [doc.GetElement(ref) for ref in refs]
except:
    pass

#🚨 Ensure Elements Selected.
if not sel_elems:
    forms.alert('No Elements Selected.',exitscript=True)

print(sel_elems)



#3️⃣ Update UI Selection (.SetElementIds)
#--------------------------------------------------
elements    = doc.GetElementIds()
walls       = [el for el in elements if type(el) == Wall]

el_ids      = [e.Id for e in walls]
List_el_ids = List[ElementId](el_ids)      #Convert python list to .NET List[ElementId]

uidoc.Selection.SetElementIds(List_el_ids) # Change Revit UI Selection


#███████████████████████████████████████████████████████████████████████████
# # Happy Coding!



#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
