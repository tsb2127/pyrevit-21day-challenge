# -*- coding: utf-8 -*-
__title__   = "06 - 3D Isolation Trap"
__doc__     = """Version = 1.0
Date    = 04.26.2026
________________________________________________________________
Description:
Pick one or more Group Types, get a freshly-created 3D view
showing ONLY the elements inside those groups. Two modes:
single combined view, or one view per group type.

Real use: QA-checking repeated assemblies (apartment units,
bathroom pods, facade modules) without fighting Revit's native
visibility toggles or Section Box. One click → isolated view.
________________________________________________________________
How-To:
1. Click 3D Isolation Trap.
2. Pick one or more Group Types from the list.
3. Pick a view mode (single combined / one per type).
4. Tool creates the view(s), permanently isolates the elements,
   and prints clickable links to navigate to each new view.
________________________________________________________________
To-Do:
[FEATURE] - Auto-open the first new view after creation
            (currently the user has to click the link)
[FEATURE] - Apply a section box around the isolated elements
            so the camera frames them automatically
[FEATURE] - Color-code groups in single-view mode for visual
            distinction between group types
[CLEANUP] - Element.Name.GetValue() workaround is needed
            because group_type.Name returns the wrong thing in
            pyRevit. Document this for future me.
________________________________________________________________
Last Updates:
- [04.26.2026] v1.0 Single + multi-view modes, clickable report
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 6)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script
import datetime

# .NET Imports
import clr
clr.AddReference('System')
from System.Collections.Generic import List


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()

# Default 3D ViewFamilyType — required to construct a new 3D view
view3d_type_id = doc.GetDefaultElementTypeId(ElementTypeGroup.ViewType3D)

# All placed Group instances in the project
# (Group != GroupType — this is the placed instances, not the templates)
all_groups = FilteredElementCollector(doc).OfClass(Group).ToElements()


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

def create_isolated_3d_view(isolate_ids):
    """Create a new isometric 3D view, isolate the given element IDs
    in it, and bake the isolation into the view permanently.

    🎯 CS PATTERN: .NET–Python bridge.
    Revit's API expects a .NET typed list (List[ElementId]), not a
    Python list. The conversion `List[ElementId](python_list)` is
    the seam between Python's duck-typed world and .NET's strict-
    typed world. You'll do this anytime a Revit method takes an
    IList<T> — same pattern, same fix.

    🎯 CS PATTERN: temporary state → permanent state.
    Revit's IsolateElementsTemporary applies a temporary visibility
    rule (the orange border you'd see in the UI when you hit
    HI / Isolate). ConvertTemporaryHideIsolateToPermanent then bakes
    that rule into the view's saved settings. Two-step idiom.
    """
    new_view = View3D.CreateIsometric(doc, view3d_type_id)

    # Bridge: Python list → .NET List[ElementId]
    list_isolate_ids = List[ElementId](isolate_ids)

    new_view.IsolateElementsTemporary(list_isolate_ids)
    new_view.ConvertTemporaryHideIsolateToPermanent()
    return new_view


def safe_group_type_name(group_type):
    """Read a GroupType's name reliably.

    🎯 NOTE: Erik flagged this in his lesson. In pyRevit, calling
    group_type.Name directly returns something unexpected (looks
    like a property descriptor, not a string). The reliable
    accessor is Element.Name.GetValue(group_type). Annoying,
    but it's the documented workaround.
    """
    return Element.Name.GetValue(group_type)


# ╔═╗╦═╗╔═╗╔═╗╔═╗╔═╗╔═╗
# ╠═╝╠╦╝║ ║║  ║╣ ╚═╗╚═╗
# ╩  ╩╚═╚═╝╚═╝╚═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Get all Group Types in the project
all_group_types = FilteredElementCollector(doc).OfClass(GroupType)
dict_group_types = {safe_group_type_name(g): g for g in all_group_types}

if not dict_group_types:
    forms.alert(
        'No Group Types in this project. Create some Groups first, then try again.',
        exitscript=True,
    )


# 2️⃣ User picks which Group Types to isolate
sel_group_type_names = forms.SelectFromList.show(
    sorted(dict_group_types.keys()),
    multiselect=True,
    button_name='Isolate Selected',
    title='Pick Group Types to Isolate',
)

if not sel_group_type_names:
    forms.alert('No Group Types selected. Try again.', exitscript=True)


# 3️⃣ User picks single vs multi view mode
view_mode = forms.alert(
    "How do you want the views?\n\n"
    "Single = one combined 3D view with everything\n"
    "Multiple = one isolated 3D view per group type",
    title='Select View Mode',
    options=["Single View (All)", "Multiple Views (Each)"],
)

if not view_mode:
    forms.alert('No view mode selected. Try again.', exitscript=True)


# Resolve selected names back to GroupType objects, then collect
# all matching Group instances in the project
sel_group_types = [dict_group_types[name] for name in sel_group_type_names]
sel_type_names_set = set(sel_group_type_names)


# ────────────────────────────────────────────────────────────────
# 🔒 Transaction — required for any document modification
# ────────────────────────────────────────────────────────────────
t = Transaction(doc, '3D Isolation Trap')
t.Start()

new_views = []

if view_mode == "Single View (All)":
    # Filter to instances of the selected types
    groups_to_isolate = [g for g in all_groups if g.Name in sel_type_names_set]

    # 🎯 CS PATTERN: list flattening (double-for comprehension)
    # Each group has many member element IDs; we want a single flat
    # list of every element ID across all groups.
    keep_ids = [
        el_id
        for group in groups_to_isolate
        for el_id in group.GetMemberIds()
    ]

    new_view = create_isolated_3d_view(keep_ids)
    timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    new_view.Name = "Isolation - All Selected ({})".format(timestamp)
    new_views.append(new_view)

elif view_mode == "Multiple Views (Each)":
    for group_name in sel_group_type_names:
        groups_to_isolate = [g for g in all_groups if g.Name == group_name]

        # Same flattening pattern, scoped to one group type
        keep_ids = [
            el_id
            for group in groups_to_isolate
            for el_id in group.GetMemberIds()
        ]

        if not keep_ids:
            # No placed instances of this group type — skip silently
            continue

        new_view = create_isolated_3d_view(keep_ids)
        timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        new_view.Name = "{} ({})".format(group_name, timestamp)
        new_views.append(new_view)

t.Commit()


# 4️⃣ Summary report
output.print_md('# 3D Isolation Trap Report')
output.print_md("- **Mode:** {}".format(view_mode))
output.print_md("- **Group Types selected:** {}".format(len(sel_group_type_names)))
output.print_md("- **New views created:** {}".format(len(new_views)))
output.print_md('---')

if not new_views:
    output.print_md('No views created — none of the selected Group Types had placed instances.')
else:
    output.print_md('### New Views')
    for v in new_views:
        link = output.linkify(v.Id, v.Name)
        output.print_md("- {}".format(link))

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!