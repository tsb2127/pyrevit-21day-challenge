# -*- coding: utf-8 -*-
__title__   = "12 - Click Counter"
__doc__     = """Version = 1.0
Date    = 03.06.2026
________________________________________________________________
Description:
Renumber elements in Revit by clicking them in sequence.

The tool allows the user to:
• Pick elements one-by-one in the desired order
• Automatically increment a counter
• Write the generated value into a specified parameter

________________________________________________________________
How-To:
1. Run the tool
2. Click elements in the order you want them numbered
3. Press ESC to stop the selection loop

________________________________________________________________
To-Do:
[FEATURE] 
- Add UI form for prefix / suffix / start value
- Allow parameter selection
- Add error handling for missing parameters

[BUG]     
- None known (PoC stage)

________________________________________________________________
Last Updates:
- [03.06.2026] v1.0 Proof of Concept

________________________________________________________________
Author: Tanmay Bhalerao """

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

#0️⃣ Numbering Rules
COUNT_START = 5
PREFIX      = 'EF-'
SUFFIX      = ''

#1️⃣ Pick Doors
from pyrevit import revit
elem = revit.pick_element_by_category(BuiltInCategory.OST_Doors)

#2️⃣ Create New Value
value = "{}{:02d}{}".format(PREFIX, COUNT_START, SUFFIX)
print(value)

# Transaction To Allow Changes
t = Transaction(doc, 'Click Counter')
t.Start()   #🔓

#3️⃣ Change Parameter
p_door_num = elem.LookupParameter('DoorNumber')
p_door_num.Set(value)

t.Commit()  #🔒

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
