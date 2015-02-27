# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:       parityAndSpeedTestOfArrayTracingFuncs.py
# Purpose:    1. parity tests
#                To verify the correctness of the array ray tracing functions by
#                checking the returned data against the existing single dde call
#                based ray tracing functions. The parity tests could potentially
#                be moved/used in the unit-tests for array tracing functions
#             2. speed tests
#                compute the average of best n execution times for array ray
#                tracing and compare that with single dde call based ray tracing
# Author:     Indranil Sinharoy
#
# Copyright:  (c) Indranil Sinharoy, 2012 - 2015
# Licence:    MIT License
#-------------------------------------------------------------------------------
from __future__ import print_function, division
import time as time
import pyzdde.arraytrace as at  # Module for array ray tracing
import pyzdde.zdde as pyz       # PyZDDE module
import os as os
from math import sqrt as sqrt


def set_up():
    """create dde link, and load lens into zemax, and push lens into
    zemax application (this is required for array ray tracing)
    """
    zmxfile = 'Cooke 40 degree field.zmx'
    ln = pyz.createLink()
    filename = os.path.join(ln.zGetPath()[1], "Sequential\Objectives", zmxfile)
    ln.zLoadFile(filename)
    ln.zGetUpdate()
    ln.zPushLens(1)
    return ln

def set_down(ln):
    """clean up, and close link
    """
    ln.zNewLens()
    ln.zPushLens(1)
    ln.close()

def no_error_in_ray_trace(rd, numRays):
    """This is not an "absolute". It assumes that if there have been no errors
    in tracing all rays, then the sum of all the "error" fields of the ray
    data array will be 0. However, it is possible, albeit with very small
    probability that few positive valued error may cancel out few negative
    valued errors.
    """
    sumErr = 0
    for i in range(1, numRays+1):
        sumErr += rd[i].error
    return sumErr == 0

def parity_zGetTrace_zArrayTrace_zGetTraceArray(ln, numRays):
    """function to check the parity between the ray traced data returned
    by zGetTrace(), zArrayTrace() and zGetTraceArray
    """
    x, y = [0.0]*numRays, [0.0]*numRays
    l, m, n = [0.0]*numRays, [0.0]*numRays, [0.0]*numRays
    l2, m2, n2 = [0.0]*numRays, [0.0]*numRays, [0.0]*numRays
    hx, hy, mode, surf, waveNum = 0.0, 0.0, 0, -1, 1
    radius = int(sqrt(numRays)/2)
    k = 0
    for i in xrange(-radius, radius + 1, 1):
        for j in xrange(-radius, radius + 1, 1):
            px, py = i/(2*radius), j/(2*radius)
            tData = ln.zGetTrace(waveNum, mode, surf, hx, hy, px, py)
            _, _, x[k], y[k], _, l[k], m[k], n[k], l2[k], m2[k], n2[k], _, = tData
            k += 1
    # trace data from zArrayTrace
    _, rd = get_time_zArrayTrace(numRays, retRd=True)
    # compare the two ray traced data
    tol = 1e-10
    for k in range(numRays):
        assert abs(x[k] - rd[k+1].x) < tol, "x[{}] = {}, rd[{}].x = {}".format(k, x[k], k+1, rd[k+1].x)
        assert abs(y[k] - rd[k+1].y) < tol, "y[{}] = {}, rd[{}].y = {}".format(k, y[k], k+1, rd[k+1].y)
        assert abs(l[k] - rd[k+1].l) < tol, "l[{}] = {}, rd[{}].l = {}".format(k, l[k], k+1, rd[k+1].l)
        assert abs(m[k] - rd[k+1].m) < tol, "m[{}] = {}, rd[{}].m = {}".format(k, m[k], k+1, rd[k+1].m)
        assert abs(n[k] - rd[k+1].n) < tol, "n[{}] = {}, rd[{}].n = {}".format(k, n[k], k+1, rd[k+1].n)
        assert abs(l2[k] - rd[k+1].Exr) < tol, "l2[{}] = {}, rd[{}].l = {}".format(k, l2[k], k+1, rd[k+1].Exr)
        assert abs(m2[k] - rd[k+1].Eyr) < tol, "m2[{}] = {}, rd[{}].m = {}".format(k, m2[k], k+1, rd[k+1].Eyr)
        assert abs(n2[k] - rd[k+1].Ezr) < tol, "n2[{}] = {}, rd[{}].n = {}".format(k, n2[k], k+1, rd[k+1].Ezr)
    print("Parity test between zGetTrace() and zArrayTrace() successful")
    # trace data from zGetTraceArray
    _, tData = get_time_zGetTraceArray(numRays, rettData=True)
    # compare the ray traced data
    for k in range(numRays):
        assert abs(x[k] - tData[2][k]) < tol, "x[{}] = {}, tData[2][{}] = {}".format(k, x[k], k, tData[2][k])
        assert abs(y[k] - tData[3][k]) < tol, "y[{}] = {}, tData[2][{}] = {}".format(k, y[k], k, tData[3][k])
        assert abs(l[k] - tData[5][k]) < tol, "l[{}] = {}, tData[5][{}] = {}".format(k, l[k], k, tData[5][k])
        assert abs(m[k] - tData[6][k]) < tol, "m[{}] = {}, tData[6][{}] = {}".format(k, m[k], k, tData[6][k])
        assert abs(n[k] - tData[7][k]) < tol, "n[{}] = {}, tData[7][{}] = {}".format(k, n[k], k, tData[7][k])
        assert abs(l2[k] - tData[8][k]) < tol, "l2[{}] = {}, tData[8][{}] = {}".format(k, l2[k], k, tData[8][k])
        assert abs(m2[k] - tData[9][k]) < tol, "m2[{}] = {}, tData[9][{}] = {}".format(k, m2[k], k, tData[9][k])
        assert abs(n2[k] - tData[10][k]) < tol, "n2[{}] = {}, tData[10][{}] = {}".format(k, n2[k], k, tData[10][k])
    print("Parity test between zGetTrace() and zGetTraceArray() successful")

def get_time_zArrayTrace(numRays, retRd=False):
    """return the time taken to perform ray tracing for the given number of rays
    using zArrayTrace() function.
    """
    radius = int(sqrt(numRays)/2)
    startTime = time.clock()
    rd = at.getRayDataArray(numRays, tType=0, mode=0)
    # Fill the rest of the ray data array,
    # hx, hy are zeros; mode = 0 (real), surf =  img surf, waveNum = 1
    k = 0
    for i in xrange(-radius, radius + 1, 1):
        for j in xrange(-radius, radius + 1, 1):
            k += 1
            rd[k].z = i/(2*radius)      # px
            rd[k].l = j/(2*radius)      # py
            rd[k].intensity = 1.0
            rd[k].wave = 1
    # Trace the rays
    ret = at.zArrayTrace(rd, timeout=5000)
    endTime = time.clock()
    if ret == 0 and no_error_in_ray_trace(rd, numRays):
        if retRd:
            return (endTime - startTime)*10e3, rd
        else:
            return (endTime - startTime)*10e3   # time in milliseconds

def get_time_zGetTraceArray(numRays, rettData=False):
    """return the time taken to perform tracing for the given number of rays
    using zGetTraceArray() function.
    """
    radius = int(sqrt(numRays)/2)
    startTime = time.clock()
    flatGrid = [(x/(2*radius),y/(2*radius)) for x in xrange(-radius, radius + 1, 1)
                      for y in xrange(-radius, radius + 1, 1)]
    px = [e[0] for e in flatGrid]
    py = [e[1] for e in flatGrid]
    tData = at.zGetTraceArray(numRays=numRays, px=px, py=py, waveNum=1)
    endTime = time.clock()
    if tData not in [-1, -999, -998] and sum(tData[0])==0: # tData[0] == error
        if rettData:
            return (endTime - startTime)*10e3, tData
        else:
            return (endTime - startTime)*10e3


def get_time_zGetTrace(ln, numRays):
    """return the time required to trace ``numRays`` number of rays
    using the PyZDDE function zGetTrace() that makes DDE call per trace
    """
    hx, hy, mode, surf, waveNum = 0.0, 0.0, 0, -1, 1
    radius = int(sqrt(numRays)/2)
    #print("i = ", int(sqrt(numRays)), ", numRays = ", numRays, ", a = ", -radius, ", b = ", radius+1)
    startTime = time.clock()
    errSum = 0
    for i in xrange(-radius, radius + 1, 1):
        for j in xrange(-radius, radius + 1, 1):
            px, py = i/(2*radius), j/(2*radius)
            errSum += ln.zGetTrace(waveNum, mode, surf, hx, hy, px, py)[0]
    endTime = time.clock()
    assert errSum == 0   # TO DO:: replace assert with something more meaningful
    return (endTime - startTime)*10e3   # time in milliseconds

def get_best_of_n_avg(seq, n=3):
    """compute the average of first n numbers in the list ``seq``
    sorted in ascending order
    """
    return sum(sorted(seq)[:n])/n

def compute_best_of_n_execution_times(func, numRays, numRuns, n, ln=None):
    """compute average execution time of func()
    numRays : list of the number of rays to trace
    numRuns : integer, number of times to execute the function ``func``
    n : integer, specifies how many execution times to average from the sorted
        list of execution times
    ln : PyZDDE link (only required for calling the single ray tracing
         functions)
    """
    bestnExecTimes = []
    funcName = (func.__name__).split('get_time_')[1]
    for nrays in numRays:
        print("Tracing {} rays {} times using {}".format(nrays, numRuns, funcName))
        execTimes = [0.0]*numRuns
        for i in range(numRuns):
            execTimes[i] = func(ln, nrays) if ln else func(nrays)
        bestnExecTimes.append(get_best_of_n_avg(execTimes, n))
    print("Average of best 10 execution times = \n", bestnExecTimes)
    print("\n")

def speedtest_zGetTrace_zArrayTrace_zGetTraceArray(ln):
    print("\n")
    # i's must be odd, such that i**2, which is the number of rays to plot
    # is also odd
    numRays = [i**2 for i in xrange(3, 104, 10)]
    numRuns = 50
    n = 20
    # compute average of best of 10 execution times of zArrayTrace
    compute_best_of_n_execution_times(get_time_zArrayTrace, numRays, numRuns, n)
    # compute average execution time of zGetTraceArray()
    compute_best_of_n_execution_times(get_time_zGetTraceArray, numRays, numRuns, n)
    # compute average execution time of zGetTrace
    numRuns = 1
    n = 1
    compute_best_of_n_execution_times(get_time_zGetTrace, numRays, numRuns, n, ln)

if __name__ == '__main__':
    ln = set_up()
    # parity tests
    parity_zGetTrace_zArrayTrace_zGetTraceArray(ln, 81)
    # speed test
    speedtest_zGetTrace_zArrayTrace_zGetTraceArray(ln)
    set_down(ln)