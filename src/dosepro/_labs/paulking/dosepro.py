# Copyright (C) 2019 Paul King

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version (the "AGPL-3.0+").

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License and the additional terms for more
# details.

# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# ADDITIONAL TERMS are also included as allowed by Section 7 of the GNU
# Affero General Public License. These additional terms are Sections 1, 5,
# 6, 7, 8, and 9 from the Apache License, Version 2.0 (the "Apache-2.0")
# where all references to the definition "License" are instead defined to
# mean the AGPL-3.0+.

# You should have received a copy of the Apache-2.0 along with this
# program. If not, see <http://www.apache.org/licenses/LICENSE-2.0>.

""" Graphical User Interface for Profile Class """

import os
import sys
import tkinter as tk
from tkinter.filedialog import askopenfilename
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

from functools import partial

if "dosepro\dosepro" in __file__:
    add_path = os.path.abspath(os.path.join(__file__, '..','..','..','..'))
    add_path = os.path.join(add_path, 'src', 'dosepro', '_labs', 'paulking')
    sys.path.insert(0,add_path)
    from profile import Profile
else:
    from pymedphys._labs.paulking.profile import Profile

class Color():
    def __init__(self):
        self.palette = ['red', 'green', 'orange', 'blue', 'yellow', 'purple1', 'black'
                        'red', 'green', 'orange', 'blue', 'yellow', 'purple1', 'black']
        self.from_palette = (c for c in self.palette)
        self.current = next(self.from_palette)
    def get(self):
        return self.current
    def next(self):
        self.current = next(self.from_palette)
    def reset(self):
        self.__init__()

class Menu(tk.Frame):
    def __init__(self, master):
        menu = tk.Menu(root)
        root.config(menu=menu)

        def file_menu():
            filemenu = tk.Menu(menu)
            menu.add_cascade(label="File", menu=filemenu)
            ## =====
            import_submenu = tk.Menu(filemenu)  ## =====
            import_submenu.add_command(label="Profiler", command=master.menu_file_import_profiler)
            import_submenu.add_command(label="Film", command=master.menu_file_import_film)
            import_submenu.add_command(label="Pulse", command=master.menu_import_pulse)
            filemenu.add_cascade(label='Import ...', menu=import_submenu)
            ## =====
            filemenu.add_command(label="Clear Selected", command=master.file_clr)
            ## =====
            filemenu.add_command(label="Clear All", command=master.menu_file_clear_all)
            ## =====
            filemenu.add_command(label="Exit", command=master._quit)
        file_menu()

        def edit_menu():
            editmenu = tk.Menu(menu)
            menu.add_cascade(label="Edit", menu=editmenu)
            ## =====
            resample_submenu = tk.Menu(editmenu)  
            resample_submenu.add_command(label="X", command=master.menu_resample_x)
            resample_submenu.add_command(label="Y", command=self.menu_stub)
            editmenu.add_cascade(label='Resample ...', menu=resample_submenu)
            ## =====    
            normalise_submenu = tk.Menu(editmenu)
            normalise_submenu.add_command(label="X", command=self.menu_stub)
            normalise_submenu.add_command(label="Y", command=self.menu_stub)
            editmenu.add_cascade(label='Normalise ...', menu=normalise_submenu)
            ## =====
            editmenu.add_command(label="Flip", command=self.menu_stub)
            ## =====
            editmenu.add_command(label="Symmetrise", command=self.menu_stub)
        edit_menu()

        def get_menu():
            getmenu = tk.Menu(menu)
            menu.add_cascade(label="Get", menu=getmenu)
            ## =====    
            value_submenu = tk.Menu(getmenu)
            value_submenu.add_command(label="X", command=self.menu_stub)
            value_submenu.add_command(label="Y", command=self.menu_stub)
            getmenu.add_cascade(label='Value ...', menu=value_submenu)
            ## =====
            getmenu.add_command(label="Edges", command=self.menu_stub)
            ## =====
            getmenu.add_command(label="Flatness", command=self.menu_stub)
            ## =====
            getmenu.add_command(label="Symmetry", command=self.menu_stub)
            # ## =====
            segment_submenu = tk.Menu(getmenu)
            segment_submenu.add_command(label="Defined", command=self.menu_stub)
            segment_submenu.add_command(label="Umbra", command=self.menu_stub)
            segment_submenu.add_command(label="Penumbra", command=self.menu_stub)
            segment_submenu.add_command(label="Shoulders", command=self.menu_stub)
            segment_submenu.add_command(label="Tails", command=self.menu_stub)
            getmenu.add_cascade(label='Segment ...', menu=segment_submenu)
        get_menu()

        def help_menu():
            helpmenu = tk.Menu(menu)
            menu.add_cascade(label="Help", menu=helpmenu)
            helpmenu.add_command(label="About...", command=master.about)
        help_menu()

    def menu_stub(self):
        pass

class Application(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        root.wm_title("Profile Tool")

        selector_frame = tk.Frame(self, width=5, height=100, background="bisque")
        graph_frame = tk.Frame(self, width=90, height=100, background="bisque")
        selector_frame.pack(side=tk.LEFT)
        graph_frame.pack(side=tk.RIGHT)

        fig = Figure(figsize=(6, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.subplot = fig.add_subplot(111)
        self.toolbar = NavigationToolbar2Tk(self.canvas, graph_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas.mpl_connect("key_press_event", self.on_key_press)

        ## self.status
        self.status = tk.StringVar() 
        self.status_bar = tk.Frame(master=graph_frame, relief=tk.RIDGE)
        self.status_label=tk.Label(self.status_bar, bd=1, relief=tk.FLAT, anchor=tk.W, 
                                   textvariable=self.status, 
                                   font=('arial',10,'normal'))
        self.status_label.pack(fill=tk.X, expand=True, side=tk.LEFT) 
        self.status_bar.pack(fill=tk.X, expand=False, side=tk.LEFT)
        self.status.set("__init__")

        self.color = Color()
        self.menu = Menu(self)

        self.profiles = []

        self.data_folder = os.path.join(str.split(__file__, 'src')[0], 
                           'tests','test_labs', 'test_paulking', 'data')

        self.buttons = []
        self.selector = tk.Frame(selector_frame)
        self.selector.pack(side=tk.TOP, fill="both", expand=True)
        self.selected_profile = tk.IntVar(value=0)
        self.update('__init__')
        self.canvas.draw()

    def set_active_profile(self, i):
        for J in range(len(self.buttons)):
            self.buttons[J].config(relief=tk.RAISED)    
        self.selected_profile.set(i)
        self.buttons[i].config(relief=tk.SUNKEN)

    def update(self, msg):
        selected_profile = self.selected_profile.get()
        self.color.reset()
        self.subplot.cla()
        self.buttons = []
        for button in self.selector.winfo_children():
            button.destroy()
        selector_title = tk.Label(master=self.selector, width=10, 
                                  bg='white', text='Selector')
        selector_title.pack(side="top", fill="both", expand=True)
        for i,profile in enumerate(self.profiles):
            self.subplot.plot(profile.x, profile.y, color=self.color.get())
            button = tk.Button(master=self.selector,
                        bg=self.color.get(), text=str(i), width=10,
                        command=partial(self.set_active_profile, i))
            button.pack(side=tk.TOP, fill='both')
            self.buttons.append(button)
            self.color.next()
        self.status.set(msg)
        self.canvas.draw()

    def menu_file_import_film(self):
        filename = askopenfilename(
            initialdir=self.data_folder, title="Film File",
            filetypes=(("Film Files", "*.png"), ("all files", "*.*")))
        self.profiles.append(Profile().from_narrow_png(filename))
        self.update('menu_file_import_film')
        self.set_active_profile(len(self.profiles)-1)

    def menu_file_import_profiler(self):
        filename = askopenfilename(
            initialdir=self.data_folder, title="SNC Profiler",
            filetypes=(("Profiler Files", "*.prs"), ("all files", "*.*")))
        self.profiles.append(Profile().from_snc_profiler(filename, 'rad'))
        self.profiles.append(Profile().from_snc_profiler(filename, 'tvs'))
        self.update('menu_file_import_profiler')
        self.set_active_profile(len(self.profiles)-1)

    def menu_import_pulse(self):
        pulse_window = tk.Tk()
        pulse_window.title("Pulse Parameters")
        pulse_window.grid()
        variables = []
        params = [('Centre',0.0), ('Width',10.0), ('Start',-12.0), ('End',12.0), ('Step',0.1)]
        for i,(l,d) in enumerate(params):
            variable = tk.DoubleVar(pulse_window, value=d)
            variables.append(variable)
            label = tk.Label(pulse_window, text=l)
            entry = tk.Entry(pulse_window, width=10, textvariable=variable)
            label.grid(column=0, row=i, sticky=tk.E)
            entry.grid(column=1, row=i)
        def OK():
            p = [v.get() for v in variables]
            p = [p[0], p[1], (p[2], p[3]), p[4]]
            self.profiles.append(Profile().from_pulse(*p))
            self.selected_profile.set(len(self.profiles)-1)
            self.update('menu_import_pulse')
            self.set_active_profile(len(self.profiles)-1)
            pulse_window.destroy()
        ok_button = tk.Button(pulse_window, text="OK", command=OK)
        ok_button.grid(column=0, row=6, columnspan=2)
        pulse_window.mainloop()

    def file_clr(self):
        self.profiles.pop(self.selected_profile.get())
        self.update('file_clr')
        
    def menu_file_clear_all(self):
        self.profiles = []
        self.update('menu_file_clear_all')

    def menu_resample_x(self):
        step_window = tk.Tk()
        step_window.title("Step Size")
        step_window.grid()
        step = tk.StringVar(step_window, value=0.1)
        label = tk.Label(step_window, width=10, text="Step size")
        entry = tk.Entry(step_window, width=10, textvariable=step)
        label.grid(column=0, row=0, sticky=tk.E)
        entry.grid(column=1, row=0)
        def OK():
            p = self.selected_profile.get()
            new_profile = self.profiles[p].resample_x(float(step.get()))
            self.profiles = self.profiles[:p] + [new_profile] + self.profiles[(p+1):]
            self.update('menu_resample_x')
            step_window.destroy()
        ok_button = tk.Button(step_window, text="OK", command=OK)
        ok_button.grid(column=0, row=10, columnspan=2)
        step_window.mainloop()

    def on_key_press(self, event):
        print("you pressed {}".format(event.key))
        key_press_handler(event, self.canvas, self.toolbar)

    def _quit(self):
        root.quit()
        root.destroy()

    def about(self):
        tk.messagebox.showinfo(
            "About", "Profile Tool \n king.r.paul@gmail.com")

if __name__ == "__main__":
    root = tk.Tk()
    Application(root).pack(side="top", fill="both", expand=True)
    root.mainloop()