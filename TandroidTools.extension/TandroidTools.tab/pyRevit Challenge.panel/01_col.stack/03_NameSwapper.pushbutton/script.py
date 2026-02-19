# -*- coding: utf-8 -*-
__title__   = "03 - Name Swapper"
__doc__     = """Version = 1.0
Date    = 02.18.2026
________________________________________________________________
Description:
Batch rename selected Revit views.

________________________________________________________________
How-To:
1. Select views in Revit or run tool to choose from list.
2. Enter rename pattern (prefix/suffix/find-replace).
3. Confirm and apply changes.

________________________________________________________________
To-Do:
[FEATURE] - Custom UI for Naming Forms

________________________________________________________________
Last Updates:
- [02.18.2026] v1 Proof of Concept 
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

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

#1️⃣ Select Views
from pyrevit import forms
selected_views = forms.select_views()

#2️⃣ Define Rules
PREFIX     = 'Pre_'
FIND       = 'Find'
REPLACE    = 'Replace'
SUFFIX     = '_Suf'

#🔓 Start Transaction (Allow API Changes)
t = Transaction(doc, "Name Swapper")
t.Start()       #🔓 Allow Changes

#3️⃣ Change View Name
print('Renaming Views:')
print('-'*50)
for view in selected_views:
    old_name = view.Name
    new_name =  PREFIX + old_name.replace(FIND, REPLACE) + SUFFIX

    view.Name = new_name

    # 4️⃣ Report the change
    print('{} ➡️ {}'.format(old_name, new_name))

t.Commit()      #🔒 # Confirm Changes


#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
