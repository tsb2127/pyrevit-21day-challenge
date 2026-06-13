# pyRevit 21-Day Challenge

My attempt at [Erik Frits' 21-Day pyRevit Challenge](https://www.learnrevitapi.com/21-day-challenge/) — one Revit API tool per day, built with [pyRevit](https://github.com/pyrevitlabs/pyRevit) and Python.

## Requirements

- Autodesk Revit 2022+ (developed and tested on Revit 2026)
- [pyRevit](https://github.com/pyrevitlabs/pyRevit/releases) 4.8+

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/tsb2127/pyrevit-21day-challenge.git
   ```
2. In Revit, go to the **pyRevit tab → Settings → Custom Extension Directories** and add the path to the cloned repo folder.
3. Click **Save Settings and Reload**.
4. A new **TandroidTools** tab appears in the Revit ribbon with all the challenge tools.

## The Tools

| Day | Tool | What it does |
|-----|------|--------------|
| 01 | InPlace | Audit in-place families in the project |
| 02 | DoorSwing | Manage door swing parameters |
| 03 | NameSwapper | Batch rename elements |
| 04 | FlatSummarizer | Summarize flat/unit data |
| 05 | BIMpressionistPainter | Override element graphics in views |
| 06 | 3D Isolation Trap | Isolate selected group types in new 3D views |
| 07 | Tagless Shame List | Find untagged doors/windows across views |
| 08 | Warnings Snitch | Group, filter, and report project warnings |
| 09 | Auto-Planner | Auto-create cropped floor plans per room group |
| 10 | Lazy Sheets | Batch-create sheets with placed views |
| 11 | Parameter-Matched Picker | Selection filter that only allows elements matching a reference parameter value |
| 12 | ClickCounter | Selection/click utilities |
| 13 | Floorify | Floor creation helpers |
| 14 | Workset Police | Audit elements on wrong worksets |
| 15 | Workset Grabber | Select all elements on chosen worksets |
| 16 | Crash-n-Clash | Find intersecting elements between two categories |
| 17 | Shared Param Smuggler | Batch-import shared parameters with category, binding, and group settings |
| 18 | 3D Cutter | Slice floors in two along a model line using boolean geometry |
| 19 | Wall Splitter | Split compound walls into separate single-layer walls |
| 20 | Pro Coordinator | Convert and export element coordinates across Internal/Project/Survey systems |
| 21 | Excel Smuggler | Export Revit data to Excel and import edited values back |

## Repo Structure

```
pyrevit-21day-challenge/
├── TandroidTools.extension/
│   └── TandroidTools.tab/
│       ├── pyRevit Challenge.panel/    # the 21 daily tools
│       ├── pyRevit StarterKit 2.0.panel/
│       ├── Resources.panel/
│       └── Dev.panel/
├── lib/                                # shared/reusable code
└── extension.json
```

Each tool is in its own `.pushbutton` folder with a `script.py` containing a docstring and code organized into Imports / Variables / Functions / Main sections.

## Credits

Challenge and lessons by [Erik Frits](https://www.learnrevitapi.com/) (LearnRevitAPI.com). Implementations and modifications by [@tsb2127](https://github.com/tsb2127).

## Note

Personal learning project. Some tools delete or modify elements — test on a sandbox model first.
