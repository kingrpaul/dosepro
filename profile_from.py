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

from profile_class import Profile

# pylint: disable = C0103, C0121, W0102

def lists(x, y, meta={}):
    """  import x and y lists

    Parameters
    ----------
    x : list
        List of float x values
    y : list
        List of float y values
    meta : dict, optional

    Returns
    -------
    Profile

    Examples
    --------
    ``profile = lists(x_list,data_list)``

    """

    # self.x = np.array(x)
    # self.y = np.array(y)
    # # self.__init__(x=x, y=y, meta=meta)
    return Profile(x=np.array(x), y=np.array(y), meta=meta)

def tuples(list_of_tuples, meta={}):
    """  import list of (x,y) tuples

    Parameters
    ----------
    list_of_tuples : [(float x, float y), ...]
    meta : dict, optional

    Returns
    -------
    Profile

    Examples
    --------
    ``profile = lists(list_of_tuples)``

    """
    x = list(list(zip(*list_of_tuples))[0])
    y = list(list(zip(*list_of_tuples))[1])
    # self.__init__(x=x, y=y, meta=meta)
    return Profile(x=x, y=y, meta=meta)

def pulse(centre, width, domain, increment, meta={}):
    """ create pulse of unit height

    Parameters
    ----------
    centre : float
    width : float
    domain : tuple
        (x_left, x_right)
    increment : float
    meta : dict, optional

    Returns
    -------
    Profile


    """
    x_vals = np.arange(domain[0], domain[1] + increment, increment)
    y = []
    for x in x_vals:
        if abs(x) > (centre + width/2.0):
            y.append(0.0)
        elif abs(x) < (centre + width/2.0):
            y.append(1.0)
        else:
            y.append(0.5)
    return lists(x_vals, y, meta=meta)

def snc_profiler(file_name, axis):
    """ import profile from SNC Profiler file

    Parameters
    ----------
    file_name : string
        file name with path, .prs
    axis : string
        'tvs' or 'rad'

    Returns
    -------
    Profile

    Raises
    ------
    TypeError
        if axis invalid

    """

    with open(file_name) as profiler_file:
        munge = '\n'.join(profiler_file.readlines())
        munge = munge.replace('\t', '').replace(': ', ':')
        munge = munge.replace(' Time:', '\nTime:')  # BREAK 2-ITEM ROWS
        munge = munge.replace(' Revision:', '\nRevision:')
        munge = munge.replace('Energy:', '\nEnergy:')
        munge = munge.replace('Dose:', '\nDose:')
        munge = munge.replace('Collimator Angle:', '\nCollimator Angle:')
        munge = munge.split('TYPE')[0].split('\n')  # DISCARD NON-METADATA
        munge = [i.split(':', 1) for i in munge if i and ':' in i]
        munge = [i for i in munge if i[1]]  # DISCARD EMPTY ITEMS
        meta = dict(munge)

    with open(file_name) as profiler_file:
        for row in profiler_file.readlines():
            if row[:11] == "Calibration" and "File" not in row:
                calibs = np.array(row.split())[1:].astype(float)
            elif row[:5] == "Data:":
                counts = np.array(row.split()[5:145]).astype(float)
            elif row[:15] == "Dose Per Count:":
                dose_per_count = (float(row.split()[-1]))
    dose = counts * dose_per_count * calibs

    x_vals = [-11.2 + 0.4*i for i in range(57)]
    x_prof = list(zip(x_vals, dose[:57]))
    y_vals = [-16.4 + 0.4*i for i in range(83)]
    y_prof = list(zip(y_vals, dose[57:]))

    if axis == 'tvs':
        return tuples(x_prof, meta=meta)
    elif axis == 'rad':
        return tuples(y_prof, meta=meta)
    else:
        raise TypeError("axis must be 'tvs' or 'rad'")

def narrow_png(file_name, step_size=0.1):
    """ import from png file

    Source file is a full color PNG, sufficiently narrow that
    density is uniform along its short dimension. The image density along
    its long dimension is reflective of a dose distribution.

    Parameters
    ----------
    file_name : str
    step-size : float, optional

    Returns
    -------
    Profile

    Raises
    ------
    ValueError
        if aspect ratio <= 5, i.e. not narrow
    AssertionError
        if step_size <= 12.7 over dpi, i.e. small

    """
    image_file = PIL.Image.open(file_name)
    # print(image_file.mode)
    # assert image_file.mode == 'RGB'
    dpi_horiz, dpi_vert = image_file.info['dpi']

    image_array = mpimg.imread(file_name)

    # DIMENSIONS TO AVG ACROSS DIFFERENT FOR HORIZ VS VERT IMG
    if image_array.shape[0] > 5*image_array.shape[1]:    # VERT
        image_vector = np.average(image_array, axis=(1, 2))
        pixel_size_in_cm = (2.54 / dpi_vert)
    elif image_array.shape[1] > 5*image_array.shape[0]:  # HORIZ
        image_vector = np.average(image_array, axis=(0, 2))
        pixel_size_in_cm = (2.54 / dpi_horiz)
    else:
        raise ValueError('The PNG file is not a narrow strip.')
    assert step_size > 5 * pixel_size_in_cm, "step size too small"

    if image_vector.shape[0] % 2 == 0:
        image_vector = image_vector[:-1]  # SO ZERO DISTANCE IS MID-PIXEL

    length_in_cm = image_vector.shape[0] * pixel_size_in_cm
    full_resolution_distances = np.arange(-length_in_cm/2,
                                            length_in_cm/2,
                                            pixel_size_in_cm)

    # TO MOVE FROM FILM RESOLUTION TO DESIRED PROFILE RESOLUTION
    num_pixels_to_avg_over = int(step_size/pixel_size_in_cm)
    sample_indices = np.arange(num_pixels_to_avg_over/2,
                                len(full_resolution_distances),
                                num_pixels_to_avg_over).astype(int)
    downsampled_distances = list(full_resolution_distances[sample_indices])

    downsampled_density = []
    for idx in sample_indices:  # AVERAGE OVER THE SAMPLING WINDOW
        avg_density = np.average(
            image_vector[int(idx - num_pixels_to_avg_over / 2):
                            int(idx + num_pixels_to_avg_over / 2)])
        downsampled_density.append(avg_density)

    zipped_profile = list(zip(downsampled_distances, downsampled_density))
    return tuples(zipped_profile)


def raystation_line(file_name):
    """ import from raystation plan csv file

    Source file is a line-dose distribution created by RayStation-6.
    
    Parameters
    ----------
    file_name : str

    Returns
    -------
    Profile

    """
    meta = dict()
    with open(file_name) as ray_file:
        contents = ''.join(ray_file)
    for key in ('RayStationVersion', 'PatientName', 'PatientId', 
                'CoordinateSystem','LineName', 'DoseName', 
                'DoseEngine', 'TreatmentMachine'):
        regex = key + r':\W+(.{1,})\n'
        meta[key] = re.search(regex, contents).group(1)

    data = contents.split('#X [cm];Y [cm];Z [cm];Dose [cGy]')[-1]
    data = data.split('##')[0].split('\n')[1:-1]
    data = csv.reader(data, delimiter=';')
    data = np.array(list(data)).astype(float)
    distance = (  (data[:,0] - data[0,0]  )**2 + 
                    (data[:,1] - data[0,1]  )**2 + 
                    (data[:,2] - data[0,2]  )**2)**0.5
    distance = distance - distance[len(distance)//2]
    dose = data[:,3]
    return Profile(x=distance, y=dose, meta=meta)

def rfa_ascii(file_name):
    """ import from rfa scan csv file

    Source file is as produced by Omnipro Accept.
    
    Parameters
    ----------
    file_name : str

    Returns
    -------
    Profile

    """

    result = []

    with open(file_name) as rfa_file:
        contents = ''.join(rfa_file)

    num_measurments = int(re.search(r':MSR\W+(\d+)', contents).group(1))

    contents = contents.split(':EOM #')[:-1]

    for idx, measurement in enumerate(contents):
        meta = dict()
        for key in ( ('%DAT', 'date'), ('%TIM', 'time'), ('%SSD', 'SSD'), 
                    ('%WEG', 'wedge'), ('%PTS', 'num_pts')):
            regex = key[0] + r'\W+(.{1,})\n'
            meta[key[1]] = re.search(regex, measurement).group(1)

        key = (r'%FSZ', 'field_size')
        regex = key[0] + r'\W+(.+)\t(.+)\n'
        meta[key[1]] = (re.search(regex, measurement).group(1), 
                        re.search(regex, measurement).group(2))

        for key in (('%STS', 'start_pt'), (r'%EDS', 'end_pt')):
            regex = key[0] + r'\W+(.+)\t(.+)\t(.+) #'
            meta[key[1]] = (re.search(regex, measurement).group(1).strip(),
                            re.search(regex, measurement).group(2).strip(),
                            re.search(regex, measurement).group(3).strip())

        data = np.array([(m.split('\t')[-1]).split() for m in measurement.split('\n') if '=' in m])
        data = data.astype(float)
        distance = (  (data[:,0] - data[0,0]  )**2 + 
                    (data[:,1] - data[0,1]  )**2 + 
                    (data[:,2] - data[0,2]  )**2)**0.5 / 10
        distance = distance - distance[len(distance)//2]

        dose = data[:,3]
        result.append(Profile(x=distance, y=dose, meta=meta))
    return result

def pinnacle_ascii(file_name):
    """ import from pinnacle full ASCII file

    Source file is as produced by Pinnacle TPS.
    
    Parameters
    ----------
    file_name : str

    Returns
    -------
    Profile

    """

    with open(file_name) as pinn_file:
        contents = ''.join(pinn_file)

    row1 = r'(\w{15})\n'
    assert 'PinnDoseProfile' in re.match(row1, contents).group(1)

    row2 = row1 + r'(\d+)\s(\d+\.?\d*)\n'
    energy, ssd = re.match(row2, contents).group(2,3)

    row3 = row2 + r'(\d+\.?\d*)\s(\d+\.?\d*)\s(\d+\.?\d*)\s(\d+\.?\d*)\n'
    jaws = re.match(row3, contents).group(4,5,6,7)
    
    row4 = row3 + r'WedgeName\s+"(.+)"\n'
    wedge = re.match(row4, contents).group(8)

    row5 = row4 + r'(\d+)\n'
    num_profiles = re.match(row5, contents).group(9)
    assert int(num_profiles) == len(re.findall('(^De|XP|YP)', contents))

    hdr = r'(De.+|XP.+|YP.+)\s(-?\d+\.\d+)\s(-?\d+\.\d+)\n(\d+)'
    p_type, dpth, offset, num_pt = tuple(zip(*re.findall(hdr, contents)))

    regex = re.compile(r'De.+|XP.+|YP.+\s-?\d+\.\d+')
    contents = re.sub(regex, '*break*', contents).split('*break*')[1:]

    result = []
    for i in range(int(num_profiles)):
        meta = {'type': p_type[i],'energy': energy, 'ssd': ssd, 'jaws': jaws, 
                'wedge': wedge, 'depth': dpth[i],'offset': offset[i], 
                'num_points': num_pt[i]}
        data = np.array([c.split() for c in contents[i].split('\n') 
                            if len(c.split())==2]).astype(float)
        x = data[:,0]
        y = data[:,1]
        result.append(Profile(x=x, y=y, meta=meta))

    return result