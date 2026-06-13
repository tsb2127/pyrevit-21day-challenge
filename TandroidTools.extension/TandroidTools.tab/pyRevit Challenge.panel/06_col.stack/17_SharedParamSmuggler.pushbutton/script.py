# -*- coding: utf-8 -*-
__title__   = "17 - Shared Param Smuggler"
__doc__     = """Version = 1.1
Date    = 06.13.2026
________________________________________________________________
Description:
Batch-imports shared parameters from a .txt SharedParameterFile
into the active project. Two modes:
  - Same settings for all selected parameters (fast path), or
  - Per-parameter settings (different categories / binding /
    group for each parameter).

All user input is gathered into an import plan FIRST, then the
plan runs inside a single transaction.
________________________________________________________________
How-To:
1. Load your SharedParameterFile (Manage > Shared Parameters).
2. Click Shared Param Smuggler.
3. Pick which parameters to import.
4. Choose "Same for all" or "Per parameter".
5. Fill in binding / categories / group (once, or per param).
6. Review the report.
________________________________________________________________
To-Do:
[FEATURE] - "Varies by Group" detection for params that need it.
[FEATURE] - Import a config preset (JSON) so firms can ship a
            "load these params with these settings" file.
[FEATURE] - Let the per-param flow reuse the previous param's
            answers as defaults to cut clicks.
________________________________________________________________
Last Updates:
- [06.13.2026] v1.1 Per-parameter settings via plan-then-execute
- [05.08.2026] v1.0 Full importer with category + group pickers
- [05.07.2026] v0.1 POC - read SP file and inspect contents
________________________________________________________________
Author: Tandroid (LearnRevitAPI.com 21-day challenge, Day 17)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script

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
    """Names of all parameters already bound to the project (iterator pattern)."""
    loaded = []
    itor = doc.ParameterBindings.ForwardIterator()
    while itor.MoveNext():
        loaded.append(itor.Key.Name)
    return loaded


def get_shared_param_definitions(already_loaded_names):
    """Open the SharedParameterFile, return {display_label: ExternalDefinition}
    for params NOT already loaded."""
    sp_file = app.OpenSharedParameterFile()
    if not sp_file:
        forms.alert(
            'No SharedParameterFile is loaded.\n\n'
            'Manage tab > Shared Parameters > Browse to your .txt file, '
            'then run this tool again.',
            exitscript=True,
        )

    available = {}
    for group in sp_file.Groups:
        for p_def in group.Definitions:
            if p_def.Name in already_loaded_names:
                continue
            available['[{}] {}'.format(group.Name, p_def.Name)] = p_def

    if not available:
        forms.alert('Every parameter in the file is already loaded. '
                    'Nothing to import.', exitscript=True)
    return available


def ask_binding_kind(title):
    """Instance vs Type. Returns 'Instance'/'Type' or None if cancelled."""
    return forms.alert(
        'Import as Instance or Type parameter?\n\n'
        'Instance = each placed element has its own value.\n'
        'Type = all elements of a type share one value.',
        title=title,
        options=['Instance', 'Type'],
    )


def ask_category_set(title):
    """Pick categories. Returns (CategorySet, [names]) or (None, None)."""
    all_cats = [c for c in doc.Settings.Categories if c.AllowsBoundParameters]
    cats_by_name = {c.Name: c for c in all_cats}

    selection = forms.SelectFromList.show(
        sorted(cats_by_name.keys()),
        multiselect=True,
        title=title,
        button_name='Confirm categories',
    )
    if not selection:
        return None, None

    cat_set = CategorySet()
    for name in selection:
        cat_set.Insert(cats_by_name[name])
    return cat_set, selection


def ask_param_group(title):
    """Pick the Properties-panel group. Returns (group_id, label) or (None, None).
    Handles the 2024+ BuiltInParameterGroup -> GroupTypeId API change."""
    common_groups = [
        ('Identity Data',          'PG_IDENTITY_DATA',    'IdentityData'),
        ('Construction',           'PG_CONSTRUCTION',     'Construction'),
        ('Materials and Finishes', 'PG_MATERIALS',        'Materials'),
        ('Dimensions',             'PG_GEOMETRY',         'Geometry'),
        ('Analysis Results',       'PG_ANALYSIS_RESULTS', 'AnalysisResults'),
        ('Phasing',                'PG_PHASING',          'Phasing'),
        ('Other',                  'PG_DATA',             'Data'),
    ]
    selection = forms.SelectFromList.show(
        [name for name, _, _ in common_groups],
        multiselect=False,
        title=title,
        button_name='Confirm group',
    )
    if not selection:
        return None, None

    for label, old_name, new_name in common_groups:
        if label == selection:
            if rvt_year < 2024:
                return getattr(BuiltInParameterGroup, old_name), label
            return getattr(GroupTypeId, new_name), label
    return None, None


def gather_settings(prompt_label):
    """Gather ONE complete settings bundle (binding + group + summary).
    Returns a dict, or None if the user cancels any step.

    🎯 This is the unit of the 'plan'. It does NO document modification
    and opens NO transaction. It only collects choices."""
    kind = ask_binding_kind('Binding for {}'.format(prompt_label))
    if not kind:
        return None

    cat_set, cat_names = ask_category_set('Categories for {}'.format(prompt_label))
    if not cat_set:
        return None

    p_group, group_label = ask_param_group('Group for {}'.format(prompt_label))
    if not p_group:
        return None

    if kind == 'Instance':
        binding = app.Create.NewInstanceBinding(cat_set)
    else:
        binding = app.Create.NewTypeBinding(cat_set)

    return {
        'binding': binding,
        'p_group': p_group,
        'kind': kind,
        'cat_names': cat_names,
        'group_label': group_label,
    }


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# 1️⃣ Find what's loaded, open the file, pick params
loaded_names = get_loaded_parameter_names()
dict_p_def   = get_shared_param_definitions(loaded_names)

selection = forms.SelectFromList.show(
    sorted(dict_p_def.keys()),
    multiselect=True,
    title=__title__,
    button_name='Next: choose settings',
)
if not selection:
    forms.alert('No parameters selected. Exiting.', exitscript=True)


# 2️⃣ PLANNING PHASE - build the import plan (no transaction yet)
# 🎯 default-vs-override: fast path applies one bundle to all; the
# per-param path gathers a bundle for each. Either way we end up with
# a list of jobs to execute.
mode = forms.alert(
    'How should settings be applied?\n\n'
    'Same for all = one set of binding/categories/group for every param.\n'
    'Per parameter = configure each parameter separately.',
    title='Settings mode',
    options=['Same for all', 'Per parameter'],
)
if not mode:
    forms.alert('No mode selected. Exiting.', exitscript=True)

jobs = []     # each job: (label, ExternalDefinition, settings_dict)
skipped = []  # params the user cancelled out of (per-param mode)

if mode == 'Same for all':
    settings = gather_settings('all selected parameters')
    if not settings:
        forms.alert('Settings cancelled. Exiting.', exitscript=True)
    for label in selection:
        jobs.append((label, dict_p_def[label], settings))

else:  # Per parameter
    for label in selection:
        settings = gather_settings(label)
        if not settings:
            # Cancelling one param skips just that param, not the whole run
            skipped.append(label)
            continue
        jobs.append((label, dict_p_def[label], settings))

if not jobs:
    forms.alert('No parameters configured for import. Exiting.', exitscript=True)


# 3️⃣ EXECUTION PHASE - run the plan in one transaction
# 🎯 plan-then-execute: every choice is already made; the transaction
# just applies the list. Simple, fast, and either-succeeds-or-reports.
imported = []
failed   = []

t = Transaction(doc, __title__)
t.Start()

for label, p_def, settings in jobs:
    try:
        ok = doc.ParameterBindings.Insert(p_def, settings['binding'], settings['p_group'])
        row = [p_def.Name, settings['kind'],
               ', '.join(sorted(settings['cat_names'])), settings['group_label']]
        if ok:
            imported.append(row)
        else:
            failed.append([p_def.Name, 'Insert returned False (already bound or rejected)'])
    except Exception as e:
        failed.append([p_def.Name, str(e)])

t.Commit()


# 4️⃣ Report
output.print_md('# Shared Param Smuggler Report')
output.print_md('- **Mode:** {}'.format(mode))
output.print_md('- **Imported:** {}'.format(len(imported)))
output.print_md('- **Failed:** {}'.format(len(failed)))
output.print_md('- **Skipped:** {}'.format(len(skipped)))
output.print_md('---')

if imported:
    output.print_table(
        table_data=imported,
        title='Imported',
        columns=['Parameter', 'Binding', 'Categories', 'Group'],
    )

if failed:
    output.print_table(
        table_data=failed,
        title='Failed',
        columns=['Parameter', 'Reason'],
    )

if skipped:
    output.print_md('### Skipped (cancelled during setup)')
    for label in skipped:
        output.print_md('- {}'.format(label))

#███████████████████████████████████████████████████████████████████████████
# Happy Coding!