# -*- coding: utf-8 -*-
__title__   = "01 - InPlace Hunter"
__doc__     = """Version = 1.0
Date    = 02.16.2026
________________________________________________________________
Description:
Finds all In-Place Elements in the active document
and generates a clickable selection report.

________________________________________________________________
How-To:
1. Click the button
2. Review the report
3. Select elements from the list or use Select by ID

________________________________________________________________
To-Do:
[INVESTIGATE] - output.linkify does not trigger selection


________________________________________________________________
Last Updates:
- [02.16.2026] v1.0 Initial working version (In-Place detection + report)
________________________________________________________________
Author: Tanmay Bhalerao (following Erik Frits template from LearnRevitAPI.com)"""

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
# Print Header
output.print_md("# In-Place Elements Report")
output.print_md("---")

# Collect all FamilyInstance elements
collector = FilteredElementCollector(doc) \
    .OfClass(FamilyInstance) \
    .WhereElementIsNotElementType()

inplace_elements = []

# Loop through elements and check if InPlace
for elem in collector:
    try:
        elem_type = doc.GetElement(elem.GetTypeId())
        family = elem_type.Family

        if family.IsInPlace:
            inplace_elements.append(elem)

    except:
        # Some elements may not have Family (skip safely)
        continue

# Report Results
if inplace_elements:
    output.print_md("## ⚠ Found {} In-Place Elements".format(len(inplace_elements)))
    output.print_md("---")

    for elem in inplace_elements:
        print("Element:", output.linkify(elem.Id))

    # Auto-select all found elements
    ids = List[ElementId]([e.Id for e in inplace_elements])
    uidoc.Selection.SetElementIds(ids)

else:
    output.print_md("## ✅ No In-Place Elements Found")


#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
