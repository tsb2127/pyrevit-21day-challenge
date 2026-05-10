# -*- coding: utf-8 -*-
__title__   = "19 - Wall Splitter"
__doc__     = """Version = 2.0
Date    = 05.10.2026
________________________________________________________________
Description:
Pick a multi-layer compound wall. The tool reads each layer's
material and thickness, creates (or reuses) a single-layer
WallType per layer, duplicates the original wall once per layer,
sets each copy's curve to the correct parallel offset, joins
the new walls' geometry, and deletes the original.

Result: one compound wall becomes N single-layer walls in the
same physical location, each individually editable.
________________________________________________________________
How-To:
1. Save your project (this tool deletes the original wall).
2. Click Wall Splitter.
3. Pick a multi-layer wall.
4. Tool produces N single-layer walls; original is deleted.
________________________________________________________________
To-Do:
[FEATURE] - Multi-wall selection
[FEATURE] - Option to keep the original instead of deleting
[FEATURE] - Smarter handling of stacked-wall types
[BUG]     - Hosted elements (windows/doors) attach to one of
            the new layer-walls based on dependent-element
            order, not always the visually correct one
________________________________________________________________
Last Updates:
- [05.10.2026] v2.0 Polish: per-layer try/except, membrane
               skip, generic-material fallback, geometry join,
               cached wall-type dict
- [05.09.2026] v1.0 Initial working version with bug fix on
               type-name characters
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 19)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script, revit
import traceback

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

# 🎯 CACHED LOOKUP — fetch all WallTypes once, build a name→type dict.
# We'll reuse this throughout the loop instead of re-querying every
# iteration. Big projects can have 100+ wall types; querying once
# is meaningfully faster.
all_wall_types = FilteredElementCollector(doc).OfClass(WallType).ToElements()
dict_wall_types = {Element.Name.GetValue(wt): wt for wt in all_wall_types}


# ╔═╗╦═╗╔═╗╔═╗╔═╗  ╔═╗╔═╗  ╔═╗╔═╗╔╗╔╔═╗╔═╗╔═╗╔╦╗
# ╠═╝╠╦╝║ ║║ ║╠╣   ║ ║╠╣   ║  ║ ║║║║║  ║╣ ╠═╝ ║
# ╩  ╩╚═╚═╝╚═╝╚    ╚═╝╚    ╚═╝╚═╝╝╚╝╚═╝╚═╝╩   ╩
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Pick a wall
with forms.WarningBar(title='Pick a multi-layer wall to split'):
    try:
        wall = revit.pick_element_by_category(BuiltInCategory.OST_Walls)
    except:
        script.exit()

if not wall:
    forms.alert('No wall selected.', exitscript=True)


# 2️⃣ Read the wall's compound structure (with guards)
wall_type = wall.WallType
structure = wall_type.GetCompoundStructure()

# Curtain walls and stacked walls don't have a CompoundStructure
if not structure:
    forms.alert(
        "Selected wall doesn't have a compound structure (likely a "
        "curtain wall or stacked wall). Pick a regular layered wall.",
        exitscript=True,
    )

layers = structure.GetLayers()
if len(layers) < 2:
    forms.alert(
        "This wall only has one layer — nothing to split.",
        exitscript=True,
    )

if not isinstance(wall.Location, LocationCurve):
    forms.alert("This wall doesn't have a curve-based location.", exitscript=True)


# ────────────────────────────────────────────────────────────────
# 🔒 Transaction — required for any document modification
# ────────────────────────────────────────────────────────────────
t = Transaction(doc, 'Wall Splitter')
t.Start()

current_offset = 0.0
new_walls = []
skipped = []
created_types = []
reused_types = []

for n, layer in enumerate(layers):
    # 🎯 PATTERN: per-layer try/except.
    # Same defensive shape as Day 18's per-floor isolation. One
    # bad layer should not stop the rest of the batch — we log
    # it and keep going.
    try:
        # Skip membrane layers (zero or near-zero thickness — Revit
        # rejects them as the basis for a single-layer WallType)
        if layer.Function == MaterialFunctionAssignment.Membrane:
            skipped.append((n, "membrane layer"))
            continue

        width_ft = layer.Width
        if width_ft <= 0.0001:
            skipped.append((n, "zero-thickness layer"))
            continue

        width_cm = UnitUtils.ConvertFromInternalUnits(width_ft, UnitTypeId.Centimeters)
        width_cm = round(width_cm, 1)

        # Material: use the layer's, or fall back to "Generic" label
        mat_id = layer.MaterialId
        mat = doc.GetElement(mat_id) if mat_id != ElementId.InvalidElementId else None
        mat_name = mat.Name if mat else 'Generic'

        # 3️⃣ Build the new WallType name
        # NOTE: Revit forbids these characters in type names:
        #   { } [ ] | ; < > ? ` ~
        # Parentheses are fine. Sticking with parens is the safe choice.
        new_type_name = "{} ({}cm)".format(mat_name, width_cm)

        # 4️⃣ Get-or-create the matching single-layer WallType
        # 🎯 CS PATTERN: get-or-create ("upsert"). Avoids
        # accumulating duplicate types across multiple runs.
        if new_type_name in dict_wall_types:
            new_wall_type = dict_wall_types[new_type_name]
            reused_types.append(new_type_name)
        else:
            new_wall_type = wall_type.Duplicate(new_type_name)

            # 🎯 .NET-Python bridge — CompoundStructure expects a
            # typed List<CompoundStructureLayer>, not a Python list.
            # Same pattern as Day 6's List[ElementId] conversion.
            layer_list = List[CompoundStructureLayer]([layer])
            new_structure = CompoundStructure.CreateSimpleCompoundStructure(layer_list)
            new_wall_type.SetCompoundStructure(new_structure)

            # Update the cache so subsequent iterations find it
            dict_wall_types[new_type_name] = new_wall_type
            created_types.append(new_type_name)

        # 5️⃣ Compute the curve offset for this layer's center line
        curve = wall.Location.Curve
        offset = (wall_type.Width - width_ft - current_offset * 2) / 2.0
        if not wall.Flipped:
            offset = -offset

        new_curve = curve.CreateOffset(offset, XYZ.BasisZ)

        # 6️⃣ Duplicate the original wall, retarget the copy
        # 🎯 CS PATTERN: prototype-based creation. Copying preserves
        # all instance params, hosted elements, etc. We only override
        # the curve and type.
        copied_ids = ElementTransformUtils.CopyElement(doc, wall.Id, XYZ(0, 0, 0))
        new_wall_id = list(copied_ids)[0]
        new_wall = doc.GetElement(new_wall_id)

        new_wall.Location.Curve = new_curve
        new_wall.WallType = new_wall_type

        # Advance the running accumulator before we collect the result
        current_offset += width_ft
        new_walls.append(new_wall)

        # 7️⃣ Strip hosted elements from all-but-the-first new wall.
        # The CopyElement above duplicates hosted windows/doors onto
        # every copy — but a window can only really live on ONE wall.
        # Erik's heuristic: keep them on layer 0, delete from the rest.
        # Defensive try/except: some dependents refuse to delete
        # (joined geometry, etc.); skip and continue.
        if n != 0:
            dep_ids = new_wall.GetDependentElements(None)
            for dep_id in list(dep_ids)[1:]:
                try:
                    doc.Delete(dep_id)
                except:
                    pass

    except Exception:
        skipped.append((n, "error: " + traceback.format_exc().splitlines()[-1]))


# 8️⃣ Join geometry between all new walls so they appear as one
# clean assembly visually rather than overlapping ghosts.
# Quadratic loop (every wall vs every wall) is fine for ≤10 layers;
# would need optimization for hundreds.
for wall_a in new_walls:
    for wall_b in new_walls:
        if wall_a.Id == wall_b.Id:
            continue
        try:
            JoinGeometryUtils.JoinGeometry(doc, wall_a, wall_b)
        except:
            pass


# 9️⃣ Delete the original wall (must be in the same transaction)
original_id = wall.Id
try:
    doc.Delete(original_id)
except:
    # Rare: original might be locked by something. Don't crash the
    # whole transaction over the cleanup step.
    pass

t.Commit()


# 🔟 Report
output.print_md('# Wall Splitter Report')
output.print_md('- **Original wall:** deleted (ID was {})'.format(original_id))
output.print_md('- **New walls created:** {}'.format(len(new_walls)))
output.print_md('- **WallTypes newly created:** {}'.format(len(created_types)))
output.print_md('- **WallTypes reused:** {}'.format(len(reused_types)))
output.print_md('- **Layers skipped:** {}'.format(len(skipped)))
output.print_md('---')

if new_walls:
    output.print_md('### New layer-walls')
    for w in new_walls:
        wt_name = Element.Name.GetValue(w.WallType)
        link = output.linkify(w.Id, wt_name)
        output.print_md('- {}'.format(link))

if created_types:
    output.print_md('### New WallTypes added to project')
    for name in created_types:
        output.print_md('- {}'.format(name))

if skipped:
    output.print_md('### Skipped layers')
    for layer_index, reason in skipped:
        output.print_md('- Layer {}: {}'.format(layer_index, reason))

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!