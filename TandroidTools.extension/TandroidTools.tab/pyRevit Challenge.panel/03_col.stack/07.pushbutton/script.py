# -*- coding: utf-8 -*-
__title__   = "07 - Tagless Shame List"
__doc__     = """Version = 1.0
Date    = 04.26.2026
________________________________________________________________
Description:
Audits selected views for untagged Doors AND Windows. Generates
a clickable shame-list report grouped by view, so you can jump
straight to each missing tag and fix it before issuing drawings.

Replaces the manual workflow of opening every plan and visually
hunting for missing tags ("Where's Waldo with your Door tags").

Real value: a 100-sheet drawing set sweep goes from ~30 minutes
of view-by-view checking to ~10 seconds.
________________________________________________________________
How-To:
1. Click Tagless Shame List.
2. Select the views to audit (typically: all sheet plans).
3. Review the report — each view section lists its untagged
   Doors and Windows with clickable navigation links.
4. Click an item to jump to the element. Add the missing tag.
5. Re-run to confirm the view is clean.
________________________________________________________________
To-Do:
[FEATURE] - Let user pick which categories to audit (currently
            hard-coded to Doors + Windows). Could extend to
            Furniture, Lighting Fixtures, Equipment, etc.
[FEATURE] - Cross-view tag awareness: an element tagged in
            another view but not this one is still "untagged
            in this view" — currently correct, but worth
            considering a "tagged anywhere" mode.
[FEATURE] - Optional CSV export of the shame list.
[CLEANUP] - GetTaggedLocalElementIds helper covers Revit 2022+;
            untested on 2021 and earlier.
________________________________________________________________
Last Updates:
- [04.26.2026] v1.0 Multi-view, multi-category, grouped report
- [04.26.2026] v0.1 POC — single view, single category
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 7)"""

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

rvt_year = int(app.VersionNumber)

# Categories to audit — element + its corresponding tag category.
# Adding more is a one-line change: just append a tuple.
# 🎯 CS PATTERN: configuration-as-data.
# Instead of repeating logic for each category, we put the
# (element_category, tag_category) pairs in a list and loop
# the same logic over each. This is how serious tools stay
# maintainable as the feature set grows.
CATEGORY_PAIRS = [
    (BuiltInCategory.OST_Doors,   BuiltInCategory.OST_DoorTags,   "Doors"),
    (BuiltInCategory.OST_Windows, BuiltInCategory.OST_WindowTags, "Windows"),
]


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

def get_tagged_elem_ids(all_tags):
    """Read tagged element IDs from a list of tags, handling the
    Revit 2022+ API change to GetTaggedLocalElementIds.

    Why this exists: in Revit 2021 and earlier, tags expose a single
    element via GetTaggedLocalElement(). In 2022+, multi-leader tags
    can point at multiple elements, so the API became
    GetTaggedLocalElementIds() (plural). This wrapper hides the
    version difference behind one clean call.

    🎯 CS PATTERN: compatibility shim. Every long-lived codebase
    has a few of these. They keep the call-site clean.
    """
    tagged_ids = []
    if rvt_year > 2021:
        for tag in all_tags:
            tagged_ids.extend(tag.GetTaggedLocalElementIds())
    else:
        for tag in all_tags:
            tagged_ids.append(tag.GetTaggedLocalElement().Id)
    return tagged_ids


def find_untagged_in_view(view, elem_cat, tag_cat):
    """For one view + one category, return the list of elements
    that don't have a tag pointing at them in this view.

    🎯 CS PATTERN: set difference, done with a set lookup.
    Erik's original code does `if elem.Id not in tagged_ids` against
    a Python list. That's O(n) per lookup — fine for small views,
    slow on big projects. Converting tagged_ids to a set makes
    each `not in` check O(1). Same logic, much faster on a real
    400-door floor plan.
    """
    all_elems = FilteredElementCollector(doc, view.Id)\
        .OfCategory(elem_cat)\
        .WhereElementIsNotElementType()\
        .ToElements()

    all_tags = FilteredElementCollector(doc, view.Id)\
        .OfCategory(tag_cat)\
        .WhereElementIsNotElementType()\
        .ToElements()

    # Build the set of "ids that are already tagged in this view"
    tagged_ids_set = set(get_tagged_elem_ids(all_tags))

    # Elements whose Id isn't in that set = untagged
    untagged = [el for el in all_elems if el.Id not in tagged_ids_set]
    return untagged


def describe_element(elem):
    """Build a human-readable label like 'Doors: Single-Flush_36" x 84"'
    that gives enough info to identify the element in Revit's UI.
    """
    cat_name = elem.Category.Name if elem.Category else "Uncategorized"
    elem_type = doc.GetElement(elem.GetTypeId())
    family_name = elem_type.Family.Name if elem_type and elem_type.Family else "?"
    type_name = elem.Name if elem.Name else "?"
    return "{cat}: {family}_{type}".format(
        cat=cat_name, family=family_name, type=type_name
    )


# ╔═╗╦═╗╔═╗╔═╗╔═╗╔═╗╔═╗
# ╠═╝╠╦╝║ ║║  ║╣ ╚═╗╚═╗
# ╩  ╩╚═╚═╝╚═╝╚═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Let user pick views to audit
selected_views = forms.select_views(title='Select Views to Audit for Missing Tags')

if not selected_views:
    forms.alert('No views selected. Exiting.', exitscript=True)


# 2️⃣ Header
output.print_md('# Tagless Shame List')
output.print_md(
    'Auditing **{}** view(s) for missing **Doors** and **Windows** tags.\n'
    .format(len(selected_views))
)

total_untagged_count = 0


# 3️⃣ Loop over views, then over category pairs, building report inline
# ────────────────────────────────────────────────────────────────
# Two-level loop:
#   outer: each view the user selected
#   inner: each (element category, tag category) pair we audit
# This is the configuration-as-data pattern paying off — adding
# a new category to audit doesn't change the loop, only the list.
for view in selected_views:

    view_link = output.linkify(view.Id, view.Name)
    view_section_data = []  # collect per-category results before printing

    for elem_cat, tag_cat, label in CATEGORY_PAIRS:
        untagged = find_untagged_in_view(view, elem_cat, tag_cat)
        view_section_data.append((label, untagged))

    # Skip views that are completely clean — keeps the report focused
    view_total = sum(len(items) for _, items in view_section_data)
    if view_total == 0:
        continue

    total_untagged_count += view_total

    output.print_md('---')
    output.print_md('### View: {} ({})'.format(view_link, view.ViewType))

    for label, untagged in view_section_data:
        if not untagged:
            output.print_md('- **{}**: clean'.format(label))
            continue

        output.print_md('- **{}**: {} missing'.format(label, len(untagged)))
        for elem in untagged:
            link = output.linkify(elem.Id, describe_element(elem))
            output.print_md('  - {}'.format(link))


# 4️⃣ Summary footer
output.print_md('---')
if total_untagged_count == 0:
    output.print_md(
        '## All clean.\n\n'
        'No untagged Doors or Windows in the selected views. '
        'Ship the drawings.'
    )
else:
    output.print_md(
        '## Total untagged elements: **{}**\n\n'
        'Click any link above to jump to that element.'
        .format(total_untagged_count)
    )

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!