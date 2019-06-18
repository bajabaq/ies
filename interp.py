#!/usr/bin/python

#------------------------------------------------------------------
# Program to calculate lamps needed for space
# based on IES procedure
#------------------------------------------------------------------
import os
import sys
import math
import ConfigParser

from hvac_database import get_db_filename, do_query
from hvac_math     import interpolate_val, extrapolate_val, mean


#what happens if col_val > max col or col_val < min col?
#it should get the two previous ones
def get_ends(settings, table, col, col_val):
    SQL_vars = ()
    #get hi
    SQL      = """SELECT DISTINCT {col} FROM {table} WHERE {col} >= {col_val} ORDER BY {col} ASC;"""
    SQL      = SQL.format(col=col,table=table,col_val=col_val)
    results  = do_query(settings, SQL, SQL_vars)
    #print "*" * 22
    #print results
    [hi_col1, hi_col2]  = get_n_results(results,2)
    hi_col = hi_col1

    #get low
    SQL     = """SELECT DISTINCT {col} FROM {table} WHERE {col} <= {col_val} ORDER BY {col} DESC;"""
    SQL     = SQL.format(col=col,table=table,col_val=col_val)
    results = do_query(settings, SQL, SQL_vars)
    #print results
    [low_col1, low_col2] = get_n_results(results,2)
    low_col = low_col1

    #print hi_col2, hi_col1, col_val, low_col1, low_col2
    #print "*" * 22
    
    if hi_col1 == 999999:
        hi_col  = low_col1
        low_col = low_col2
    elif low_col1 == 999999:
        hi_col  = hi_col2
        low_col = hi_col1
    #endif    
    return [hi_col, low_col]
#enddef



def interpolate_one(y2,y1,x2,x1,x):
    print "interpolate one"
    #                       y2,   y1, x2, x1, x
#    val = extrapolate_val(0.94, 0.96, 30, 20, 25)
#    print val

    val = extrapolate_val(y2, y1, x2, x1, x)
    print val
    return val
    
def interpolate_two():
    print "interpolate two"

def interpolate_three():
    print "interpolate three"
    
def interpolate_four():
    print "interpolate four"

#read the system settings file (maybe should be in own module - along w/ get_database name)
settings      = ConfigParser.SafeConfigParser()
settings_file = os.path.abspath('system_settings.txt')    
settings.read(settings_file)

#interpolate_1d is interpolate

def interpolate_2d(settings, (table_name, col, col_val), (d1_name, d1_val), (d2_name, d2_val), val_name):
    print table_name,col,col_val,d1_name,d1_val,d2_name,d2_val,val_name
    SQL = """SELECT {val_name} FROM {table_name} WHERE {col} = ? AND {d1_name} = ? AND {d2_name} = ?;"""
    SQL = SQL.format(val_name=val_name,table_name=table_name,col=col,d1_name=d1_name,d2_name=d2_name)
    SQL_vars = (col_val,d1_val,d2_val)
    results  = do_query(settings, SQL, SQL_vars)
    print SQL
    print SQL_vars
    print results
    sys.exit()
    
#    print dirtiness_per, ltype
    [hi_dirt_per, low_dirt_per] = get_ends(settings, 'rsdd', 'expect_dirt_depr', dirtiness_per)
#    print hi_dirt_per, low_dirt_per

#    print room_CR
    [hi_rcr, low_rcr] = get_ends(settings, 'rsdd', 'rcr', room_CR)
#    print hi_rcr, low_rcr

    #hi-hi; hi-low; low-hi; low-low
    
    return val

#2d is a square
val = interpolate_2d(settings, ('rsdd', 'ltype','direct'), ('expect_dirt_depr', 25), ('rcr', 2.5), 'rsdd')
    
#                        y2,   y1, x2, x1, x    
#val1 = interpolate_one(0.94, 0.96, 30, 20, 25)  #rcr 2   #.95
#val2 = interpolate_one(0.93, 0.95, 30, 20, 25)  #rcr 3   #.94
#val3 = interpolate_one(0.95, 0.96,  3,  2, 2.5) #%dd 20  #.955
#val4 = interpolate_one(0.93, 0.94,  3,  2, 2.5) #%dd 30  #.935

#val = interpolate_two(val1, val2, 2, 3, 1)


#interpolate_x(table,15,55,25,2.5)
#(10,20) =get_ends(15, table)
#(50,70) =get_ends(55, table)
#(10,30) =get_ends(25, table)
#(2,3)   =get_ends(2.5, table)

#interpolate_one(table,  2, 3, 20)
#interpolate_one(table,  2, 3, 30)
#interpolate_one(table, 20, 30, 2)
#interpolate_one(table, 20, 30, 3)

#interpolate_1d
#interpolate_2d
#interpolate_3d
#interpolate_4d
    
