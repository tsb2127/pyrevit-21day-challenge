# -*- coding: utf-8 -*-
__title__   = "12 - Click Counter"
__doc__     = """Version = 3.0
Date    = 03.08.2026
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
- Allow parameter selection
- Add error handling for missing parameters

[BUG]     
- Ensure integer is provided as input for now (COUNT_START)

________________________________________________________________
Last Updates:
- [03.08.2026] V3 Stress Testing (Ensuring form values and parameters exist) 
- [03.08.2026] V2 Refactored (UI form, warning and while loop)
- [03.06.2026] v1 Proof of Concept

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

# ╔═╗╦╔╗╔╔═╗╦    ╔═╗╔═╗╔╦╗╔═╗
# ╠╣ ║║║║╠═╣║    ║  ║ ║ ║║║╣
# ╚  ╩╝╚╝╩ ╩╩═╝  ╚═╝╚═╝═╩╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

#0️⃣ Numbering Rules - FlexForm

# Show UI Form
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, Separator, Button, CheckBox)
components = [Label('PREFIX:'), TextBox('prefix'), Label('COUNT (int)'), TextBox('count'),
              Label('SUFFIX:'), TextBox('suffix'), Separator(), Button('Set Renumbering Rules')]

form = FlexForm('Click Counter Rules', components)
form.show()

# Read UI Form
#🚨 Ensure Input Available
if not form.values:
    forms.alert('No naming rules provided. Please try again', exitscript=True)


#🚨Ensure Count is Integer!

try:
    input = form.values
    PREFIX      = input['prefix']
    COUNT_START = int(input['count'])
    SUFFIX      = input['suffix']
except:
    forms.alert('COUNT START should be an integer. Please try again', exitscript=True)



#1️⃣ Pick Doors
from pyrevit import revit
with forms.WarningBar(title='Select Doors to Renumber or hit [ESC] To STOP'):
    while True:
        elem = revit.pick_element_by_category(BuiltInCategory.OST_Doors)
        if not elem:
            break

        #2️⃣ Create New Value
        value = "{}{:02d}{}".format(PREFIX, COUNT_START, SUFFIX)
        COUNT_START += 1
        print(value)

        # Transaction To Allow Changes
        t = Transaction(doc, 'Click Counter')
        t.Start()   #🔓

        #3️⃣ Change Parameter
        p_name = 'DoorNumber'
        p_door_num = elem.LookupParameter(p_name)

        #🚨 Ensure Parameter Exists
        if not p_door_num:
            forms.alert('Missing Shared Parameter: "{}"'.format(p_name), exitscript=True)
            t.RollBack()

        #4️⃣ Set New Value
        p_door_num.Set(value)

        t.Commit()  #🔒

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
