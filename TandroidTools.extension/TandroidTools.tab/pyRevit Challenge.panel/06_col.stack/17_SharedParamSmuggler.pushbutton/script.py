# -*- coding: utf-8 -*-
__title__   = "17 - Shared Param Smuggler"
__doc__     = """Version = 1.0
Date    = 05.08.2026
________________________________________________________________
Description:
Batch-imports shared parameters from a .txt SharedParameterFile
into the active project. Asks the user once for: which params
to import, Instance vs Type, target categories, and parameter
group. Then imports them all in one transaction.

Replaces a ~30-minute manual chore (Manage > Project Parameters
> Add > pick category > pick group > repeat for every param)
with a ~30-second batch operation. Useful at the start of every
new project, after a firm's shared param library updates, or
when standardizing across templates.
________________________________________________________________
How-To:
1. Make sure your SharedParameterFile is loaded:
   Manage tab > Shared Parameters > Browse to your .txt file.
2. Click Shared Param Smuggler.
3. Pick which parameters to import.
4. Pick Instance or Type.
5. Pick target categories (multi-select).
6. Pick the parameter group (where it appears in Properties).
7. Done. Review the report.
________________________________________________________________
To-Do:
[FEATURE] - Per-parameter settings (different categories per
            param) instead of one-size-fits-all.
[FEATURE] - Detect "Varies by Group" requirement automatically
            for params that need it.
[FEATURE] - Import a config preset (JSON) so firms can ship a
            "import these 30 params with these settings" file.
[CLEANUP] - The PG_ANALYSIS_RESULTS / GroupTypeId.AnalysisResults
            switch is hardcoded; user selection now overrides.
________________________________________________________________
Last Updates:
- [05.08.2026] v1.0 Full importer with category + group pickers
- [05.07.2026] v0.1 POC — read SP file and inspect contents
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 17)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script

# .NET Imports
import clr
clr.AddReference('System')
from System.Collections.Generic import List


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc      = __revit__.ActiveUIDocument.Document
uidoc    = __revit__.ActiveUIDocument
app      = __revit__.Application
output   = script.get_output()
rvt_year = int(app.VersionNumber)


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

def get_loaded_parameter_names():
    """Return the names of all parameters currently bound to the project.

    🎯 CS PATTERN: iterator pattern.
    BindingMap doesn't support `for x in bm` directly; it exposes a
    .NET-style ForwardIterator with .MoveNext() and .Key. Same shape
    as Java/C# iterators or Python generators under the hood — a
    cursor that walks the collection one item at a time.
    """
    loaded = []
    bm = doc.ParameterBindings
    itor = bm.ForwardIterator()
    while itor.MoveNext():
        definition = itor.Key
        loaded.append(definition.Name)
    return loaded


def get_shared_param_definitions(already_loaded_names):
    """Open the active SharedParameterFile and return a dict of
    {display_label: ExternalDefinition} for every param NOT already
    loaded in the project.

    Filtering already-loaded params prevents duplicate imports
    (which would silently fail anyway, but cluttering the picker
    with already-imported items is bad UX).
    """
    sp_file = app.OpenSharedParameterFile()
    if not sp_file:
        forms.alert(
            'No SharedParameterFile is loaded.\n\n'
            'In Revit: Manage tab > Shared Parameters > Browse to your .txt file.\n'
            'Then run this tool again.',
            exitscript=True,
        )

    available = {}
    for group in sp_file.Groups:
        for p_def in group.Definitions:
            if p_def.Name in already_loaded_names:
                continue
            label = '[{}] {}'.format(group.Name, p_def.Name)
            available[label] = p_def

    if not available:
        forms.alert(
            'Every parameter in your SharedParameterFile is already '
            'loaded in this project. Nothing to import.',
            exitscript=True,
        )

    return available


def ask_user_for_category_set():
    """Ask the user to pick which categories the new parameters apply to.
    Returns a CategorySet object ready to feed into a Binding."""
    all_cats = [
        cat for cat in doc.Settings.Categories
        if cat.AllowsBoundParameters
    ]
    cats_by_name = {cat.Name: cat for cat in all_cats}

    selection = forms.SelectFromList.show(
        sorted(cats_by_name.keys()),
        multiselect=True,
        title='Select target categories',
        button_name='Confirm categories',
    )

    if not selection:
        forms.alert('No categories selected. Exiting.', exitscript=True)

    cat_set = CategorySet()
    for cat_name in selection:
        cat_set.Insert(cats_by_name[cat_name])
    return cat_set, selection


def ask_user_for_param_group():
    """Let the user pick which Properties-panel group the imported
    params show up under. Critical for clean models — without this,
    every imported param dumps into 'Analysis Results' regardless
    of what it actually is.

    🎯 CS PATTERN: API compatibility shim, again.
    Pre-2024: BuiltInParameterGroup enum.
    2024+:    GroupTypeId class (ForgeTypeId-style).
    Same logical concept, two different API shapes.
    """
    # Curated list of the most common groups (full list is huge).
    # Order matches Revit's Properties panel ordering.
    common_groups = [
        ('Identity Data',     'PG_IDENTITY_DATA',     'IdentityData'),
        ('Construction',      'PG_CONSTRUCTION',      'Construction'),
        ('Materials and Finishes', 'PG_MATERIALS',    'Materials'),
        ('Dimensions',        'PG_GEOMETRY',          'Geometry'),
        ('Analytical',        'PG_ANALYTICAL_MODEL',  'AnalyticalModel'),
        ('Analysis Results',  'PG_ANALYSIS_RESULTS',  'AnalysisResults'),
        ('Energy Analysis',   'PG_ENERGY_ANALYSIS',   'EnergyAnalysis'),
        ('Phasing',           'PG_PHASING',           'Phasing'),
        ('Other',             'PG_DATA',              'Data'),
    ]

    selection = forms.SelectFromList.show(
        [name for name, _, _ in common_groups],
        multiselect=False,
        title='Where should these params show up in the Properties panel?',
        button_name='Confirm group',
    )

    if not selection:
        forms.alert('No parameter group selected. Exiting.', exitscript=True)

    # Find the matching tuple
    for label, old_name, new_name in common_groups:
        if label == selection:
            if rvt_year < 2024:
                return getattr(BuiltInParameterGroup, old_name)
            else:
                return getattr(GroupTypeId, new_name)

    # Fallback (shouldn't reach here)
    if rvt_year < 2024:
        return BuiltInParameterGroup.PG_DATA
    else:
        return GroupTypeId.Data


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Find what's already loaded so we don't show duplicates
loaded_names = get_loaded_parameter_names()


# 2️⃣ Open the SharedParameterFile, build pickable list
dict_p_def = get_shared_param_definitions(loaded_names)


# 3️⃣ User picks which params to import
selection = forms.SelectFromList.show(
    sorted(dict_p_def.keys()),
    multiselect=True,
    title=__title__,
    button_name='Import shared parameters',
)
if not selection:
    forms.alert('No shared parameters selected to import. Exiting.', exitscript=True)

p_def_to_load = [dict_p_def[label] for label in selection]


# 4️⃣ User picks Instance vs Type
sel_binding_kind = forms.alert(
    'Import as Instance or Type parameter?\n\n'
    'Instance = each placed element gets its own value (e.g., Mark).\n'
    'Type = all elements of a type share one value (e.g., Fire Rating).',
    options=['Instance', 'Type'],
)
if not sel_binding_kind:
    forms.alert('No binding kind selected. Exiting.', exitscript=True)


# 5️⃣ User picks target categories
cat_set, selected_cat_names = ask_user_for_category_set()


# 6️⃣ Build the actual Binding object
if sel_binding_kind == 'Instance':
    binding = app.Create.NewInstanceBinding(cat_set)
else:
    binding = app.Create.NewTypeBinding(cat_set)


# 7️⃣ User picks the parameter group (where it shows in Properties)
p_group = ask_user_for_param_group()


# 8️⃣ Run the import inside a transaction
imported = []
failed = []

t = Transaction(doc, __title__)
t.Start()

for p_def in p_def_to_load:
    try:
        success = doc.ParameterBindings.Insert(p_def, binding, p_group)
        if success:
            imported.append(p_def.Name)
        else:
            failed.append((p_def.Name, "Insert returned False (likely already bound or rejected)"))
    except Exception as e:
        failed.append((p_def.Name, str(e)))

t.Commit()


# 9️⃣ Report
output.print_md('# Shared Param Smuggler Report')
output.print_md('- **Source file:** {}'.format(app.OpenSharedParameterFile().Filename))
output.print_md('- **Binding:** {} parameter'.format(sel_binding_kind))
output.print_md('- **Categories:** {}'.format(', '.join(sorted(selected_cat_names))))
output.print_md('- **Imported:** {}'.format(len(imported)))
output.print_md('- **Failed:**   {}'.format(len(failed)))
output.print_md('---')

if imported:
    output.print_md('### Imported successfully')
    for name in imported:
        output.print_md('- {}'.format(name))

if failed:
    output.print_md('### Failed')
    for name, reason in failed:
        output.print_md('- **{}**: {}'.format(name, reason))

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!