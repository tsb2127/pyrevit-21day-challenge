# -*- coding: utf-8 -*-
__title__   = "20 - Pro Coordinator"
__doc__     = """Version = 1.0
Date    = 06.14.2026
________________________________________________________________
Description:
Pick a Family Type, collect every placed instance, and export
each instance's location coordinates to a CSV file. You choose
the coordinate system (Internal / Project / Survey) and the
units (meters / feet / millimeters).

Real use: hand a consultant a CSV of every diffuser, rack, or
fixture location in real-world survey coordinates for ingestion
into DCIM / GIS / commissioning software.
________________________________________________________________
How-To:
1. Click Pro Coordinator.
2. Pick a Family Type from the list.
3. Pick the coordinate system (Internal / Project / Survey).
4. Pick units (Meters / Feet / Millimeters).
5. CSV is written to your Documents folder.
________________________________________________________________
To-Do:
[FEATURE] - Import side: read a CSV of points and place a chosen
            family at each one (the return trip).
[FEATURE] - Multi-type export in one CSV with a Type column.
[FEATURE] - Include selected instance parameters as extra columns.
[CLEANUP] - Curve-based elements export their midpoint; expose a
            start/end/mid choice.
________________________________________________________________
Last Updates:
- [06.14.2026] v1.0 Family-type picker + coord/unit choice + CSV
- [06.12.2026] v0.1 POC - PointConverter sanity check
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 20)
PointConverter helper class by Erik Frits (LearnRevitAPI.com)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script
import os, csv, datetime


# ╔═╗╦  ╔═╗╔═╗╔═╗╔═╗╔═╗
# ║  ║  ╠═╣╚═╗╚═╗║╣ ╚═╗
# ╚═╝╩═╝╩ ╩╚═╝╚═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# Erik's helper classes — sealed black box (see POC for full notes).
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()


class CoordSys:
    Internal = 'Internal'
    Project  = 'Project'
    Survey   = 'Survey'


class PointConverter:
    pt_internal = None
    pt_survey   = None
    pt_project  = None

    def __init__(self, input_pt, coord_sys=CoordSys.Internal):
        srvTrans  = self._GetSurveyTransform()
        projTrans = self._GetProjectTransform()

        if coord_sys == CoordSys.Internal:
            self.pt_internal = input_pt
            self.pt_survey   = self._ApplyInverseTransformation(srvTrans,  self.pt_internal)
            self.pt_project  = self._ApplyInverseTransformation(projTrans, self.pt_internal)
        elif coord_sys == CoordSys.Project:
            self.pt_project  = input_pt
            self.pt_internal = self._ApplyTransformation(projTrans, self.pt_project)
            self.pt_survey   = self._ApplyInverseTransformation(srvTrans, self.pt_internal)
        elif coord_sys == CoordSys.Survey:
            self.pt_survey   = input_pt
            self.pt_internal = self._ApplyTransformation(srvTrans, self.pt_survey)
            self.pt_project  = self._ApplyInverseTransformation(projTrans, self.pt_internal)
        else:
            raise Exception("Wrong argument value for 'coord_sys' in PointConverter.")

    def get_XYZ(self, coord_sys, units):
        """Return this point in the requested system, converted to the
        requested units. Units come in as a UnitTypeId."""
        if   coord_sys == CoordSys.Internal: pt = self.pt_internal
        elif coord_sys == CoordSys.Project:  pt = self.pt_project
        elif coord_sys == CoordSys.Survey:   pt = self.pt_survey
        # 🎯 THE UNITS RULE: Revit API coordinates are ALWAYS feet
        # internally. Convert only at the display/export boundary.
        x = UnitUtils.ConvertFromInternalUnits(pt.X, units)
        y = UnitUtils.ConvertFromInternalUnits(pt.Y, units)
        z = UnitUtils.ConvertFromInternalUnits(pt.Z, units)
        return x, y, z

    def _GetSurveyTransform(self):
        return doc.ActiveProjectLocation.GetTotalTransform()

    def _GetProjectTransform(self):
        basePtLoc = next((l for l in FilteredElementCollector(doc)
                              .OfClass(ProjectLocation)
                              .WhereElementIsNotElementType()
                              .ToElements() if l.Name == "Project"), None)
        return basePtLoc.GetTotalTransform()

    def _ApplyInverseTransformation(self, t, pt):
        return t.Inverse.OfPoint(pt)

    def _ApplyTransformation(self, t, pt):
        return t.OfPoint(pt)


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

def get_element_point(elem):
    """Return an element's representative XYZ, or None if it has no
    usable location.

    🎯 Location is NOT uniform: family instances usually have a
    LocationPoint; walls/pipes have a LocationCurve. Guard for both,
    fall back to the curve midpoint, skip anything else."""
    loc = elem.Location
    if isinstance(loc, LocationPoint):
        return loc.Point
    if isinstance(loc, LocationCurve):
        curve = loc.Curve
        return curve.Evaluate(0.5, True)  # normalized midpoint
    return None


def get_type_label(type_elem):
    """Family + Type display name for the picker, e.g.
    'Desk: 1500x750mm'."""
    fam = type_elem.FamilyName if hasattr(type_elem, 'FamilyName') else ''
    name = Element.Name.GetValue(type_elem)
    return '{}: {}'.format(fam, name) if fam else name


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Pick a Family Type
# Collect placeable family symbols (FamilyInstance types). These are
# the things that get placed as instances and have point locations.
all_types = (FilteredElementCollector(doc)
             .OfClass(FamilySymbol)
             .WhereElementIsElementType()
             .ToElements())

if not all_types:
    forms.alert('No family types found in this project.', exitscript=True)

types_by_label = {}
for t in all_types:
    types_by_label[get_type_label(t)] = t

chosen_label = forms.SelectFromList.show(
    sorted(types_by_label.keys()),
    title='Pick a Family Type to export',
    button_name='Next',
    multiselect=False,
)
if not chosen_label:
    forms.alert('No type selected. Exiting.', exitscript=True)

chosen_type = types_by_label[chosen_label]


# 2️⃣ Collect every placed instance of that type
# 🎯 FamilyInstanceFilter finds instances of a specific symbol.
instances = (FilteredElementCollector(doc)
             .WherePasses(FamilyInstanceFilter(doc, chosen_type.Id))
             .WhereElementIsNotElementType()
             .ToElements())

if not instances:
    forms.alert('No placed instances of "{}" found.'.format(chosen_label),
                exitscript=True)


# 3️⃣ Pick coordinate system
coord_choice = forms.alert(
    'Which coordinate system?\n\n'
    'Internal = Revit origin (small numbers).\n'
    'Project = project base point.\n'
    'Survey = real-world / shared coordinates.',
    title='Coordinate system',
    options=[CoordSys.Survey, CoordSys.Project, CoordSys.Internal],
)
if not coord_choice:
    forms.alert('No coordinate system selected. Exiting.', exitscript=True)


# 4️⃣ Pick units
unit_map = {
    'Meters':      UnitTypeId.Meters,
    'Feet':        UnitTypeId.Feet,
    'Millimeters': UnitTypeId.Millimeters,
}
unit_choice = forms.alert(
    'Which units for the exported coordinates?',
    title='Units',
    options=['Meters', 'Feet', 'Millimeters'],
)
if not unit_choice:
    forms.alert('No units selected. Exiting.', exitscript=True)
units = unit_map[unit_choice]


# 5️⃣ Build the rows (read-only — no transaction needed)
headers = ['ElementId', 'X', 'Y', 'Z']
rows = []
skipped = 0

for inst in instances:
    pt = get_element_point(inst)
    if pt is None:
        skipped += 1
        continue
    converter = PointConverter(pt, CoordSys.Internal)
    x, y, z = converter.get_XYZ(coord_choice, units)
    rows.append([str(inst.Id), round(x, 4), round(y, 4), round(z, 4)])


# 6️⃣ Write the CSV
# 🎯 IronPython file-mode quirk: open with 'wb' (binary), not 'w',
# or you get a blank line between every row.
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
safe_name = chosen_label.replace(':', '-').replace(' ', '_').replace('/', '-')
filename  = 'Coords_{}_{}_{}.csv'.format(safe_name, coord_choice, timestamp)
csv_path  = os.path.join(os.path.expanduser('~'), 'Documents', filename)

with open(csv_path, 'wb') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)


# 7️⃣ Report
output.print_md('# Pro Coordinator Report')
output.print_md('- **Type:** {}'.format(chosen_label))
output.print_md('- **Coordinate system:** {}'.format(coord_choice))
output.print_md('- **Units:** {}'.format(unit_choice))
output.print_md('- **Instances exported:** {}'.format(len(rows)))
output.print_md('- **Skipped (no location):** {}'.format(skipped))
output.print_md('- **File:** `{}`'.format(csv_path))
output.print_md('---')
if rows:
    preview = rows[:10]
    output.print_table(
        table_data=preview,
        title='Preview (first {} rows)'.format(len(preview)),
        columns=headers,
    )

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!