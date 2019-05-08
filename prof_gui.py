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

""" For importing, analyzing, and comparing dose or intensity profiles
    from different sources."""

import os
import copy
import sys

from typing import Callable
from scipy import interpolate

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import tkinter as tk
from tkinter.filedialog import askopenfilename
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

from functools import partial
import PIL

from prof_funct import Profile

# pylint: disable = C0103, C0121, W0102

class GUI(tk.Frame):
    """ Graphical User Interface for Profile Class

    """

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        parent.wm_title("Profile Tool")
        parent.resizable(False, False)

        selector_frame = tk.Frame(self, width=5, height=100, background="bisque")
        graph_frame = tk.Frame(self, width=90, height=100, background="bisque")

        selector_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

        fig = Figure(figsize=(6, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.subplot = fig.add_subplot(111)
        self.toolbar = NavigationToolbar2Tk(self.canvas, graph_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas.mpl_connect("key_press_event", self.on_key_press)

        self.status = tk.StringVar()
        self.status_bar = tk.Frame(master=graph_frame, relief=tk.RIDGE, background="bisque")
        self.status_label=tk.Label(self.status_bar, bd=1, relief=tk.FLAT, anchor=tk.W,
                                   textvariable=self.status, background="bisque",
                                   font=('arial',10,'normal'))
        self.status_label.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.status_bar.pack(fill=tk.X, expand=False, side=tk.LEFT)

        self._color_palette = {'idx': 0, 'val': dict(enumerate(
            ['red', 'green', 'orange', 'blue', 'yellow', 'purple1', 'grey']*5))}

        menu = tk.Menu(parent)
        parent.config(menu=menu)
        ## ----------
        _file = tk.Menu(menu)
        __from = tk.Menu(_file)
        _edit = tk.Menu(menu)
        __resample = tk.Menu(_edit)
        __normalise = tk.Menu(_edit)
        _get = tk.Menu(menu)
        __value = tk.Menu(_get)
        __segment = tk.Menu(_get)
        _help = tk.Menu(menu)
        ## ----------
        menu.add_cascade(label="File", menu=_file)
        _file.add_cascade(label='From ...', menu=__from)
        __from.add_command(label="Film", command=self.from_narrow_png)
        __from.add_command(label="Pulse", command=self.from_pulse)
        __from.add_command(label="Profiler", command=self.from_snc_profiler)
        __from.add_command(label="RayStation Line", command=self.from_raystation_line)
        __from.add_command(label="RFA ASCII", command=self.from_rfa_ascii)
        __from.add_command(label="Pinnacle ASCII", command=self.from_pinnacle_ascii)
        __from.add_command(label="X-Calib", command=self.from_cross_calibration)
        _file.add_command(label="Clear Selected", command=self.file_clr)
        _file.add_command(label="Clear All", command=self.file_clr_all)
        _file.add_command(label="Exit", command=self._quit)
        menu.add_cascade(label="Edit", menu=_edit)
        _edit.add_cascade(label='Resample ...', menu=__resample)
        __resample.add_command(label="X", command=self.resample_x)
        __resample.add_command(label="Y", command=self.resample_y)
        _edit.add_cascade(label='Normalise ...', menu=__normalise)
        __normalise.add_command(label="X", command=self.make_normal_x)
        __normalise.add_command(label="Y", command=self.make_normal_y)
        _edit.add_command(label="Flip", command=self.make_flipped)
        _edit.add_command(label="Symmetrise", command=self.make_symmetric)
        _edit.add_command(label="Centre", command=self.make_centered)
        menu.add_cascade(label="Get", menu=_get)
        _get.add_cascade(label='Value ...', menu=__value)
        __value.add_command(label="X", command=self.get_x)
        __value.add_command(label="Y", command=self.get_y)
        _get.add_command(label="Increment", command=self.get_increment)
        _get.add_command(label="Edges", command=self.get_edges)
        _get.add_command(label="Flatness", command=self.get_flatness)
        _get.add_command(label="Symmetry", command=self.get_symmetry)
        _get.add_cascade(label='Segment ...', menu=__segment)
        __segment.add_command(label="Defined", command=self.slice_segment)
        __segment.add_command(label="Umbra", command=self.slice_umbra)
        __segment.add_command(label="Penumbra", command=self.slice_penumbra)
        __segment.add_command(label="Shoulders", command=self.slice_shoulders)
        __segment.add_command(label="Tails", command=self.slice_tails)
        menu.add_cascade(label="Help", menu=_help)
        _help.add_command(label="About...", command=self.about)
        self.profiles = []

        self.data_folder = os.path.join(os.path.split(__file__)[0],'data')

        self.selector = tk.Frame(selector_frame)
        self.selector.pack(side=tk.TOP, fill="both", expand=True)
        self.selected_profile = tk.IntVar(value=0)
        self.update('__init__')
        self.canvas.draw()

    def _color(self, cmd):
        assert cmd in ('get', 'next', 'reset')
        if cmd == 'next':
            self._color_palette['idx'] += 1
        elif cmd == 'reset':
            self._color_palette['idx'] = 0
        return self._color_palette['val'][self._color_palette['idx']]

    def select_active(self, i):
        for J in range(len(self.buttons)):
            self.buttons[J].config(relief=tk.RAISED)
        self.selected_profile.set(i)
        self.buttons[i].config(relief=tk.SUNKEN)

    def update(self, msg):
        self._color('reset')
        self.subplot.cla()
        self.buttons = []
        for button in self.selector.winfo_children():
            button.destroy()
        selector_title = tk.Label(master=self.selector, width=10,
                                  bg='white', text='Selector')
        selector_title.pack(side="top", fill="both", expand=True)
        for i,profile in enumerate(self.profiles):
            self.subplot.plot(profile.x, profile.y, color=self._color('get'))
            button = tk.Button(master=self.selector,
                        bg=self._color('get'), text=str(i), width=8,
                        command=partial(self.select_active, i))
            button.pack(side=tk.TOP, fill='both')
            self.buttons.append(button)
            self._color('next')
        try:
            self.select_active(self.selected_profile.get())
        except IndexError:
            pass
        self.status.set(msg)
        self.canvas.draw()

    def from_narrow_png(self):
        filename = askopenfilename(
            initialdir=self.data_folder, title="Film File",
            filetypes=(("Film Files", "*.png"), ("all files", "*.*")))
        self.profiles.append(Profile().from_narrow_png(filename))
        self.update('from_narrow_png')
        self.select_active(len(self.profiles)-1)

    def from_pulse(self):
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
            self.update('from_pulse')
            self.select_active(len(self.profiles)-1)
            pulse_window.destroy()
        ok_button = tk.Button(pulse_window, text="OK", command=OK)
        ok_button.grid(column=0, row=6, columnspan=2)
        pulse_window.mainloop()

    def from_snc_profiler(self):
        filename = askopenfilename(
            initialdir=self.data_folder, title="SNC Profiler",
            filetypes=(("Profiler Files", "*.prs"), ("all files", "*.*")))
        self.profiles.append(Profile().from_snc_profiler(filename, 'rad'))
        self.profiles.append(Profile().from_snc_profiler(filename, 'tvs'))
        self.update('from_snc_profiler')
        self.select_active(len(self.profiles)-1)

    def from_raystation_line(self):
        filename = askopenfilename(
            initialdir=self.data_folder, title="Film File",
            filetypes=(("CSV Files", "*.csv"), ("all files", "*.*")))
        self.profiles.append(Profile().from_raystation_line(filename))
        self.update('from_raystation_line')
        self.select_active(len(self.profiles)-1)

    def from_rfa_ascii(self):
        filename = askopenfilename(
            initialdir=self.data_folder, title="RFA File",
            filetypes=(("ASC Files", "*.asc"), ("all files", "*.*")))
        for profile in Profile().from_rfa_ascii(filename):
            self.profiles.append(profile)
            self.update('from_rfa_ascii')
        self.select_active(len(self.profiles)-1)

    def from_pinnacle_ascii(self):
        filename = askopenfilename(
            initialdir=self.data_folder, title="DAT File",
            filetypes=(("Pinnacle Files", "*.dat"), ("all files", "*.*")))
        for profile in Profile().from_pinnacle_ascii(filename):
            self.profiles.append(profile)
            self.update('from_pinnacle_ascii')
        self.select_active(len(self.profiles)-1)

    def from_cross_calibration(self):
        profiler_filename = askopenfilename(
            initialdir=self.data_folder, title="SNC Profiler",
            filetypes=(("Profiler Files", "*.prs"), ("all files", "*.*")))
        film_filename = askopenfilename(
            initialdir=self.data_folder, title="Film File",
            filetypes=(("Film Files", "*.png"), ("all files", "*.*")))

        self.profiles.append(Profile().cross_calibrate(profiler_filename,film_filename))
        self.update('from_cross_calibration')
        self.select_active(len(self.profiles)-1)

    def file_clr(self):
        self.profiles.pop(self.selected_profile.get())
        self.update('file_clr')
        self.select_active(len(self.profiles)-1)

    def file_clr_all(self):
        self.profiles = []
        self.update('file_clr_all')

    def get_edges(self):
        try:
            p = self.selected_profile.get()
            e = self.profiles[p].get_edges()
            result = "Edges: ( {0:.1f}, {1:.1f})".format(e[0], e[1])
            self.update(result)
        except IndexError:
            pass

    def get_flatness(self):
        try:
            p = self.selected_profile.get()
            e = 100 * self.profiles[p].get_flatness()
            result = "Flatness: ( {0:.2f}%)".format(e)
            self.update(result)
        except IndexError:
            pass

    def get_increment(self):
        try:
            p = self.selected_profile.get()
            e = self.profiles[p].get_increment()
            result = "Spacing: {0:.1f} cm".format(e)
            self.update(result)
        except IndexError:
            pass

    def get_symmetry(self):
        try:
            p = self.selected_profile.get()
            e = 100 * self.profiles[p].get_symmetry()
            result = "Symmetry: ( {0:.2f}%)".format(e)
            self.update(result)
        except IndexError:
            pass

    def get_x(self):
        win = tk.Tk()
        win.title("Get Y")
        win.grid()
        y = tk.StringVar(win, value=100.0)
        label = tk.Label(win, width=10, text='y')
        entry = tk.Entry(win, width=10, textvariable=y)
        label.grid(column=0, row=0, sticky=tk.E)
        entry.grid(column=1, row=0)
        def OK():
            try:
                v = float(y.get())
                p = self.selected_profile.get()
                result = self.profiles[p].get_x(v)
                result_string = '('
                if result:
                    for r in result:
                        result_string += '{:.2f}'.format(r) + ', '
                    result_string = result_string[:-2] + ')'
                    self.update('x='+ str(v) +'  ->  '+'y='+result_string)
                else:
                    self.update('')
            except IndexError:
                pass
            win.destroy()
        ok_button = tk.Button(win, text="OK", command=OK)
        ok_button.grid(column=0, row=10, columnspan=2)
        win.mainloop()


    def get_y(self):
        win = tk.Tk()
        win.title("Get X")
        win.grid()
        x = tk.StringVar(win, value=0.0)
        label = tk.Label(win, width=10, text='x')
        entry = tk.Entry(win, width=10, textvariable=x)
        label.grid(column=0, row=0, sticky=tk.E)
        entry.grid(column=1, row=0)
        def OK():
            try:
                v = float(x.get())
                p = self.selected_profile.get()
                result = self.profiles[p].get_y(v)
                if result:
                    self.update('x='+ str(v) +'  ->  '+'y='+'{:.2f}'.format(result))
            except IndexError:
                pass
            win.destroy()
        ok_button = tk.Button(win, text="OK", command=OK)
        ok_button.grid(column=0, row=10, columnspan=2)
        win.mainloop()

    def make_centered(self):
        try:
            p = self.selected_profile.get()
            new_profile = self.profiles[p].make_centered()
            self.profiles = self.profiles[:p] + [new_profile] + self.profiles[(p+1):]
            self.update('make_centered')
        except IndexError:
            pass

    def make_flipped(self):
        try:
            p = self.selected_profile.get()
            new_profile = self.profiles[p].make_flipped()
            self.profiles = self.profiles[:p] + [new_profile] + self.profiles[(p+1):]
            self.update('make_flipped')
        except IndexError:
            pass

    def make_normal_x(self):
        try:
            p = self.selected_profile.get()
            new_profile = self.profiles[p].make_normal_x()
            self.profiles = self.profiles[:p] + [new_profile] + self.profiles[(p+1):]
            self.update('normalise_x')
        except IndexError:
            pass

    def make_normal_y(self):
        norm_window = tk.Tk()
        norm_window.title("Normalization")
        norm_window.grid()
        x = tk.StringVar(norm_window, value=0.0)
        y = tk.StringVar(norm_window, value=1.0)
        x_label = tk.Label(norm_window, width=10, text="Norm distance")
        y_label = tk.Label(norm_window, width=10, text="Norm value")
        x_entry = tk.Entry(norm_window, width=10, textvariable=x)
        y_entry = tk.Entry(norm_window, width=10, textvariable=y)
        x_label.grid(column=0, row=0, sticky=tk.E)
        y_label.grid(column=0, row=1, sticky=tk.E)
        x_entry.grid(column=1, row=0)
        y_entry.grid(column=1, row=1)
        def OK():
            try:
                p = self.selected_profile.get()
                new_profile = self.profiles[p].make_normal_y(x=float(x.get()),y=float(y.get()))
                self.profiles = self.profiles[:p] + [new_profile] + self.profiles[(p+1):]
                self.update('make_normal_y')
            except IndexError:
                pass
            norm_window.destroy()
        ok_button = tk.Button(norm_window, text="OK", command=OK)
        ok_button.grid(column=0, row=10, columnspan=2)
        norm_window.mainloop()

    def make_symmetric(self):
        try:
            p = self.selected_profile.get()
            new_profile = self.profiles[p].make_symmetric()
            self.profiles = self.profiles[:p] + [new_profile] + self.profiles[(p+1):]
            self.update('make_symmetric')
        except IndexError:
            pass

    def resample_x(self):
        step_window = tk.Tk()
        step_window.title("Step Size")
        step_window.grid()
        step = tk.StringVar(step_window, value=0.1)
        label = tk.Label(step_window, width=10, text="Step size")
        entry = tk.Entry(step_window, width=10, textvariable=step)
        label.grid(column=0, row=0, sticky=tk.E)
        entry.grid(column=1, row=0)
        def OK():
            try:
                p = self.selected_profile.get()
                new_profile = self.profiles[p].resample_x(float(step.get()))
                self.profiles = self.profiles[:p] + [new_profile] + self.profiles[(p+1):]
                self.update('resample_x')
            except IndexError:
                pass
            step_window.destroy()
        ok_button = tk.Button(step_window, text="OK", command=OK)
        ok_button.grid(column=0, row=10, columnspan=2)
        step_window.mainloop()

    def resample_y(self):
        step_window = tk.Tk()
        step_window.title("Step Size")
        step_window.grid()
        step = tk.StringVar(step_window, value=0.1)
        label = tk.Label(step_window, width=10, text="Step size")
        entry = tk.Entry(step_window, width=10, textvariable=step)
        label.grid(column=0, row=0, sticky=tk.E)
        entry.grid(column=1, row=0)
        def OK():
            try:
                p = self.selected_profile.get()
                new_profile = self.profiles[p].resample_y(float(step.get()))
                self.profiles = self.profiles[:p] + [new_profile] + self.profiles[(p+1):]
                self.update('resample_y')
            except IndexError:
                pass
            step_window.destroy()
        ok_button = tk.Button(step_window, text="OK", command=OK)
        ok_button.grid(column=0, row=10, columnspan=2)
        step_window.mainloop()

    def slice_penumbra(self):
        p = self.selected_profile.get()
        (new_profile1,new_profile2) = self.profiles[p].slice_penumbra()
        self.profiles = self.profiles[:p] + [new_profile1, new_profile2] + self.profiles[(p+2):]
        self.update('slice_penumbra')

    def slice_segment(self):
        seg_window = tk.Tk()
        seg_window.title("Slice Segment")
        seg_window.grid()
        start = tk.StringVar(seg_window, value=-5.0)
        stop = tk.StringVar(seg_window, value=5.0)
        start_label = tk.Label(seg_window, width=10, text="Start")
        stop_label = tk.Label(seg_window, width=10, text="Stop")
        start_entry = tk.Entry(seg_window, width=10, textvariable=start)
        stop_entry = tk.Entry(seg_window, width=10, textvariable=stop)
        start_label.grid(column=0, row=0, sticky=tk.E)
        stop_label.grid(column=0, row=1, sticky=tk.E)
        start_entry.grid(column=1, row=0)
        stop_entry.grid(column=1, row=1)
        def OK():
            try:
                p = self.selected_profile.get()
                new_profile = self.profiles[p].slice_segment(start=float(start.get()),stop=float(stop.get()))
                self.profiles = self.profiles[:p] + [new_profile] + self.profiles[(p+1):]
                self.update('slice_segment')
            except IndexError:
                pass
            seg_window.destroy()
        ok_button = tk.Button(seg_window, text="OK", command=OK)
        ok_button.grid(column=0, row=10, columnspan=2)
        seg_window.mainloop()

    def slice_shoulders(self):
        p = self.selected_profile.get()
        (new_profile1,new_profile2) = self.profiles[p].slice_shoulders()
        self.profiles = self.profiles[:p] + [new_profile1, new_profile2] + self.profiles[(p+2):]
        self.update('slice_shoulders')

    def slice_tails(self):
        p = self.selected_profile.get()
        (new_profile1,new_profile2) = self.profiles[p].slice_tails()
        self.profiles = self.profiles[:p] + [new_profile1, new_profile2] + self.profiles[(p+2):]
        self.update('slice_tails')

    def slice_umbra(self):
        p = self.selected_profile.get()
        new_profile = self.profiles[p].slice_umbra()
        self.profiles = self.profiles[:p] + [new_profile] + self.profiles[(p+1):]
        self.update('slice_umbra')

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
    GUI(root).pack(side="top", fill="both", expand=True)
    root.mainloop()