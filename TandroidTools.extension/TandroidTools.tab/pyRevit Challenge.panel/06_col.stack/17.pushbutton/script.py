# -*- coding: utf-8 -*-
__title__   = "17 - Shared-Param Smuggler (POC)"
__doc__     = """Version = 0.1 (Proof of Concept)
Date    = 05.07.2026
________________________________________________________________
Description:
PROOF OF CONCEPT — read-only inspection.

Opens the currently-loaded shared parameter file (or prompts
for one), walks every group, prints every parameter inside.
No imports, no UI form, no transaction yet — just verify we
can read the file and see its contents.

Teaches: ExternalDefinitionFile loading, the Group/Definition
tree structure inside a shared param file, save-and-restore
of application-wide state.
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 17 — POC stage)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script
import os


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()


# ╔═╗╦═╗╔═╗╔═╗╔═╗  ╔═╗╔═╗  ╔═╗╔═╗╔╗╔╔═╗╔═╗╔═╗╔╦╗
# ╠═╝╠╦╝║ ║║ ║╠╣   ║ ║╠╣   ║  ║ ║║║║║  ║╣ ╠═╝ ║
# ╩  ╩╚═╚═╝╚═╝╚    ╚═╝╚    ╚═╝╚═╝╝╚╝╚═╝╚═╝╩   ╩
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Save the user's current shared param file path
# ────────────────────────────────────────────────────────────────
# 🎯 CS PATTERN: save-then-restore application state.
# Revit's "current shared param file" is application-wide global
# state. If we change it during our tool's run, we're polluting
# the user's environment. So we capture it first, do our work,
# then restore at the end. Same idea as try/finally for resource
# cleanup, or context managers ("with open(...) as f:").
original_sp_file = app.SharedParametersFilename
print("Current SP file path: {}".format(original_sp_file or "(none set)"))


# 2️⃣ Make sure a shared param file is loaded
# ────────────────────────────────────────────────────────────────
# OpenSharedParameterFile reads whatever file path is in
# app.SharedParametersFilename. If that's empty or the file
# doesn't exist, it returns None.
sp_file = app.OpenSharedParameterFile()

if sp_file is None:
    # No SP file is currently set — prompt user to pick one
    forms.alert(
        "No shared parameter file is currently loaded in Revit.\n\n"
        "Pick a .txt shared parameter file in the next dialog.",
        title="No SP File Loaded",
    )

    sp_path = forms.pick_file(file_ext='txt', title='Select Shared Parameter File')
    if not sp_path:
        forms.alert("No file selected. Exiting.", exitscript=True)

    app.SharedParametersFilename = sp_path
    sp_file = app.OpenSharedParameterFile()

    if sp_file is None:
        forms.alert(
            "Couldn't open that file as a shared parameter file. "
            "Make sure it's a valid Revit SP .txt.",
            exitscript=True,
        )


# 3️⃣ Walk the file's tree and print everything
print("\n" + "=" * 60)
print("Shared Parameter File: {}".format(sp_file.Filename))
print("=" * 60)

def get_param_type_label(definition):
    """Read parameter type, handling Revit 2022+ ForgeTypeId API change.

    🎯 CS PATTERN: API compatibility shim, same as Day 9's ElementId
    Int64 fix. New code path first, fallback to old. Try/except as
    feature detection.
    """
    # Modern API (2022+): GetDataType() returns ForgeTypeId
    try:
        type_id = definition.GetDataType().TypeId
        # TypeId looks like "autodesk.spec.string:text-1.0.0"
        # Extract the friendly part: "text"
        if ':' in type_id:
            type_id = type_id.split(':')[-1]
        if '-' in type_id:
            type_id = type_id.split('-')[0]
        return type_id
    except:
        pass

    # Older API fallback
    try:
        return str(definition.ParameterType)
    except:
        return "Unknown"


total_params = 0
total_groups = 0
for group in sp_file.Groups:
    print("\n📁 Group: {}".format(group.Name))
    total_groups += 1
    for definition in group.Definitions:
        param_type = get_param_type_label(definition)
        print("   • {}  ({})".format(definition.Name, param_type))
        total_params += 1

print("\n" + "=" * 60)
print("Total: {} parameters across {} groups".format(total_params, total_groups))


# 4️⃣ Restore the original SP file path (good citizen behavior)
# ────────────────────────────────────────────────────────────────
# If we changed the SP file path in step 2, restore it now so
# the user's normal Revit session isn't affected. If we never
# changed it (original_sp_file was already set), this is a no-op.
if original_sp_file:
    app.SharedParametersFilename = original_sp_file

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!