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
import os
import numpy
import argparse
import re
from pytriqs.archive.hdf_archive import HDFArchive
from triqs_dft_tools.converters.wannier90_converter import Wannier90Converter
from triqs_dft_tools.converters.hk_converter import HkConverter
from program_options import create_parser
import pytriqs.utility.mpi as mpi
from pytriqs.operators.util.U_matrix import U_J_to_radial_integrals, U_matrix, eg_submatrix, t2g_submatrix


def __print_paramter(p, param_name):
    print(param_name + " = " + str(p[param_name]))


def __generate_wannier90_model(params, f):
    """
    Compute hopping etc. for A(k,w) of Wannier90

    Parameters
    ----------
    params : dictionary
        Input parameters
    f : File stream
        file
    """
    #
    # Number of orbitals in each shell
    # Equivalence of each shell
    #
    ncor = params["model"]["ncor"]
    #
    norb_list = re.findall(r'\d+', params["model"]["norb"])
    norb = [int(norb_list[icor]) for icor in range(ncor)]
    #
    if params["model"]["equiv"] == "None":
        equiv = [icor for icor in range(ncor)]
    else:
        equiv_list = re.findall(r'[^\s,]+', params["model"]["equiv"])
        equiv_str_list = []
        equiv_index = 0
        equiv = [0] * ncor
        for icor in range(ncor):
            if equiv_list[icor] in equiv_str_list:
                # Defined before
                equiv[icor] = equiv_str_list.index(equiv_list[icor])
            else:
                # New one
                equiv_str_list.append(equiv_list[icor])
                equiv[icor] = equiv_index
                equiv_index += 1
    #
    nk = params["system"]["nk"]
    nk0 = params["system"]["nk0"]
    nk1 = params["system"]["nk1"]
    nk2 = params["system"]["nk2"]
    if nk0 == 0:
        nk0 = nk
    if nk1 == 0:
        nk1 = nk
    if nk2 == 0:
        nk2 = nk
    print("\n    nk0 = {0}".format(nk0))
    print("    nk1 = {0}".format(nk1))
    print("    nk2 = {0}".format(nk2))
    print("    ncor = {0}".format(ncor))
    for i in range(ncor):
        assert equiv[i] >= 0
        print("    norb[{0}], equiv[{0}] = {1}, {2}".format(i, norb[i], equiv[i]))
    print("")
    #
    # Generate file for Wannier90-Converter
    #
    print("0 {0} {1} {2}".format(nk0, nk1, nk2), file=f)
    print(params["model"]["nelec"], file=f)
    print(ncor, file=f)
    for i in range(ncor):
        print("{0} {1} {2} {3} 0 0".format(i, equiv[i], 0, norb[i]), file=f)


def para2noncol(params):
    """
    Duplicate orbitals when we perform non-colinear DMFT from the colinear DFT calculation.
    """
    ncor = params["model"]['ncor']
    norb_list = re.findall(r'\d+', params["model"]["norb"])
    norb = [int(norb_list[icor]) / 2 for icor in range(ncor)]
    #
    # Read Wannier90 file
    #
    w90 = Wannier90Converter(seedname=params["model"]["seedname"])
    nr, rvec, rdeg, nwan, hamr = w90.read_wannier90hr(params["model"]["seedname"] + "_col_hr.dat")
    #
    # Non correlated shell
    #
    ncor += 1
    norb_tot = sum(norb)
    norb.append(nwan - norb_tot)
    #
    # Output new wannier90 file
    #
    with open(params["model"]["seedname"] + "_hr.dat", 'w') as f:

        print("Converted from Para to Non-collinear", file=f)
        print(nwan*2, file=f)
        print(nr, file=f)
        for ir in range(nr):
            print("%5d" % rdeg[ir], end="", file=f)
            if ir % 15 == 14:
                print("", file=f)
        if nr % 15 != 0:
            print("", file=f)
        #
        # Hopping
        #
        for ir in range(nr):
            iorb1 = 0
            iorb2 = 0
            for icor in range(ncor):
                for ispin in range(2):
                    iorb1 -= ispin * norb[icor]
                    for iorb in range(norb[icor]):
                        iorb1 += 1
                        iorb2 += 1
                        jorb1 = 0
                        jorb2 = 0
                        for jcor in range(ncor):
                            for jspin in range(2):
                                jorb1 -= jspin * norb[jcor]
                                for jorb in range(norb[jcor]):
                                    jorb1 += 1
                                    jorb2 += 1
                                    if ispin == jspin:
                                        hamr2 = hamr[ir][jorb1-1, iorb1-1]
                                    else:
                                        hamr2 = 0.0 + 0.0j
                                    print("%5d%5d%5d%5d%5d%12.6f%12.6f" %
                                          (rvec[ir, 0], rvec[ir, 1], rvec[ir, 2], jorb2, iorb2,
                                           hamr2.real, hamr2.imag), file=f)


def __generate_lattice_model(params, f):
    """
    Compute hopping etc. for A(k,w) of preset models

    Parameters
    ----------
    params : dictionary
            Input parameters
    Returns
    -------
    weights_in_file: Bool
        Weights for the bethe lattice
    """
    weights_in_file = False
    if params["model"]["lattice"] == 'chain':
        nkbz = params["system"]["nk"]
    elif params["model"]["lattice"] == 'square':
        nkbz = params["system"]["nk"]**2
    elif params["model"]["lattice"] == 'cubic':
        nkbz = params["system"]["nk"]**3
    elif params["model"]["lattice"] == 'bethe':
        nkbz = params["system"]["nk"]
        weights_in_file = True
    else:
        print("Error ! Invalid lattice : ", params["model"]["lattice"])
        sys.exit(-1)
    print("\n    Total number of k =", str(nkbz))
    #
    # Model
    #
    norb = int(params["model"]["norb"])
    #
    # Write General-Hk formatted file
    #
    print(nkbz, file=f)
    print(params["model"]["nelec"], file=f)
    print("1", file=f)
    print("0 0 {0} {1}".format(0, norb), file=f)
    print("1", file=f)
    print("0 0 {0} {1} 0 0".format(0, norb), file=f)
    print("1 {0}".format(norb), file=f)

    t = params["model"]["t"]
    tp = params["model"]["t'"]
    nk = params["system"]["nk"]

    #
    # Energy band
    #
    if params["model"]["lattice"] == 'bethe':
        #
        # If Bethe lattice, set k-weight manually to generate semi-circular DOS
        #
        for i0 in range(nk):
            ek = float(2*i0 + 1 - nk) / float(nk)
            wk = numpy.sqrt(1.0 - ek**2)
            print("{0}".format(wk), file=f)
        for i0 in range(nk):
            ek = 2.0 * t * float(2*i0 + 1 - nk) / float(nk)
            for iorb in range(norb):
                for jorb in range(norb):
                    if iorb == jorb:
                        print("{0}".format(ek), file=f)  # Real part
                    else:
                        print("0.0", file=f)  # Real part
            for iorb in range(norb*norb):
                print("0.0", file=f)  # Imaginary part
    elif params["model"]["lattice"] == 'chain':
        kvec = [0.0, 0.0, 0.0]
        for i0 in range(nk):
            kvec[0] = 2.0 * numpy.pi * float(i0) / float(nk)
            ek = 2.0*t*numpy.cos(kvec[0]) + 2*tp*numpy.cos(2.0*kvec[0])
            for iorb in range(norb):
                for jorb in range(norb):
                    if iorb == jorb:
                        print("{0}".format(ek), file=f)  # Real part
                    else:
                        print("0.0", file=f)  # Real part
            for iorb in range(norb*norb):
                print("0.0", file=f)  # Imaginary part
    elif params["model"]["lattice"] == 'square':
        kvec = [0.0, 0.0, 0.0]
        for i0 in range(nk):
            kvec[0] = 2.0 * numpy.pi * float(i0) / float(nk)
            for i1 in range(nk):
                kvec[1] = 2.0 * numpy.pi * float(i1) / float(nk)
                ek = 2.0*t*(numpy.cos(kvec[0]) + numpy.cos(kvec[1])) \
                    + 2.0*tp*(numpy.cos(kvec[0] + kvec[1]) + numpy.cos(kvec[0] - kvec[1]))
                for iorb in range(norb):
                    for jorb in range(norb):
                        if iorb == jorb:
                            print("{0}".format(ek), file=f)  # Real part
                        else:
                            print("0.0", file=f)  # Real part
                for iorb in range(norb*norb):
                    print("0.0", file=f)  # Imaginary part
    elif params["model"]["lattice"] == 'cubic':
        kvec = [0.0, 0.0, 0.0]
        for i0 in range(nk):
            kvec[0] = 2.0 * numpy.pi * float(i0) / float(nk)
            for i1 in range(nk):
                kvec[1] = 2.0 * numpy.pi * float(i1) / float(nk)
                for i2 in range(nk):
                    kvec[2] = 2.0 * numpy.pi * float(i2) / float(nk)
                    ek = 2*t*(numpy.cos(kvec[0]) + numpy.cos(kvec[1]) + numpy.cos(kvec[2])) \
                        + 2*tp*(numpy.cos(kvec[0] + kvec[1]) + numpy.cos(kvec[0] - kvec[1])
                                + numpy.cos(kvec[1] + kvec[2]) + numpy.cos(kvec[1] - kvec[2])
                                + numpy.cos(kvec[2] + kvec[0]) + numpy.cos(kvec[2] - kvec[0]))
                    for iorb in range(norb):
                        for jorb in range(norb):
                            if iorb == jorb:
                                print("{0}".format(ek), file=f)  # Real part
                            else:
                                print("0.0", file=f)  # Real part
                    for iorb in range(norb*norb):
                        print("0.0", file=f)  # Imaginary part
    return weights_in_file


def __generate_umat(p):
    """
    Add U-matrix block (Tentative)
    :param p: dictionary
        Input parameters
    :return:
    """
    # Add U-matrix block (Tentative)
    # ####  The format of this block is not fixed  ####
    #
    ncor = p["model"]['ncor']
    kanamori = numpy.zeros((ncor, 3), numpy.float_)
    slater_f = numpy.zeros((ncor, 4), numpy.float_)
    slater_l = numpy.zeros(ncor, numpy.int_)
    #
    # Read interaction from input file
    #
    if p["model"]["interaction"] == 'kanamori':
        if p["model"]["kanamori"] == "None":
            print("Error ! Parameter \"kanamori\" is not specified.")
            sys.exit(-1)
        if p["model"]["slater_f"] != "None":
            print("Error ! Parameter \"slater_f\" is specified but is not used.")
            sys.exit(-1)
        if p["model"]["slater_uj"] != "None":
            print("Error ! Parameter \"slater_uj\" is specified but is not used.")
            sys.exit(-1)

        kanamori_list = re.findall(r'\(\s*-?\s*\d+\.?\d*,\s*-?\s*\d+\.?\d*,\s*-?\s*\d+\.?\d*\)', p["model"]["kanamori"])
        if len(kanamori_list) != ncor:
            print("\nError! The length of \"kanamori\" is wrong.")
            sys.exit(-1)

        try:
            for i, _list in enumerate(kanamori_list):
                _kanamori = filter(lambda w: len(w) > 0, re.split(r'[)(,]', _list))
                for j in range(3):
                    kanamori[i, j] = float(_kanamori[j])
        except RuntimeError:
            raise RuntimeError("Error ! Format of u_j is wrong.")
    elif p["model"]["interaction"] == 'slater_uj':
        if p["model"]["slater_uj"] == "None":
            print("Error ! Parameter \"slater_uj\" is not specified.")
            sys.exit(-1)
        if p["model"]["slater_f"] != "None":
            print("Error ! Parameter \"slater_f\" is specified but is not used.")
            sys.exit(-1)
        if p["model"]["kanamori"] != "None":
            print("Error ! Parameter \"kanamori\" is specified but is not used.")
            sys.exit(-1)

        f_list = re.findall(r'\(\s*\d+\s*,\s*-?\s*\d+\.?\d*,\s*-?\s*\d+\.?\d*\)',
                            p["model"]["slater_uj"])
        if len(f_list) != ncor:
            print("\nError! The length of \"slater_uj\" is wrong.")
            sys.exit(-1)

        try:
            for i, _list in enumerate(f_list):
                _slater = filter(lambda w: len(w) > 0, re.split(r'[)(,]', _list))
                slater_l[i] = int(_slater[0])
                slater_u = float(_slater[1])
                slater_j = float(_slater[2])
                if slater_l[i] == 0:
                    slater_f[i, 0] = slater_u
                else:
                    slater_f[i, 0:slater_l[i]+1] = U_J_to_radial_integrals(slater_l[i], slater_u, slater_j)
        except RuntimeError:
            raise RuntimeError("Error ! Format of u_j is wrong.")
    elif p["model"]["interaction"] == 'slater_f':
        if p["model"]["slater_f"] == "None":
            print("Error ! Parameter \"slater_f\" is not specified.")
            sys.exit(-1)
        if p["model"]["kanamori"] != "None":
            print("Error ! Parameter \"kanamori\" is specified but is not used.")
            sys.exit(-1)
        if p["model"]["slater_uj"] != "None":
            print("Error ! Parameter \"slater_uj\" is specified but is not used.")
            sys.exit(-1)

        f_list = re.findall(r'\(\s*\d+\s*,\s*-?\s*\d+\.?\d*,\s*-?\s*\d+\.?\d*,\s*-?\s*\d+\.?\d*,\s*-?\s*\d+\.?\d*\)',
                            p["model"]["slater_f"])
        slater_f = numpy.zeros((ncor, 4), numpy.float_)
        slater_l = numpy.zeros(ncor, numpy.int_)
        if len(f_list) != ncor:
            print("\nError! The length of \"slater_f\" is wrong.")
            sys.exit(-1)

        try:
            for i, _list in enumerate(f_list):
                _slater = filter(lambda w: len(w) > 0, re.split(r'[)(,]', _list))
                slater_l[i] = int(_slater[0])
                for j in range(4):
                    slater_f[i, j] = float(_slater[j])
        except RuntimeError:
            raise RuntimeError("Error ! Format of u_j is wrong.")
    elif p["model"]["interaction"] == 'respack':
        if p["model"]["kanamori"] != "None":
            print("Error ! Parameter \"kanamori\" is specified but is not used.")
            sys.exit(-1)
        if p["model"]["slater_uj"] != "None":
            print("Error ! Parameter \"slater_uj\" is specified but is not used.")
            sys.exit(-1)
        if p["model"]["slater_f"] != "None":
            print("Error ! Parameter \"slater_f\" is specified but is not used.")
            sys.exit(-1)
    else:
        print("Error ! Invalid interaction : ", p["model"]["interaction"])
        sys.exit(-1)
    #
    # Generate and Write U-matrix
    #
    print("\n  @ Write the information of interactions")
    f = HDFArchive(p["model"]["seedname"]+'.h5', 'a')

    corr_shells = f["dft_input"]["corr_shells"]
    norb = [corr_shells[icor]["dim"] for icor in range(ncor)]
    if p["model"]["spin_orbit"] or p["model"]["non_colinear"]:
        for icor in range(ncor):
            norb[icor] /= 2

    if not ("DCore" in f):
        f.create_group("DCore")
    #
    u_mat = [numpy.zeros((norb[icor], norb[icor], norb[icor], norb[icor]), numpy.complex_) for icor in range(ncor)]
    if p["model"]["interaction"] == 'kanamori':
        for icor in range(ncor):
            for iorb in range(norb[icor]):
                for jorb in range(norb[icor]):
                    u_mat[icor][iorb, jorb, iorb, jorb] = kanamori[icor, 1]
                    u_mat[icor][iorb, jorb, jorb, iorb] = kanamori[icor, 2]
                    u_mat[icor][iorb, iorb, jorb, jorb] = kanamori[icor, 2]
            for iorb in range(norb[icor]):
                u_mat[icor][iorb, iorb, iorb, iorb] = kanamori[icor, 0]
    elif p["model"]["interaction"] == 'slater_uj' or p["model"]["interaction"] == 'slater_f':
        for icor in range(ncor):
            if slater_l[icor] == 0:
                umat_full = numpy.zeros((1, 1, 1, 1), numpy.complex_)
                umat_full[0, 0, 0, 0] = slater_f[icor, 0]
            else:
                umat_full = U_matrix(l=slater_l[icor], radial_integrals=slater_f[icor, :], basis='cubic')
            #
            # For t2g or eg, compute submatrix
            #
            if slater_l[icor]*2+1 != norb[icor]:
                if slater_l[icor] == 2 and norb[icor] == 2:
                    u_mat = eg_submatrix(umat_full)
                elif slater_l[icor] == 2 and norb[icor] == 3:
                    u_mat = t2g_submatrix(umat_full)
                else:
                    print("Error ! Unsupported pair of l and norb : ", slater_l[icor], norb[icor])
                    sys.exit(-1)
            else:
                u_mat[icor] = umat_full
    elif p["model"]["interaction"] == 'respack':
        w90u = Wannier90Converter(seedname=p["model"]["seedname"])
        nr_u, rvec_u, rdeg_u, nwan_u, hamr_u = w90u.read_wannier90hr(p["model"]["seedname"] + "_ur.dat")
        w90j = Wannier90Converter(seedname=p["model"]["seedname"])
        nr_j, rvec_j, rdeg_j, nwan_j, hamr_j = w90j.read_wannier90hr(p["model"]["seedname"] + "_jr.dat")
        #
        # Read 2-index U-matrix
        #
        umat2 = numpy.zeros((nwan_u, nwan_u), numpy.complex_)
        for ir in range(nr_u):
            if rvec_u[ir, 0] == 0 and rvec_u[ir, 1] == 0 and rvec_u[ir, 2] == 0:
                umat2 = hamr_u[ir]
        #
        # Read 2-index J-matrix
        #
        jmat2 = numpy.zeros((nwan_j, nwan_j), numpy.complex_)
        for ir in range(nr_j):
            if rvec_j[ir, 0] == 0 and rvec_j[ir, 1] == 0 and rvec_j[ir, 2] == 0:
                jmat2 = hamr_j[ir]
        #
        # Map into 4-index U at each correlated shell
        #
        start = 0
        for icor in range(ncor):
            for iorb in range(norb[icor]):
                for jorb in range(norb[icor]):
                    u_mat[icor][iorb, jorb, iorb, jorb] = umat2[start+iorb, start+jorb]
                    u_mat[icor][iorb, jorb, jorb, iorb] = jmat2[start+iorb, start+jorb]
                    u_mat[icor][iorb, iorb, jorb, jorb] = jmat2[start+iorb, start+jorb]
            for iorb in range(norb[icor]):
                u_mat[icor][iorb, iorb, iorb, iorb] = umat2[start+iorb, start+iorb]
            start += norb[icor]
    #
    for icor in range(ncor):
        u_mat[icor][:, :, :, :].imag = 0.0
    #
    # Spin & Orb
    #
    u_mat2 = [numpy.zeros((norb[icor]*2, norb[icor]*2, norb[icor]*2, norb[icor]*2), numpy.complex_)
              for icor in range(ncor)]
    for icor in range(ncor):
        no = norb[icor]
        for i1 in range(2):
            for i2 in range(2):
                for i3 in range(2):
                    for i4 in range(2):
                        if i1 == i3 and i2 == i4:
                            u_mat2[icor][i1*no:(i1+1)*no, i2*no:(i2+1)*no, i3*no:(i3+1)*no, i4*no:(i4+1)*no]\
                                = u_mat[icor][:, :, :, :]
    f["DCore"]["Umat"] = u_mat2
    print("\n    Wrote to {0}".format(p["model"]["seedname"]+'.h5'))
    del f


def dcore_pre(filename):
    """
    Main routine for the pre-processing tool

    Parameters
    ----------
    filename : string
        Input-file name
    """
    print("\n@@@@@@@@@@@@@@@@@@@  Reading Input File  @@@@@@@@@@@@@@@@@@@@\n")
    print("Input File Name : ", filename)
    #
    # Construct a parser with default values
    #
    pars = create_parser()
    #
    # Parse keywords and store
    #
    pars.read(filename)
    p = pars.as_dict()
    ncor = p["model"]['ncor']
    #
    # Summary of input parameters
    #
    print("\n  @ Parameter summary")
    print("\n    [model] block")
    for k, v in p["model"].items():
        print("      {0} = {1}".format(k, v))
    print("\n    [system] block")
    for k, v in p["system"].items():
        print("      {0} = {1}".format(k, v))
    #
    # One-body term
    #
    print("\n@@@@@@@@@@@@@@@@@@@  Generate Model-HDF5 File  @@@@@@@@@@@@@@@@@@@@\n")
    seedname = p["model"]["seedname"]
    if p["model"]["lattice"] == 'wannier90':
        #
        # non_colinear flag is used only for the case that COLINEAR DFT calculation
        #
        if p["model"]["spin_orbit"]:
            p["model"]["non_colinear"] = False
        #
        if p["model"]["non_colinear"]:
            para2noncol(p)
        with open(seedname+'.inp', 'w') as f:
            __generate_wannier90_model(p, f)
        # Convert General-Hk to SumDFT-HDF5 format
        converter = Wannier90Converter(seedname=seedname)
        converter.convert_dft_input()
    else:
        with open(seedname+'.inp', 'w') as f:
            weights_in_file = __generate_lattice_model(p, f)
        # Convert General-Hk to SumDFT-HDF5 format
        converter = HkConverter(filename=seedname + ".inp", hdf_filename=seedname+".h5")
        converter.convert_dft_input(weights_in_file=weights_in_file)
    os.remove(seedname + ".inp")
    #
    # Interaction
    #
    __generate_umat(p)
    #
    # Spin-Orbit case
    #
    if p["model"]["spin_orbit"] or p["model"]["non_colinear"]:
        f = HDFArchive(seedname + '.h5', 'a')
        f["dft_input"]["SP"] = 1
        f["dft_input"]["SO"] = 1

        corr_shells = f["dft_input"]["corr_shells"]
        for icor in range(ncor):
            corr_shells[icor]["SO"] = 1
        f["dft_input"]["corr_shells"] = corr_shells

        del f
    #
    # Finish
    #
    print("\n@@@@@@@@@@@@@@@@@@@@@@  Done  @@@@@@@@@@@@@@@@@@@@@@@@\n")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog='dcore_pre.py',
        description='pre script for dcore.',
        epilog='end',
        usage='$ dcore_pre input',
        add_help=True)
    parser.add_argument('path_input_file',
                        action='store',
                        default=None,
                        type=str,
                        help="input file name."
                        )

    args = parser.parse_args()
    if os.path.isfile(args.path_input_file) is False:
        print("Input file is not exist.")
        sys.exit(-1)
    if mpi.is_master_node():
        dcore_pre(args.path_input_file)
