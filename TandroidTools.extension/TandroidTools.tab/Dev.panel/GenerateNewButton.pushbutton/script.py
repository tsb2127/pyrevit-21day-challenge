# -*- coding: utf-8 -*-
__title__   = "Generate New Buttons"
__doc__     = """Version = 1.0
Date    = 01.01.2026
________________________________________________________________
Description:

pyRevit Pushbutton Generator.
________________________________________________________________
How-To:

- Click Button
- Provide bew button Names (Use comma, to provide multiple buttons)
- Wait a few sec until new buttons show up
________________________________________________________________
Last Updates:

- [20.01.2026] v1.0 - Release
________________________________________________________________
Author: Erik Frits (from LearnRevitAPI.com)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from pyrevit.loader import sessionmgr # To Reload pyRevit
from pyrevit import forms
import os, shutil

# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝ FUNCTIONS
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
def replace_title(path_script, title):
    """Simple function to replace __title__=... inside script.py file"""
    title = title.replace('.pushbutton', '')

    with open(path_script, 'r') as f:               # READ
        data = f.readlines()

    for n, line in enumerate(data):                 # FIND/REPLACE
        if line.startswith('__title__'):
            data[n] = '__title__ = "{}"\n'.format(title)

    # Rewrite Script
    with open(path_script, 'w') as f:               # RE-WRITE
        f.writelines(data)

def ask_button_names():
    """Function to prompt user to provide Button Names"""
    user_input = forms.ask_for_string(default= "Button_A, Button_B",
                                      prompt = 'Provide New Button Names (Use coma for multiple buttons):',
                                      title  = 'Generate New pyRevit Buttons')


    #🚨 Ensure User Input
    if not user_input:
        forms.alert('No Button Name Provided.\nPlease Try Again', exitscript=True)

    input_btn_names = [name.strip() for name in user_input.split(',')]

    #🚨 Ensure .pushbutton suffix
    btn_names = [btn_name if '.pushbutton' in btn_name
                          else btn_name+'.pushbutton'
                          for btn_name in input_btn_names ]

    # Return list of New Buttons Absolute Paths
    return [os.path.join(path_dev, btn_name) for btn_name in btn_names]


def create_button(abs_path_btn):
    """Function to create a new .pushbutton based on a template in provided location"""
    btn_title = os.path.basename(abs_path_btn)

    # Ensure Unique Button Name
    if os.path.exists(abs_path_btn):
        print('[WARNING] Button "{}" already exists. It will not be created.'.format(btn_title))
        return
    try:
        shutil.copytree(path_template, abs_path_btn)  # Duplicate Templatee
        path_new_button_script = os.path.join(abs_path_btn, 'script.py')  # Find Script.py Path
        replace_title(path_new_button_script, btn_title)  # Rename __title__
    except:
        print("[ERROR] Couldn't duplicate pushbutton template. Please verify button name and try again.")
        import traceback
        print(traceback.format_exc())


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝ MAIN
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
#1️⃣ Find Necessary Paths
path_script     = os.path.abspath(__file__)                     # ...Dev.panel/Button.pushbutton/script.py
path_pushbutton = os.path.dirname(path_script)                  # ...Dev.panel/Button.pushbutton
path_template   = os.path.join(path_pushbutton, 'template')     # ...Dev.panel/Button.pushbutton/template
path_dev        = os.path.dirname(path_pushbutton)              # ...Dev.panel

#2️⃣ Ask User Input + Verify
paths_new_buttons = ask_button_names()

#3️⃣ Duplicate PushButton Template + Rename
for path_btn in paths_new_buttons:
    create_button(path_btn)

#5️⃣ Reload pyRevit
sessionmgr.reload_pyrevit()


#███████████████████████████████████████████████████████████████████████████
# 🚨 𝗧𝗵𝗶𝘀 𝗰𝗼𝗱𝗲 𝗼𝗻𝗹𝘆 𝘀𝗼𝗹𝘃𝗲𝘀 𝗼𝗻𝗲 𝗽𝗿𝗼𝗯𝗹𝗲𝗺...
# 𝘆𝗼𝘂 𝗰𝗮𝗻 𝗹𝗲𝗮𝗿𝗻 𝗵𝗼𝘄 𝘁𝗼 𝘀𝗼𝗹𝘃𝗲 𝗺𝗮𝗻𝘆 𝗼𝗳 𝘆𝗼𝘂𝗿𝘀!
visit = 'www.LearnRevitAPI.com/learn' #👈👈👈
