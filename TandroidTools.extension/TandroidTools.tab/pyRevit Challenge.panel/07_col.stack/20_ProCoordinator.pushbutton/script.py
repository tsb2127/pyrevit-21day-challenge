# -*- coding: utf-8 -*-
__title__   = "Pro Coordinator (POC)"
__doc__     = """Version = 0.1 (Proof of Concept)
Date    = 06.12.2026
________________________________________________________________
Description:
POC — coordinate conversion sanity check.

Pick a point in the model, print its coordinates in all three
Revit coordinate systems (Internal / Project / Survey), in
meters. No exports, no transactions — just verify the
PointConverter helper class works in this project.

V1 will add: Family/Type picker, batch instance collection,
unit selection, and CSV export/import.
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 20 — POC)
PointConverter helper class by Erik Frits (LearnRevitAPI.com)"""

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


# ╔═╗╦  ╔═╗╔═╗╔═╗╔═╗╔═╗
# ║  ║  ╠═╣╚═╗╚═╗║╣ ╚═╗
# ╚═╝╩═╝╩ ╩╚═╝╚═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# Erik's helper classes — treat as a sealed black box.
# 🎯 CS PATTERN: facade. One class wraps four transforms, two unit
# conversions, and three coordinate systems behind a single obvious
# entry point. You hand it a point + which system it's in; it
# exposes all three systems in feet and meters as attributes.

class CoordSys:
    """🎯 CS PATTERN: enum-by-convention. IronPython 2 has no built-in
    Enum, so a class with string constants does the job. Prevents
    typo-bugs: CoordSys.Survey autocompletes; 'Survy' doesn't."""
    Internal = 'Internal'
    Project  = 'Project'
    Survey   = 'Survey'


class PointConverter:
    pt_internal = None
    pt_survey   = None
    pt_project  = None

    def __init__(self, input_pt, coord_sys=CoordSys.Internal):
        """Class for converting XYZ points between any Coordinate Systems.
        Args:
            :param input_pt:  The XYZ point (in FEET — Revit API internal units).
            :param coord_sys: Which system input_pt is expressed in
                              (CoordSys.Internal / .Project / .Survey)

        Example:
            pt = elem.Location.Point
            converter   = PointConverter(pt, CoordSys.Internal)
            pt_survey   = converter.pt_survey    # XYZ in FEET
            pt_survey_m = converter.pt_survey_m  # XYZ in Meters
        """
        # Get Systems Transforms
        srvTrans  = self._GetSurveyTransform()
        projTrans = self._GetProjectTransform()

        # 1️⃣ INPUT — INTERNAL COORDINATE SYSTEM
        if coord_sys == CoordSys.Internal:
            self.pt_internal = input_pt
            self.pt_survey   = self._ApplyInverseTransformation(srvTrans,  self.pt_internal)
            self.pt_project  = self._ApplyInverseTransformation(projTrans, self.pt_internal)

        # 2️⃣ INPUT — PROJECT COORDINATE SYSTEM
        elif coord_sys == CoordSys.Project:
            self.pt_project  = input_pt
            self.pt_internal = self._ApplyTransformation(projTrans, self.pt_project)
            self.pt_survey   = self._ApplyInverseTransformation(srvTrans, self.pt_internal)

        # 3️⃣ INPUT — SURVEY COORDINATE SYSTEM
        elif coord_sys == CoordSys.Survey:
            self.pt_survey   = input_pt
            self.pt_internal = self._ApplyTransformation(srvTrans, self.pt_survey)
            self.pt_project  = self._ApplyInverseTransformation(projTrans, self.pt_internal)

        else:
            raise Exception("Wrong argument value for 'coord_sys' in PointConverter class.")

        # Create Metric Points
        self.pt_internal_m = self._get_metric_XYZ(CoordSys.Internal)
        self.pt_project_m  = self._get_metric_XYZ(CoordSys.Project)
        self.pt_survey_m   = self._get_metric_XYZ(CoordSys.Survey)

    def print_in_metric(self, coord_sys, units=UnitTypeId.Meters):
        """Helper function to display coordinates in Metric System."""
        pt_m = self._get_metric_XYZ(coord_sys, units)
        print('[{}] XYZ: ({}m, {}m, {}m)'.format(coord_sys, pt_m.X, pt_m.Y, pt_m.Z))

    # ── INTERNAL HELPING METHODS ────────────────────────────────
    def _get_metric_XYZ(self, coord_sys, units=UnitTypeId.Meters):
        """Convert the point into Metric XYZ System.
        NB! Do not use the result with Revit API — it needs internal
        units (feet). This is for DISPLAY/EXPORT only."""
        # Get Point With Correct Coordinate System
        if   coord_sys == CoordSys.Internal: pt = self.pt_internal
        elif coord_sys == CoordSys.Project:  pt = self.pt_project
        elif coord_sys == CoordSys.Survey:   pt = self.pt_survey

        # Convert Values to Metric
        # 🎯 THE UNITS RULE: Revit API coordinates are ALWAYS in feet
        # internally, regardless of project display units.
        X_m = UnitUtils.ConvertFromInternalUnits(pt.X, units)
        Y_m = UnitUtils.ConvertFromInternalUnits(pt.Y, units)
        Z_m = UnitUtils.ConvertFromInternalUnits(pt.Z, units)
        return XYZ(X_m, Y_m, Z_m)

    def _GetSurveyTransform(self):
        """Gets the Active Project Location's Transform (Survey)."""
        return doc.ActiveProjectLocation.GetTotalTransform()

    def _GetProjectTransform(self):
        """Get the Project Base Point's Transform."""
        basePtLoc = next((l for l in FilteredElementCollector(doc)
                              .OfClass(ProjectLocation)
                              .WhereElementIsNotElementType()
                              .ToElements() if l.Name == "Project"), None)
        return basePtLoc.GetTotalTransform()

    def _ApplyInverseTransformation(self, t, pt):
        """Applies the INVERSE of the given Transform to the point.
        🎯 Transform.Inverse = 'go the other direction between the
        two coordinate frames'. Same math as world↔object space in
        3D graphics."""
        return t.Inverse.OfPoint(pt)

    def _ApplyTransformation(self, t, pt):
        """Applies the given Transform to the point."""
        return t.OfPoint(pt)


# ╔═╗╦═╗╔═╗╔═╗╔═╗  ╔═╗╔═╗  ╔═╗╔═╗╔╗╔╔═╗╔═╗╔═╗╔╦╗
# ╠═╝╠╦╝║ ║║ ║╠╣   ║ ║╠╣   ║  ║ ║║║║║  ║╣ ╠═╝ ║
# ╩  ╩╚═╚═╝╚═╝╚    ╚═╝╚    ╚═╝╚═╝╝╚╝╚═╝╚═╝╩   ╩
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Pick a Point in the model
# NOTE: PickPoint needs a work plane — run this from a FLOOR PLAN
# view, not a 3D view, or Revit will refuse the pick.
print("Pick a point in the model (use a floor plan view)...")
pt = uidoc.Selection.PickPoint()

print("\nRaw picked point (Internal system, FEET):")
print("  X={}, Y={}, Z={}".format(pt.X, pt.Y, pt.Z))


# 2️⃣ Convert Between Coordinate Systems
converter = PointConverter(pt, CoordSys.Internal)


# 3️⃣ Print the same physical location in all three systems (meters)
print("\nSame point, three coordinate systems, in METERS:")
converter.print_in_metric(coord_sys=CoordSys.Internal)
converter.print_in_metric(coord_sys=CoordSys.Project)
converter.print_in_metric(coord_sys=CoordSys.Survey)

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!