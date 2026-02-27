# -*- coding: utf-8 -*-
__title__   = "05 - BIMpressionist Painter"
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

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
#📦 Variables
active_view   = doc.ActiveView
all_patterns  = FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
solid_pattern = next((p for p in all_patterns if p.GetFillPattern().IsSolidFill), None)

if not solid_pattern:
    forms.alert('No Solid Fill pattern was found in this project.', exitscript=True)


#1️⃣ Get Walls
walls_in_view = FilteredElementCollector(doc, active_view.Id).OfClass(Wall).WhereElementIsNotElementType().ToElements()

if not walls_in_view:
    forms.alert('No wall instances were found in the active view.', exitscript=True)


#2️⃣ Sort Elements Based On Property/Parameter Value
from collections import defaultdict
dict_values = defaultdict(list)

for wall in walls_in_view:
    wall_type_name = wall.Name # 💡Change Rules Here...
    dict_values[wall_type_name].append(wall)


#🔓 Allow Changes with Revit API
t = Transaction(doc, 'BIMpressionist Painter')
t.Start()   #🔓 Allow Changes


#3️⃣ Prepare Graphic Overrides Settings
import random
for key, list_elems in dict_values.items():

    #Deterministic color per group key
    random.seed(key)
    R = random.randint(0,255)
    G = random.randint(0,255)
    B = random.randint(0,255)
    color = Color(R,G,B)

    #⚙️ CREATE OVERRIDE SETTINGS
    override_settings = OverrideGraphicSettings()

    #⚙️ SURFACE FOREGROUND (PATTERN + COLOR)
    override_settings.SetSurfaceForegroundPatternId(solid_pattern.Id)
    override_settings.SetSurfaceForegroundPatternColor(color)

    #⚙️ CUT FOREGROUND ( PATTERN + COLOR)
    override_settings.SetCutForegroundPatternId(solid_pattern.Id)
    override_settings.SetCutForegroundPatternColor(color)


    #4️⃣ Override Element Graphics
    for el in list_elems:
        active_view.SetElementOverrides(el.Id, override_settings)

t.Commit()  #🔒 Confirm Changes

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
