# -*- coding: utf-8 -*-
__title__   = "08 - Warnings Snitch (POC)"
__doc__     = """Version = 0.1 (Proof of Concept)
Date    = 04.26.2026
________________________________________________________________
Description:
PROOF OF CONCEPT — not the final tool yet.

Pulls every warning in the active project, prints each warning's
description, and creates a clickable button (linkify) that selects
the elements responsible for the warning. No grouping, no UI form,
no fancy table — just raw output to verify the mechanic works.

Teaches: doc.GetWarnings(), FailureMessage objects, the difference
between Failing and Additional elements, and pyRevit's linkify for
multi-element selection.
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 8 — POC stage)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script


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

# 1️⃣ Pull every warning in the project
# ────────────────────────────────────────────────────────────────
# doc.GetWarnings() returns an IList of FailureMessage objects.
# Each FailureMessage has methods to ask: "what's the description?"
# "which elements failed?" "which other elements are involved?"
all_warnings = doc.GetWarnings()

if not all_warnings:
    forms.alert("No warnings in this project. Lucky you.", exitscript=True)

print("Found {} warnings in the project.\n".format(len(all_warnings)))
print("=" * 60)


# 2️⃣ Iterate over each warning and print info + linkify button
# ────────────────────────────────────────────────────────────────
# CS PATTERN — you'll see this exact shape constantly:
#   - get a collection
#   - loop over it
#   - read structured data from each item
#   - format output for a human
# Same as iterating through emails, log entries, API results, anything.

for warn in all_warnings:

    # Read the warning's description (the human-readable explanation)
    description = warn.GetDescriptionText()

    # Get elements involved.
    # GetFailingElements() = the elements that CAUSED the warning
    # GetAdditionalElements() = OTHER elements involved (often empty,
    # but sometimes the failing list is empty and this list has them
    # — depends on warning type. Combining both is safer.)
    fail_elem_ids = warn.GetFailingElements()
    add_elem_ids  = warn.GetAdditionalElements()

    # Combine into one Python list. list() converts the .NET IList
    # into a Python list so we can use + to concatenate.
    elem_ids = list(fail_elem_ids) + list(add_elem_ids)

    # Build a clickable "Select Elements" button in the output.
    # linkify takes a list of ElementIds and renders a button that,
    # when clicked, selects those elements in Revit.
    link = output.linkify(elem_ids, "Select {} elements".format(len(elem_ids)))

    # Print the warning info
    print("\n" + description)
    print(link)
    print("-" * 30)

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!