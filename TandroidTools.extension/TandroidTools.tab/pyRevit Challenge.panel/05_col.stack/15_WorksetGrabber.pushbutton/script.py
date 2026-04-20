# -*- coding: utf-8 -*-
__title__   = "15 - Workset Grabber"
__doc__     = """Version = 1.0
Date    = 03.17.2026
________________________________________________________________
Description:
Select a workset and grab all elements inside it.

________________________________________________________________
How-To:
1. Run tool
2. Select a workset
3. Elements get selected

________________________________________________________________
Last Updates:
- [03.17.2026] v1 Proof of Concept

________________________________________________________________
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
workset_table = doc.GetWorksetTable()


# ╔═╗╦═╗╔═╗╔═╗╔═╗  ╔═╗╔═╗  ╔═╗╔═╗╔╗╔╔═╗╔═╗╔═╗╔╦╗
# ╠═╝╠╦╝║ ║║ ║╠╣   ║ ║╠╣   ║  ║ ║║║║║  ║╣ ╠═╝ ║
# ╩  ╩╚═╚═╝╚═╝╚    ╚═╝╚    ╚═╝╚═╝╝╚╝╚═╝╚═╝╩   ╩
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

#1️⃣ Get Workset
sel_workset = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).FirstWorkset()

#2️⃣ Get Workset Elements (basic option)
all_elements = FilteredElementCollector(doc).WhereElementIsNotElementType().WhereElementIsViewIndependent().ToElements()

sel_workset_el_ids = []
for el in all_elements:
    workset = workset_table.GetWorkset(el.WorksetId)
    if workset.Kind == WorksetKind.UserWorkset:
        if sel_workset.Id == el.WorksetId:
            sel_workset_el_ids.append(el.Id)


#3️⃣ Change Selection
List_el_ids = List[ElementId](sel_workset_el_ids)
uidoc.Selection.SetElementIds(List_el_ids)



#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
