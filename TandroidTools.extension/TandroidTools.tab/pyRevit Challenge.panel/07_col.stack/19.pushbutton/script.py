# -*- coding: utf-8 -*-
__title__   = "19 - Wall Splitter"
__doc__     = """Version = 1.0
Date    = 05.09.2026
________________________________________________________________
Description:
Pick a multi-layer compound wall. The tool reads each layer's
material and thickness, creates a new single-layer WallType per
layer (or reuses one if it already exists), then duplicates the
original wall once per layer, sets each copy's curve to the
correct parallel offset, and assigns the matching single-layer
type. Original wall is deleted.

Result: one compound wall becomes N single-layer walls in the
exact same physical location, each individually editable.

Real use: split structural studs from envelope cladding for
multi-discipline coordination, or break a wall into layers when
phasing requires different layers in different scopes.
________________________________________________________________
How-To:
1. Save your project (this tool deletes the original wall).
2. Click Wall Splitter.
3. Pick a multi-layer wall.
4. Tool produces N single-layer walls; original is deleted.
________________________________________________________________
To-Do:
[FEATURE] - Multi-wall selection (apply to many walls at once)
[FEATURE] - Skip Membrane layers (they're zero-thickness and
            create degenerate WallTypes — currently we skip them)
[FEATURE] - Handle hosted elements (windows, doors) — they may
            end up on the wrong layer-wall after split
[FEATURE] - Option to keep original wall instead of deleting
[BUG]     - Curtain walls have no CompoundStructure; tool exits
            cleanly but with a clearer message would be better
________________________________________________________________
Last Updates:
- [05.09.2026] v1.0 Full splitter with WallType creation/reuse
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 19)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script, revit


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

def get_or_create_single_layer_wall_type(donor_wall_type, material, width_ft, type_name):
    """Find an existing WallType by name, or create a new one with a
    single layer of the given material and thickness.

    🎯 CS PATTERN: get-or-create (sometimes called "find-or-make"
    or "upsert"). Avoids creating duplicates when the resource
    already exists. Same idea as Django's get_or_create(),
    Rails' find_or_create_by(), or any "ensure exists" function.

    🎯 CS PATTERN: prototype-based creation.
    We don't construct a WallType from scratch — we Duplicate() an
    existing donor type, then modify the duplicate. This preserves
    all the parent's settings (graphic overrides, parameters, etc.)
    that we don't care about.
    """
    # Look for an existing WallType with the target name
    all_wall_types = FilteredElementCollector(doc).OfClass(WallType).ToElements()
    for wt in all_wall_types:
        if Element.Name.GetValue(wt) == type_name:
            return wt

    # None found — duplicate the donor and reshape into a single layer
    new_type = donor_wall_type.Duplicate(type_name)

    # Build a new CompoundStructure with one layer
    # CreateSimpleCompoundStructure takes a list of CompoundStructureLayer
    new_layer = CompoundStructureLayer(width_ft, MaterialFunctionAssignment.Structure, material.Id)
    new_structure = CompoundStructure.CreateSimpleCompoundStructure(
        List_of_layers([new_layer])
    )
    new_type.SetCompoundStructure(new_structure)
    return new_type


def List_of_layers(py_list):
    """Convert a Python list to the .NET List[CompoundStructureLayer]
    that CompoundStructure.CreateSimpleCompoundStructure expects.

    🎯 Same .NET-Python bridge pattern from Day 6's
    List[ElementId] conversion. Different type, same fix.
    """
    import clr
    clr.AddReference('System')
    from System.Collections.Generic import List
    return List[CompoundStructureLayer](py_list)


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ User picks the wall to split
with forms.WarningBar(title='Pick a multi-layer wall to split'):
    try:
        wall = revit.pick_element_by_category(BuiltInCategory.OST_Walls)
    except:
        script.exit()

if wall is None:
    forms.alert('No wall picked.', exitscript=True)


# 2️⃣ Read the wall's compound structure
wall_type = wall.WallType

# Curtain walls don't have CompoundStructure; bail clean
try:
    structure = wall_type.GetCompoundStructure()
    if structure is None:
        raise AttributeError("CompoundStructure is None")
    layers = list(structure.GetLayers())
except:
    forms.alert(
        'This wall has no compound structure (likely a curtain wall '
        'or stacked wall). Pick a regular layered wall.',
        exitscript=True,
    )

if len(layers) <= 1:
    forms.alert(
        'This wall only has one layer — nothing to split. '
        'Pick a multi-layer compound wall.',
        exitscript=True,
    )


# 3️⃣ Validate the geometry — must be a wall with a Curve location
if not isinstance(wall.Location, LocationCurve):
    forms.alert('This wall does not have a curve-based location.', exitscript=True)

original_curve = wall.Location.Curve
total_width = wall_type.Width
is_flipped = wall.Flipped


# 4️⃣ Transaction: walk layers, create types, duplicate walls
t = Transaction(doc, 'Wall Splitter')
t.Start()

new_walls_created = []
skipped_layers = []

# 🎯 CS PATTERN: running accumulator.
# current_offset tracks how far we've walked through the wall's
# thickness as we build each layer. Each iteration's offset depends
# on the cumulative width of all prior layers.
current_offset = 0.0

for n, layer in enumerate(layers):

    width_ft = layer.Width
    mat_id = layer.MaterialId

    # Skip membrane layers — they have zero or near-zero thickness
    # and creating a single-layer WallType from them produces an
    # invalid degenerate type
    if width_ft <= 0.0001:
        skipped_layers.append((n, "zero-thickness (membrane)"))
        continue

    # Skip layers with no material assigned
    if mat_id == ElementId.InvalidElementId:
        skipped_layers.append((n, "no material assigned"))
        continue

    material = doc.GetElement(mat_id)
    if material is None:
        skipped_layers.append((n, "material lookup returned None"))
        continue

    # Build the type name from material + thickness (in cm for readability)
    width_cm = UnitUtils.ConvertFromInternalUnits(width_ft, UnitTypeId.Centimeters)
    width_cm_rounded = round(width_cm, 1)
    new_type_name = "{} ({}cm) - Split".format(material.Name, width_cm_rounded)

    # Get or create the matching single-layer WallType
    try:
        new_wall_type = get_or_create_single_layer_wall_type(
            wall_type, material, width_ft, new_type_name
        )
    except Exception as e:
        skipped_layers.append((n, "type creation failed: {}".format(str(e))))
        continue

    # Compute this layer's curve offset.
    # The offset is measured from the wall's center curve to the
    # center of THIS layer. Total wall thickness extends from
    # -total_width/2 to +total_width/2; we walk from one face inward.
    # Layer center = (cumulative_outside_offset) + (this_layer_width / 2)
    layer_center_offset = (total_width / 2.0) - current_offset - (width_ft / 2.0)
    if is_flipped:
        layer_center_offset = -layer_center_offset

    # CreateOffset shifts the curve perpendicular to itself; the
    # axis argument (BasisZ) defines the rotation plane.
    new_curve = original_curve.CreateOffset(layer_center_offset, XYZ.BasisZ)

    # 🎯 CS PATTERN: prototype-based creation via copy.
    # Copying preserves params, hosted relationships, etc.
    copied_ids = ElementTransformUtils.CopyElement(doc, wall.Id, XYZ(0, 0, 0))
    new_wall_id = list(copied_ids)[0]
    new_wall = doc.GetElement(new_wall_id)

    # Apply the new curve and type
    new_wall.Location.Curve = new_curve
    new_wall.WallType = new_wall_type

    new_walls_created.append((new_wall, material.Name, width_cm_rounded))

    # Advance the running accumulator for the next layer
    current_offset += width_ft

# Delete the original wall (must happen inside the same transaction)
original_wall_id = wall.Id
doc.Delete(original_wall_id)

t.Commit()


# 5️⃣ Report
output.print_md('# Wall Splitter Report')
output.print_md('- **Original wall:** deleted (ID was {})'.format(original_wall_id))
output.print_md('- **New walls created:** {}'.format(len(new_walls_created)))
output.print_md('- **Layers skipped:** {}'.format(len(skipped_layers)))
output.print_md('---')

if new_walls_created:
    output.print_md('### New layer-walls')
    for new_wall, mat_name, width_cm in new_walls_created:
        link = output.linkify(new_wall.Id, '{} ({}cm)'.format(mat_name, width_cm))
        output.print_md('- {}'.format(link))

if skipped_layers:
    output.print_md('### Skipped layers')
    for layer_index, reason in skipped_layers:
        output.print_md('- Layer {}: {}'.format(layer_index, reason))

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!