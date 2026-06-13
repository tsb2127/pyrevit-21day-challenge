# -*- coding: utf-8 -*-
__title__   = "18 - 3D Cutter"
__doc__     = """Version = 1.0
Date    = 05.06.2026
________________________________________________________________
Description:
Pick one or more floors + a model line. The tool slices each
floor in two along a vertical plane through the line, recreates
both halves with the same type/level, copies all parameters
from the original, and deletes the original.

Multi-floor support: select 30 floors, run once, done. Useful
when a property boundary or zone change splits the same floor
plate on every level of a tower.
________________________________________________________________
How-To:
1. Click 3D Cutter.
2. Pick the floors to cut. Click "Finish" (top-left) when done.
3. Pick a model line that crosses every selected floor.
4. Tool produces two new floors per original, with parameters
   copied. Originals are deleted. Failures on individual floors
   are logged but don't stop the batch.
________________________________________________________________
To-Do:
[FEATURE] - Handle hosted elements (railings, floor-mounted
            objects) — currently they may end up orphaned.
[FEATURE] - Support cutting with multiple connected lines.
[BUG]     - If the line doesn't cross a floor's footprint, the
            half-space cut produces an invalid curve loop. The
            try/except catches it but the error message could
            be more helpful.
[CLEANUP] - Magic 10-foot Z-offset in get_line_plane assumes
            roughly horizontal lines.
________________________________________________________________
Last Updates:
- [05.06.2026] v1.0 Multi-floor batch + parameter copy + cleanup
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 18)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script, revit
import traceback

# .NET Imports — for the custom WarningBar color
import clr
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")
from System.Windows.Media import SolidColorBrush, Color


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
output = script.get_output()

# Custom WarningBar color so prompts don't get lost in Revit's UI noise
blue_brush = SolidColorBrush(Color.FromArgb(255, 30, 144, 255))  # DodgerBlue


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

def get_floor_solid(floor):
    """Pull the first non-trivial Solid out of a Floor's geometry."""
    opt = Options()
    for geo in floor.get_Geometry(opt):
        if isinstance(geo, Solid) and geo.Volume > 0:
            return geo
    return None


def get_line_plane(line):
    """Convert a model line into a vertical Plane that contains it.

    🎯 CS PATTERN: lifting a low-dimensional input into higher
    dimensions. A line is 1D. To cut a 3D solid we need a 2D
    plane. Three non-collinear points uniquely define a plane,
    so we use the line's two endpoints plus a third point lifted
    +Z above the midpoint.
    """
    crv = line.Location.Curve
    pt_start = crv.GetEndPoint(0)
    pt_end   = crv.GetEndPoint(1)
    pt_mid   = (pt_start + pt_end) / 2
    pt_lifted = XYZ(pt_mid.X, pt_mid.Y, pt_mid.Z + 10)
    return Plane.CreateByThreePoints(pt_start, pt_end, pt_lifted)


def get_top_face(solid):
    """Return the upward-facing planar face of a solid (normal == +Z)."""
    for face in solid.Faces:
        try:
            if face.FaceNormal.IsAlmostEqualTo(XYZ.BasisZ):
                return face
        except:
            # Curved/non-planar faces don't have a single FaceNormal — skip
            pass
    return None


def read_param_value(f_param):
    """Universal parameter reader — returns the right type for any
    parameter regardless of StorageType."""
    storage = f_param.StorageType
    if storage == StorageType.String:
        return f_param.AsString()
    if storage == StorageType.Double:
        return f_param.AsDouble()
    if storage == StorageType.Integer:
        return f_param.AsInteger()
    if storage == StorageType.ElementId:
        return f_param.AsElementId()
    return None


def get_original_p_values_as_dict(floor):
    """Snapshot every parameter on a floor into a dict {name: value}.

    🎯 CS PATTERN: dehydrate-then-rehydrate.
    Captures the source's state into a portable Python dict that
    survives the source being deleted. Same idea as Redux state
    snapshots, JSON serialization, Git stash, copy-paste.
    """
    dict_floor_param = {}
    for param in floor.Parameters:
        value = read_param_value(param)
        if value is not None:
            dict_floor_param[param.Definition.Name] = value
    return dict_floor_param


def set_p_values(floor, dict_params):
    """Write a parameter dict back to a floor. Skips read-only params
    and any param the target doesn't have. Defensive try/except per
    parameter — one bad write doesn't break the whole copy."""
    for param in floor.Parameters:
        try:
            param_name = param.Definition.Name
            if param_name not in dict_params:
                continue

            current_value = read_param_value(param)
            target_value = dict_params[param_name]

            if current_value != target_value:
                param.Set(target_value)
        except:
            # Some params reject writes silently (read-only computed
            # values, type-bound, etc.). Don't let one bad param break
            # the whole copy.
            pass


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Pick floors to cut (multi-select)
with forms.WarningBar(
    title='Select Floors To Cut (click Finish in top-left when ready)',
    background=blue_brush,
):
    try:
        floors = revit.pick_elements_by_category(BuiltInCategory.OST_Floors)
    except:
        script.exit()

if not floors:
    forms.alert("No floors selected. Please try again.", exitscript=True)


# 2️⃣ Pick the model line that defines the cut
with forms.WarningBar(title='Select the Line to cut along', background=blue_brush):
    try:
        line = revit.pick_element_by_category(BuiltInCategory.OST_Lines)
    except:
        script.exit()

if line is None:
    forms.alert("No line picked.", exitscript=True)

# Validate the line is a real line (Model or Detail), not some other OST_Lines weirdness
if type(line) not in [ModelLine, DetailLine]:
    forms.alert("Pick a straight Model Line or Detail Line.", exitscript=True)


# 3️⃣ Build the cutting planes (one per direction of the half-space)
plane_a = get_line_plane(line)
plane_b = Plane.CreateByNormalAndOrigin(-plane_a.Normal, plane_a.Origin)


# 4️⃣ Transaction: cut every floor, log per-floor failures
t = Transaction(doc, '3D Cutter')
t.Start()

success_count = 0
failure_log = []

for floor in floors:
    try:
        # Extract solid
        solid = get_floor_solid(floor)
        if solid is None:
            raise Exception("No valid Solid found on floor.")

        # Cut both halves
        solid_half_a = BooleanOperationsUtils.CutWithHalfSpace(solid, plane_a)
        solid_half_b = BooleanOperationsUtils.CutWithHalfSpace(solid, plane_b)

        # Get top faces
        top_a = get_top_face(solid_half_a)
        top_b = get_top_face(solid_half_b)
        if top_a is None or top_b is None:
            raise Exception("Cut produced an invalid half (line may not cross floor).")

        # Build curve loops + create new floors
        curves_a = top_a.GetEdgesAsCurveLoops()
        curves_b = top_b.GetEdgesAsCurveLoops()
        floor_type_id = floor.GetTypeId()
        level_id      = floor.LevelId

        new_floor_a = Floor.Create(doc, curves_a, floor_type_id, level_id)
        new_floor_b = Floor.Create(doc, curves_b, floor_type_id, level_id)

        # Snapshot original params, apply to both new floors
        param_snapshot = get_original_p_values_as_dict(floor)
        set_p_values(new_floor_a, param_snapshot)
        set_p_values(new_floor_b, param_snapshot)

        # Delete the original
        original_id = floor.Id
        doc.Delete(original_id)

        success_count += 1

    except Exception as e:
        failure_log.append({
            'floor_id': floor.Id,
            'message': str(e),
            'traceback': traceback.format_exc(),
        })

t.Commit()


# 5️⃣ Report
output.print_md('# 3D Cutter Report')
output.print_md('- **Floors selected:** {}'.format(len(floors)))
output.print_md('- **Successfully cut:** {}'.format(success_count))
output.print_md('- **Failed:** {}'.format(len(failure_log)))

if failure_log:
    output.print_md('---')
    output.print_md('### Failures')
    for fail in failure_log:
        output.print_md('- **Floor {}:** {}'.format(fail['floor_id'], fail['message']))

output.print_md('---')
output.print_md(
    'Hosted elements (railings, floor-mounted objects) may need '
    'manual reattachment. The original floors have been deleted.'
)

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!