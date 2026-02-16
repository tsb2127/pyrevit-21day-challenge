# -*- coding: utf-8 -*-
#⬇️ Imports
from pyrevit import script

#📦 Variables
output = script.get_output()

#⚙️ Functions
def default_print(btn_name):
    # 👀 Print Message
    output.print_md('## ✨ You Clicked Button \'{btn_name}\' ✨'.format(btn_name=btn_name))  # <- Print MarkDown Heading 2
    output.print_md('---')
    output.print_md('⌨️ Hold **ALT + CLICK** to open the source code of this button. ')
    output.print_md('You can Duplicate, or use this placeholder for your own script.')
    output.print_md('---')
    output.print_md('*pyRevit StarterKit 2.0 was made by Erik Frits from LearnRevitAPI.com*')
    output.print_md('**Happy Coding!**')

#███████████████████████████████████████████████████████████████████████████
# Want to learn more about reusable code in pyRevit?
free_tutorial = 'https://www.LearnRevitAPI.com/resources/pyrevit-lib'
