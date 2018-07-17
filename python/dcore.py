#!/usr/bin/env python
#
# DCore -- Integrated DMFT software for correlated electrons
# Copyright (C) 2017 The University of Tokyo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from __future__ import print_function
import sys
import argparse
from triqs_dft_tools.sumk_dft import *
from dmft_core import DMFTCoreSolver

from program_options import *


def dcore(filename):
    """
    Main routine of DCore

    Parameters
    ----------
    filename : string
        Input-file name
    """
    # Set Default value
    pars = create_parser()
    #
    # Parse keywords and store
    #
    pars.read(filename)
    params = pars.as_dict()

    solver = DMFTCoreSolver(params["model"]["seedname"], params)

    solver.solve(max_step=params["control"]["max_step"], output_file=params["model"]["seedname"]+'.out.h5',
                 output_group='dmft_out')

    mpi.report("\n########################  Done  ########################\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='dcore.py',
        description='.',
        epilog='end',
        usage='$ dcore input.ini',
        add_help=True)

    parser.add_argument('path_input_file',
                        action='store',
                        default=None,
                        type=str,
                        help="input file name.")

    args = parser.parse_args()
    if os.path.isfile(args.path_input_file) is False:
        print("Input file is not exist.")
        sys.exit(-1)

    dcore(args.path_input_file)
