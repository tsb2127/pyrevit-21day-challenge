# -*- coding: utf-8 -*-
__title__   = "02 - Door Swing"
__doc__     = """Version = 1.0
Date    = 01.01.2026
________________________________________________________________
Description:
Placeholder for pyRevit .pushbutton.
Use it as a base for your new pyRevit tool.

________________________________________________________________
How-To:
1. Step 1...
2. Step 2...
3. Step 3...

________________________________________________________________
To-Do:
[FEATURE] - Describe Your Feature...
[BUG]     - Describe Your BUG...

________________________________________________________________
Last Updates:
- [01.01.2026] v1.0 Change Description
- [01.01.2026] v0.5 Change Description
- [01.01.2026] v0.1 Change Description 
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

# ╔═╗╔╦╗╦╔╦╗
# ║╣  ║║║ ║
# ╚═╝═╩╝╩ ╩  EDIT
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# #0️⃣ Get Single Door
# from Autodesk.Revit.UI.Selection import ObjectType
# ref  = uidoc.Selection.PickObject(ObjectType.Element)
# door = doc.GetElement(ref)

#1️⃣ Get All Doors
cat       = BuiltInCategory.OST_Doors
all_doors = FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType().ToElements()

# 🔓 Allow Changes with Revit API
t = Transaction(doc, 'Door Swing')
t.Start()  # 🔓 Allow Changes

for door in all_doors:
    #2️⃣ Find Door Swing (.Mirrored)
    value = 'Mirrored' if door.Mirrored else 'Regular' #🚨 Ensure correct StorageType

    #3️⃣ Write To Another Parameter
    # param = door.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS) # NB! Should be VariesByGroup to avoid issues!
    param = door.LookupParameter('DoorState')
    #🚨 Ensure ShareParameter Exists
    if param:
        param.Set(value)
    else:
        forms.alert('Parameter DoorState not found ...', exitscript=True )

t.Commit()  #🔒 Confirm Changes

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
