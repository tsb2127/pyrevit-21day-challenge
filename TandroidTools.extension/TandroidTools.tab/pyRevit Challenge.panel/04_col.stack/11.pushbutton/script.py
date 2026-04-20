# -*- coding: utf-8 -*-
__title__   = "11 - Dream Picker"
__doc__     = """Version = 1.0
Date    = 04.19.2026
________________________________________________________________
Description:
Click one element, pick one of its parameters, then click any
number of other elements — only ones matching that parameter
value will be clickable. The matching elements are selected in
the Revit UI so you can edit, tag, or pin them in bulk.

________________________________________________________________
How-To:
1. Open a view with the elements you want to work on.
2. Click the Dream Picker button.
3. Pick one element that has the parameter value you want.
4. Pick that parameter from the list.
5. Click or window-select the elements to filter. Non-matches
   show a "not allowed" cursor.
6. Press Finish — all matches become the active selection.

________________________________________________________________
To-Do:
[FEATURE] - Support numeric range matching (e.g., Area > 200 SF)
            instead of exact match only.
[FEATURE] - Remember the last-used parameter for quick re-runs.
[BUG]     - Parameters with ElementId values only compare on the
            referenced element's name — could collide if two
            different elements share a name.

________________________________________________________________
Last Updates:
- [04.19.2026] v1.0 Parameter-matched picker with ISelectionFilter
               closure pattern, instance + type params supported.
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 11)"""

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

from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter


# ──────────────────────────────────────────────────────────────────────
# STEP 1: First pick — the "reference" element.
#
# We ask the user to click one element that has the parameter value
# they want to match against. (e.g., a wall that's already 2HR rated.)
#
# A tiny filter class that accepts anything — on this first pick,
# we don't know what the user's looking for yet, so we don't restrict.
# ──────────────────────────────────────────────────────────────────────
class AllowAnything(ISelectionFilter):
    def AllowElement(self, element):
        return True


with forms.WarningBar(title='Step 1 of 3 — Click one element whose parameter value you want to match'):
    try:
        ref = uidoc.Selection.PickObject(ObjectType.Element, AllowAnything())
    except:
        script.exit()

reference_element = doc.GetElement(ref)
reference_category_id = reference_element.Category.Id


# ──────────────────────────────────────────────────────────────────────
# STEP 2: Let the user pick WHICH parameter to match on.
#
# An element has dozens of parameters — instance and type, built-in
# and custom. We need to present them in a picker so the user can
# choose intentionally.
#
# reference_element.Parameters gives us instance parameters. We also
# pull type parameters by looking up the Type and reading its params.
# Then we build a dict {display_name: parameter_object} and show
# pyRevit's built-in selection form.
#
# We skip parameters with no value — they'd filter everything out
# and confuse the user.
# ──────────────────────────────────────────────────────────────────────

def get_param_value_as_string(param):
    """Return a parameter's current value as a readable string.

    Revit parameters have four 'storage types': String, Integer, Double
    (numbers), and ElementId (references to other elements). We need
    different accessor methods for each. AsValueString() handles unit
    display for numeric params (e.g., '2HR' instead of raw internal value).
    """
    if param is None or not param.HasValue:
        return None

    value_string = param.AsValueString()  # Nicely formatted for UI
    if value_string:
        return value_string

    # Fallbacks by storage type
    storage = param.StorageType
    if storage == StorageType.String:
        return param.AsString()
    if storage == StorageType.Integer:
        return str(param.AsInteger())
    if storage == StorageType.Double:
        return str(param.AsDouble())
    if storage == StorageType.ElementId:
        target_id = param.AsElementId()
        target = doc.GetElement(target_id)
        return target.Name if target else None
    return None


# Gather instance params from the picked element
instance_params = list(reference_element.Parameters)

# Also gather type params (often where the important stuff lives:
# Fire Rating, Assembly Code, Type Mark, etc.)
type_element = doc.GetElement(reference_element.GetTypeId())
type_params = list(type_element.Parameters) if type_element else []

# Build a menu of "ParamName (current value) [instance or type]"
param_menu = {}
for p in instance_params:
    value = get_param_value_as_string(p)
    if value:
        label = '{name}  —  {value}  [instance]'.format(name=p.Definition.Name, value=value)
        param_menu[label] = ('instance', p.Definition.Name, value)

for p in type_params:
    value = get_param_value_as_string(p)
    if value:
        label = '{name}  —  {value}  [type]'.format(name=p.Definition.Name, value=value)
        param_menu[label] = ('type', p.Definition.Name, value)

if not param_menu:
    forms.alert('That element has no parameters with values. Try a different element.', exitscript=True)

# pyRevit's SelectFromList shows a clean dialog with search
chosen_label = forms.SelectFromList.show(
    sorted(param_menu.keys()),
    title='Step 2 of 3 — Pick a parameter to match on',
    button_name='Match this parameter',
    multiselect=False
)

if not chosen_label:
    script.exit()

param_scope, param_name, target_value = param_menu[chosen_label]


# ──────────────────────────────────────────────────────────────────────
# STEP 3: Build the *real* ISelectionFilter using a closure.
#
# 🎯 CS FUNDAMENTAL: closures.
#
# A closure is a function (or in our case, a class method) that
# "captures" variables from the surrounding scope. Look at how
# AllowElement references `target_value`, `param_name`, and
# `reference_category_id` — those aren't passed in as arguments,
# they're just... available, because the class is defined here
# inside the same scope that created them.
#
# That's a closure. The filter object "remembers" the context it
# was born in, and carries it forward. Revit will call AllowElement
# a thousand times while the user moves the cursor around — each
# call can look up the captured values without us re-passing them.
#
# This is the same mechanism behind: JavaScript event handlers,
# Python decorators, React useState, SQL prepared statements.
# Same idea, different language.
# ──────────────────────────────────────────────────────────────────────

class MatchParameterFilter(ISelectionFilter):
    def AllowElement(self, element):
        # Only allow same category as the reference element
        if element.Category is None or element.Category.Id != reference_category_id:
            return False

        # Find the parameter on this candidate element
        if param_scope == 'instance':
            candidate_param = element.LookupParameter(param_name)
        else:
            # Type parameter — look it up on the Type, not the instance
            type_elem = doc.GetElement(element.GetTypeId())
            if type_elem is None:
                return False
            candidate_param = type_elem.LookupParameter(param_name)

        candidate_value = get_param_value_as_string(candidate_param)
        return candidate_value == target_value


# ──────────────────────────────────────────────────────────────────────
# STEP 4: Pick multiple matching elements, gated by our filter.
#
# The user rubber-bands or clicks through the view. The cursor will
# show a "not allowed" symbol for any element that doesn't match
# — that's Revit calling our AllowElement and respecting its answer.
#
# PickObjects (plural) lets the user pick many at once. They press
# Finish (or Enter) to confirm.
# ──────────────────────────────────────────────────────────────────────

with forms.WarningBar(title='Step 3 of 3 — Click all elements to select. Only matching ones are clickable. Press Finish when done.'):
    try:
        refs = uidoc.Selection.PickObjects(ObjectType.Element, MatchParameterFilter())
    except:
        script.exit()

if not refs:
    forms.alert('No elements picked. Try again.', exitscript=True)

picked_elements = [doc.GetElement(r) for r in refs]


# ──────────────────────────────────────────────────────────────────────
# STEP 5: Apply the selection to the Revit UI and report.
# ──────────────────────────────────────────────────────────────────────

picked_ids = List[ElementId]([el.Id for el in picked_elements])
uidoc.Selection.SetElementIds(picked_ids)

output.print_md(
    '**Selected {count} elements** where `{param}` = *{value}* '
    '(category: {cat}).'.format(
        count=len(picked_elements),
        param=param_name,
        value=target_value,
        cat=reference_element.Category.Name,
    )
)

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
