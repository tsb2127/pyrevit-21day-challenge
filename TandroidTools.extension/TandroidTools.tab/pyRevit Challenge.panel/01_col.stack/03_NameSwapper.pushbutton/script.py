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
[Edge Cases] - Stress Test

________________________________________________________________
Last Updates:
- [02.18.2026] v2 Refactored
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

# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
def get_user_input():
    """Function to get user input with rpw.ui.forms.FlexForm"""
    from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, Separator, Button, CheckBox)

    components = [
        Label('Prefix:'),   TextBox('prefix'),
        Label('Find:'),     TextBox('find'),
        Label('Replace:'),  TextBox('replace'),
        Label('Sufix:'),    TextBox('sufix'),
        Separator(),
        Button('Select', is_default=True)]

    form = FlexForm('Name Swapper', components)
    form.show()

    return form.values


# ╦═╗╔═╗╔═╗╔═╗╔═╗╔╦╗╔═╗╦═╗╔═╗╔╦╗
# ╠╦╝║╣ ╠╣ ╠═╣║   ║ ║ ║╠╦╝║╣  ║║
# ╩╚═╚═╝╚  ╩ ╩╚═╝ ╩ ╚═╝╩╚═╚═╝═╩╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

#1️⃣ Select Views
#------------------------------
from pyrevit import forms
sel_views = forms.select_views()

# 🚨 Ensure User Input
if not user_input
    forms.alert('Please select a view', exitscript=True)

#2️⃣ Define Rules
#------------------------------
user_input = get_user_input()

# 🚨 Ensure User Input
if not user_input:
    forms.alert('No naming rules, please try again..', exitscript=True)

PREFIX     = user_input['prefix']
FIND       = user_input['find']
REPLACE    = user_input['replace']
SUFFIX     = user_input['sufix']


#🔓 Start Transaction (Allow API Changes)
t = Transaction(doc, __title__)
t.Start()   #🔓 Allow Changes

#3️⃣ Change View Name
#------------------------------
print('Renaming Selected Views:')
print('-'*50)
for view in sel_views:
    old_name = view.Name
    new_name = PREFIX + old_name.replace(FIND, REPLACE) + SUFFIX

    view.Name = new_name # Change View Name

    #4️⃣ Report the change
    # ------------------------------
    print("{} ➡️ {}".format(old_name, new_name))

t.Commit()  #🔒 Confirm Changes



#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
