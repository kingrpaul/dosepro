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
import csv
import re
import time
import pwlf

import profile_from

# pylint: disable = C0103, C0121, W0102

def cross_calibrate(reference, measured):
    """ density mapping, reference -> measured

    Calculated by overlaying intensity curves and observing values at
    corresponding points. Note that the result is an unsmoothed, collection
    of points.

    Parameters
    ----------
    reference : string
    measured : string
        file names with path

    Returns
    -------
    Profile

    Notes
    -----
    Requires pwlf.  https://pypi.org/project/pwlf/

    """

    reference = profile_from.snc_profiler(reference, 'rad')
    measured = profile_from.narrow_png(measured)
    measured = measured.align_to(reference)

    dist_vals = np.arange(
        max(min(measured.x), min(reference.x)),
        min(max(measured.x), max(reference.x)),
        max(reference.get_increment(), measured.get_increment()))

    x = np.array([float(measured.get_y(i)) for i in dist_vals])
    y = np.array([float(reference.get_y(i)) for i in dist_vals])

    seq = np.argsort(x) 
    x,y = x[seq], y[seq]

    def is_monotonic(func, x, y):
        return np.all(np.diff(func(x))>=0)

    def linear(x,y):
        m, b = np.polyfit(x, y, 1)
        assert m > 0
        def func(x):
            return np.multiply(m,x) + b
        return func
    
    def piece_linear(x,y,num_pieces):
        my_pwlf = pwlf.PiecewiseLinFit(x, y)
        my_pwlf.fit(num_pieces)
        if is_monotonic(my_pwlf.predict, x, y):
            return  my_pwlf.predict
        else:
            return None

    start_time = time.clock()
    last_func = linear(x,y)
    for num_pieces in range(2,10):
        if (time.clock() - start_time) > 60:
            break
        next_func = piece_linear(x,y,num_pieces)
        if not next_func:
            break
        if next_func:
            last_func = next_func

    # plt.plot(x,y, 'ro')
    # plt.plot(x,last_func(x))
    # plt.show()

    return last_func