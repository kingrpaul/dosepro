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

import copy
import csv
import os
import re
import sys
import time
import tkinter as tk
from functools import partial
from tkinter.filedialog import askopenfilename
from typing import Callable

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import PIL
import pwlf
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from scipy import interpolate

from profile_class import Profile
import profile_from

# pylint: disable = C0103, C0121, W0102


def snc_profiler(tvs_profile=None, rad_profile=None, file_name=None, meta={}):

    """ export profiles to SNC Profiler file

    Parameters
    ----------
    tvs_profile : Profile, optional
        transverse
    rad_profile : Profile, optional
        radial
    file_name : string, optional
        long file name, *.prs
    meta : dict, optional
        metadata

    Returns
    ----------
    prs_file : str
        file contents

    """
    filename = file_name or meta.get('Filename') or 'NONE'
    jaws = re.search(r'.+(\d+).+(\d+).+(\d+).+(\d+)', meta.get('Collimator')).groups()
    version = meta.get('Version') or '7'
    meas_date = meta.get('Date') or '01/01/1970'
    meas_time = meta.get('Time') or '00:00:01'
    descrip = meta.get('Description') or ''
    instit = meta.get('Institution') or ''
    file_cal = meta.get('Calibration File') or "NONE"
    collector = meta.get('Collector Model') or 'Profiler2'
    coll_sn = meta.get('Collector Serial') or '0000000'
    coll_rev = meta.get('Revision') or 'C'
    f_ware_ver = meta.get('Firmware Version') or '0.0.0'
    s_ware_v = meta.get('Software Version') or '0.0.0.0'
    depth = re.search(r'((\d|.)+)cmWat', meta.get('Buildup')).group(1) or '0'
    nom_gain = meta.get('Nominal Gain') or '1'
    orient = meta.get('Orientation') or 'Sagittal'
    ssd = meta.get('SSD') or '100cm'
    bm_mode = meta.get('Beam Mode') or 'Pulsed'
    tray = meta.get('Tray Mount') or 'No'
    align = meta.get('Alignment') or 'None'
    interval = meta.get('Collection Interval') or '50'
    room = meta.get('Room') or ''
    mach_type = meta.get('Machine Type') or ''
    bm_modal = meta.get('Beam Type') or 'Photon'
    bm_energy = meta.get('Energy') or '0'
    dose = meta.get('Dose') or '0'
    rate = re.search(r'((\d|.)+)mu/Min', meta.get('Rate')).group(1) or '0'
    collimator = meta.get('Collimator Angle') or '0 deg'
    gantry = meta.get('Gantry Angle') or '180'
    wdg_type, wdg_ang = re.search(r'(.+)at(\d+)', meta.get('Wedge')).groups()
    mach_mod = meta.get('Machine Model') or ''
    mach_num = meta.get('Machine Number') or ''
    bkg_used = meta.get('Background Used') or 'true'
    pulse_mode = meta.get('Pulse Mode') or 'true'
    alz_panels = meta.get('Analyze Panels') or '1015679'
    spacing = meta.get('Detector Spacing') or '0.4'
    cal_sn = meta.get('Cal-Serial Number') or '0000000'
    cal_rev = meta.get('Cal-Revision') or 'A'
    temp = meta.get('Temperature') or '-100'
    dose_cal = meta.get('Dose Per Count') or '0.001'
    abs_cal = meta.get('Absolute Calibration') or 'false'
    cal_date, cal_time = meta.get('TimeStamp').split() or ('01/01/1970','00:00:01')
    updates = meta.get('# updates') or '0'
    pulses = meta.get('Total Pulses') or '0'
    concat = meta.get('Concatenation') or 'false'
    m_frame = meta.get('Multi Frame') or 'false'
    detectors=('83', '57', '0', '4')
    d_at_cal='100.0'
    energy_cal='0'
    cal_cmnts=''
    time='0.0'


    # sys.exit()



    # # EXTEND PROFILE TAILS, TO ENSURE LONGER THAN DEVICE
    # x_prof = [(-1000, 0)] + x_prof + [(1000, 0)]
    # y_prof = [(-1000, 0)] + y_prof + [(1000, 0)]

    # # X,Y DETECTOR POSITIONS FOR DEVICE
    # x_vals = [-11.2 + 0.4*i for i in range(57)]
    # y_vals = [-16.4 + 0.4*i for i in range(83)]

    # X,Y DETECTOR POSITIONS FOR DEVICE
    tvs_dist = np.arange(-11.2, 11.6, 0.4)
    rad_dist = np.arange(-16.4, 16.8, 0.4)

    tvs_val = tvs_profile.interp(tvs_dist)
    rad_val = rad_profile.interp(rad_dist)


    # # X,Y COORDINATES CORRECT, DO NOT INTERPOLATE
    # if [i[0] for i in x_prof] == x_vals and [i[0] for i in y_prof] == y_vals:
    #     counts = ['Data:', '0', '0', '0', '0'] + \
    #         [str(int(1000*i[1])) for i in x_prof + y_prof] + \
    #         ['0', '0', '0', '0\n']

    # X,Y COORDINATES CORRECT, DO NOT INTERPOLATE
    counts = ['Data:', '0', '0', '0', '0'] + \
        [str(int(1000*i)) for i in list(tvs_val) + list(rad_val)] + \
        ['0', '0', '0', '0\n']


    # else:  # INTERPOLATE X,Y COORDINATES ONTO DETECTOR POSITIONS
    #     interpolator = interp1d([i[0] for i in x_prof], [i[1] for i in x_prof])
    #     # counts_x = []
    #     counts_x = [float(i) for i in list(map(interpolator, x_vals))]

    #     interpolator = interp1d([i[0] for i in y_prof], [i[1] for i in y_prof])
    #     # counts_y = []
    #     counts_y = [float(i) for i in list(map(interpolator, y_vals))]

    #     # 1000 COUNTS PER CGY
    #     counts = ['Data:', '0', '0', '0', '0'] + \
    #         [str(int(1000*i)) for i in counts_x + counts_y] + \
    #         ['0', '0', '0', '0\n']



    prs_file = ['Version:\t {}\n'.format(7),
                'Filename:\t {} \n'.format('-'),
                'Date:\t {}\t Time:\t{}\n'.format(meas_date, meas_time),
                'Description:\t{}\n'.format(descrip),
                'Institution:\t{}\n'.format(instit),
                'Calibration File:\t{}\n'.format(file_cal),
                '\tProfiler Setup\n', '\n',
                'Collector Model:\t{}\n'.format(collector),
                'Collector Serial:\t{} Revision:\t{}\n'.format(
                    coll_sn, coll_rev),
                'Firmware Version:\t{}\n'.format(f_ware_ver),
                'Software Version:\t{}\n'.format(s_ware_v),
                'Buildup:\t{}\tcm\tWaterEquiv\n'.format(depth),
                'Nominal Gain\t{}\n'.format(nom_gain),
                'Orientation:\t{}\n'.format(orient),
                'SSD:\t{}\tcm\n'.format(ssd),
                'Beam Mode:\t{}\n'.format(bm_mode),
                'Tray Mount:\t{}\n'.format(tray),
                'Alignment:\t{}\n'.format(align),
                'Collection Interval:\t{}\n'.format(interval),
                '\n',
                '\tMachine Data\n',
                'Room:\t{}\n'.format(room),
                'Machine Type:\t{}\n'.format(mach_type),
                'Machine Model:\t{}\n'.format(mach_mod),
                'Machine Serial Number:\t{}\n'.format(mach_num),
                'Beam Type:\t{}\tEnergy:\t{} MeV\n'.format(
                    bm_modal, bm_energy),
                'Collimator:\tLeft: {} Right: {} Top: {} Bottom: {} cm\n'.format(
                   *jaws),
                'Wedge:\t{}\tat\t{}\n'.format(wdg_type, wdg_ang),
                'Rate:\t{}\tmu/Min\tDose:\t{}\n'.format(rate, dose),
                'Gantry Angle:\t{} deg\tCollimator Angle:\t{} deg\n'.format(
                    gantry, collimator),
                '\n',
                '\tData Flags\n',
                'Background Used:\t{}\n'.format(bkg_used),
                'Pulse Mode:\t{}\n'.format(pulse_mode),
                'Analyze Panels:\t{}\n'.format(alz_panels),
                '\n',
                '\tHardware Data\n',
                'Cal-Serial Number:\t{}\n'.format(cal_sn),
                'Cal-Revision:\t{}\n'.format(cal_rev),
                'Temperature:\t{}\n'.format(temp),
                'Dose Calibration\n',
                'Dose Per Count:\t{}\n'.format(dose_cal),
                'Dose:\t{}\n'.format(d_at_cal),
                'Absolute Calibration:\t{}\n'.format(abs_cal),
                'Energy:\t{} MV\n'.format(energy_cal),
                'TimeStamp:\t{} {}\n'.format(cal_date, cal_time),
                'Comments:\t{}\n'.format(cal_cmnts),
                'Gain Ratios for Amp0:\t\t{}\t{}\t{}\t{}\n'.format(1, 2, 4, 8),
                'Gain Ratios for Amp1:\t\t{}\t{}\t{}\t{}\n'.format(1, 2, 4, 8),
                'Gain Ratios for Amp2:\t\t{}\t{}\t{}\t{}\n'.format(1, 2, 4, 8),
                'Gain Ratios for Amp3:\t\t{}\t{}\t{}\t{}\n'.format(1, 2, 4, 8),
                '\n',
                'Multi Frame:\t{}\n'.format(m_frame),
                '# updates:\t{}\n'.format(updates),
                'Total Pulses:\t{}\n'.format(pulses),
                'Total Time:\t{}\n'.format(0.0),
                'Detectors:\t{}\t{}\t{}\t{}\n'.format(*detectors),
                'Detector Spacing:\t{}\n'.format(spacing),
                'Concatenation:\t{}\n'.format(concat),
                '\t'.join(['TYPE',
                           'UPDATE#',
                           'TIMETIC',
                           'PULSES',
                           'ERRORS'] +
                          ['X'+str(i) for i in range(1, 58)] +
                          ['Y'+str(i) for i in range(1, 84)] +
                          ['Z0', 'Z1', 'Z2', 'Z3\n']),
                '\t'.join(['BIAS1', '', '0', '',
                           ''] + ['0.0']*143 + ['0.0\n']),
                '\t'.join(['Calibration', '', '', '', ''] +
                          ['1.0']*139 + ['1.0\n']),
                '\t'.join(counts)]

            
    # print(prs_file)

    with open(file_name, 'w') as outfile:
        for line in prs_file:
            outfile.write(line)
    return prs_file
