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

if "dosepro\dosepro" in __file__:
    add_path = os.path.abspath(os.path.join(__file__, '..','..','..','..'))
    add_path = os.path.join(add_path, 'src', 'dosepro', '_labs', 'paulking')
    sys.path.insert(0,add_path)
    from profile import Profile
else:
    from pymedphys._labs.paulking.profile import Profile


class StatusBar(tk.Frame):   
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.status = tk.StringVar()        
        self.label=tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W,
                           textvariable=self.status,
                           font=('arial',10,'normal'))
        self.label.pack(fill=tk.X)        
        self.pack()
        self.status.set('StatusBar Ready')
    def set(self, msg, *args):
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.file_import_profiler, expand=1)
        self.update_idletasks()
    def clear(self):
        self.status.set("")
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.file_import_profiler, expand=1)

class Directory(str):
    def __init__():
        pass

def get_pulse_parameters():
    pass

class OK_Button():
    pass

class ButtonBar():
    pass


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

class Application(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        root.wm_title("Profile Tool")

        fig = Figure(figsize=(5, 4), dpi=100)
        self.subplot = fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(fig, master=root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.toolbar = NavigationToolbar2Tk(self.canvas, root)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas.mpl_connect("key_press_event", self.on_key_press)

        self.buttons = []
        self.button_bar = tk.Frame(self)
        self.button_bar.pack(side=tk.BOTTOM, fill="both", expand=True)
        self.button = None

        self.status = StatusBar(self).pack(fill=tk.X)
        self.color = Color()

        menu = tk.Menu(root)
        root.config(menu=menu)
        menu = self.populate(menu)

    def menu_stub(self):
        pass

    def menu_file_import_film(self):
        filename = askopenfilename(
            initialdir="/", title="Film File",
            filetypes=(("Film Files", "*.png"), ("all files", "*.*")))
        profiler = Profile().from_narrow_png(filename)
        self.subplot.plot(profiler.x, profiler.y)
        self.canvas.draw()


    def menu_file_import_profiler(self):
        filename = askopenfilename(
            initialdir="/", title="SNC Profiler",
            filetypes=(("Profiler Files", "*.prs"), ("all files", "*.*")))

        profiler = Profile().from_snc_profiler(filename, 'rad')
        self.subplot.plot(profiler.x, profiler.y)
        self.canvas.draw()

        self.color.next()
        self.next_color = self.color.get()
        self.add_buttom()

        profiler = Profile().from_snc_profiler(filename, 'tvs')
        self.subplot.plot(profiler.x, profiler.y, color=self.next_color)
        self.canvas.draw()
        self.color.next()
        self.next_color = self.color.get()
        self.add_buttom()
        self.canvas.draw()

    def menu_import_pulse(self):

        pulse_window = tk.Tk()
        pulse_window.title("Parameters")
        pulse_window.grid()
        heading = tk.Label(pulse_window, text='Pulse Parameters')
        heading.grid(row=0, column=0, columnspan=2)
        # centre
        label = tk.Label(pulse_window, text="   Centre:", anchor=tk.E)
        label.grid(column=0, row=1)
        centre = tk.DoubleVar(pulse_window, value=0.0)
        centre_entry = tk.Entry(pulse_window, width=10, textvariable=centre)
        centre_entry.grid(column=1, row=1)
        # width
        label = tk.Label(pulse_window, text="    Width:")
        label.grid(column=0, row=2)
        width = tk.DoubleVar(pulse_window, value=10.0)
        width_entry = tk.Entry(pulse_window, width=10, textvariable=width)
        width_entry.grid(column=1, row=2)
        # domain, start
        label = tk.Label(pulse_window, text="    Start:")
        label.grid(column=0, row=3)
        start = tk.DoubleVar(pulse_window, value=-10.0)
        start_entry = tk.Entry(pulse_window, width=10, textvariable=start)
        start_entry.grid(column=1, row=3)
        # domain, end
        label = tk.Label(pulse_window, text="      End:")
        label.grid(column=0, row=4)
        end = tk.DoubleVar(pulse_window, value=10.0)
        end_entry = tk.Entry(pulse_window, width=10, textvariable=end)
        end_entry.grid(column=1, row=4)
        # increment
        label = tk.Label(pulse_window, text="Increment:")
        label.grid(column=0, row=5)
        increment = tk.DoubleVar(pulse_window, value=0.1)
        increment_entry = tk.Entry(
            pulse_window, width=10, textvariable=increment)
        increment_entry.grid(column=1, row=5)
        # OK Button

        def OK():
            self.color.next()
            self.next_color = self.color.get()
            # self.next_color = next(self.from_palette)
            profile = Profile().from_pulse(centre.get(), width.get(),
                                           (start.get(), end.get()), increment.get())
            self.subplot.plot(profile.x, profile.y, color=self.next_color)
            self.canvas.draw()
            pulse_window.destroy()
            self.add_buttom()
            self.status.set('Pulse created.')
        ok_button = tk.Button(pulse_window, text="OK", command=OK)
        ok_button.grid(column=0, row=6, columnspan=2)

        pulse_window.mainloop()


    def add_buttom(self):
        self.button = tk.Button(master=self.button_bar,
                                bg=self.next_color,
                                text="  ",
                                command=self._quit)
        self.button.pack(side=tk.LEFT, fill='both')


    def populate(self, menu):
        """ """

        filemenu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        submenu = tk.Menu(filemenu)
        submenu.add_command(label="PRS", command=self.menu_file_import_profiler)
        submenu.add_command(label="PNG", command=self.menu_file_import_film)
        submenu.add_command(label="Pulse", command=self.menu_import_pulse)
        filemenu.add_cascade(label='Import from ...', menu=submenu, underline=0)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)

        editmenu = tk.Menu(menu)
        menu.add_cascade(label="Edit", menu=editmenu)
        editmenu.add_command(label="Norm Dose", command=self.menu_stub)
        editmenu.add_command(label="Norm X", command=self.menu_stub)
        editmenu.add_command(label="Resample", command=self.menu_stub)
        editmenu.add_command(label="Resample Y", command=self.menu_stub)
        editmenu.add_command(label="Flip", command=self.menu_stub)
        editmenu.add_command(label="Normalise", command=self.menu_stub)
        editmenu.add_command(label="2X/W", command=self.menu_stub)
        editmenu.add_command(label="Symmetrise", command=self.menu_stub)

        getmenu = tk.Menu(menu)
        menu.add_cascade(label="Get", menu=getmenu)
        getmenu.add_command(label="Edges", command=self.menu_stub)
        getmenu.add_command(label="Flatness", command=self.menu_stub)
        getmenu.add_command(label="Symmetry", command=self.menu_stub)
        getmenu.add_command(label="X", command=self.menu_stub)
        getmenu.add_command(label="Y", command=self.menu_stub)
        getmenu.add_command(label="Segment", command=self.menu_stub)
        getmenu.add_command(label="Shoulders", command=self.menu_stub)
        getmenu.add_command(label="Tails", command=self.menu_stub)
        getmenu.add_command(label="Umbra", command=self.menu_stub)

        helpmenu = tk.Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command=self.about)
        return menu

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