#!/usr/bin/python

import ConfigParser
import os
import sys
import csv
import sqlite3
import hashlib

#------------------------------------------------------------------------------
#get digest of file using given hasher (md5, sha256, etc)
#------------------------------------------------------------------------------
def hashfile(afile, hasher, blocksize=65536):
    fh = open(afile, 'rb')
    buf = fh.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = fh.read(blocksize)
    fh.close()
    return hasher.hexdigest()

#------------------------------------------------------------------------------
#check filename hash value matches that saved in the settings file
#returns True if matches, the hash if it does not
#------------------------------------------------------------------------------    
def check_hash(settings, section, filename):
    bname = os.path.basename(filename)
    saved_digest256 = settings.get(section, bname)    
    digest256       = hashfile(filename, hashlib.sha256())
    
    #print filename
    #print saved_digest256
    #print digest256
    
    result = False
    if saved_digest256 == digest256:
        result = True
    else:
        result = digest256
    #endif
    #print result
    return result
#endif

#------------------------------------------------------------------------------
#Update the settings file with the latest hash
#------------------------------------------------------------------------------
def update_hash(settings, settings_file, section, item, value):
    print "...updating hash in config file for " + item + " ..."
    settings.set(section, item, value)    
    with open(settings_file,'wb') as configfile:
            settings.write(configfile)
    #endwith            
#enddef


#------------------------------------------------------------------------------
#Get the SQL to create the table in the database
#------------------------------------------------------------------------------
def get_create_SQL(file):
    if file == 'eff_base_refl.csv':
        SQL = """CREATE TABLE eff_base_refl (
                 base int, 
                 wall int, 
                 cavity_ratio float,
                 eff_base_refl float
                 );
              """
    elif file == 'coef_util.csv':
        SQL = """CREATE TABLE coef_util ( 
                    luminaire_id int,
                    eff_ceil float,
                    wall float,
                    cavity_ratio float,
                    cu float
                    );                 
              """
    elif file == 'luminaire_info.csv':
        SQL = """CREATE TABLE luminaire_info ( 
                    luminaire_id int,
                    description text,
                    maint_cat text,
                    max_s_mh float,
                    percent_lumens_up float,
                    percent_lumens_down float,
                    comment text
                    );
              """
    elif file == 'rsdd.csv':
        SQL = """CREATE TABLE rsdd (
                    ltype text,
                    expect_dirt_depr float,
                    rcr float,
                    rsdd float
                    );
               """
    elif file == 'ldd.csv':
        SQL = """CREATE TABLE ldd (
                    maint_cat text,
                    b float,
                    dirtiness text,
                    a float
                    );
               """
    elif file == 'floor_mf.csv':
        SQL = """CREATE TABLE floor_mf (
                    ceil float,
                    wall float,
                    eff_floor float,
                    cavity_ratio float,
                    mf float
                    );
               """
    #endif
              
    return SQL
#enddef

#------------------------------------------------------------------------------
#Get the SQL to load the data to the database
#------------------------------------------------------------------------------
def get_load_SQL(xfile):
    if xfile == 'eff_base_refl.csv':
        SQL = """INSERT INTO eff_base_refl (base, wall,  cavity_ratio, eff_base_refl)
                 VALUES                    (:base, :wall, :cavity_ratio, :eff_base_refl)
              """
    elif xfile == 'coef_util.csv':
        SQL = """INSERT INTO coef_util ( luminaire_id,  eff_ceil,  wall,  cavity_ratio,  cu)
                 VALUES                (:luminaire_id, :eff_ceil, :wall, :cavity_ratio, :cu)
              """
    elif xfile == 'luminaire_info.csv':
        SQL = """INSERT INTO luminaire_info ( luminaire_id,  description,  maint_cat, max_s_mh, percent_lumens_up, percent_lumens_down, comment)
                 VALUES                    ( :luminaire_id, :description, :maint_cat, :max_s_mh, :percent_lumens_up, :percent_lumens_down, :comment)
              """        
    elif xfile == 'rsdd.csv':
        SQL = """INSERT INTO rsdd ( ltype, expect_dirt_depr, rcr, rsdd)
                 VALUES          ( :ltype, :expect_dirt_depr, :rcr, :rsdd)
              """        
    elif xfile == 'ldd.csv':
        SQL = """INSERT INTO ldd ( maint_cat, b, dirtiness, a)
                 VALUES          ( :maint_cat, :b, :dirtiness, :a)
              """       
    elif xfile == 'floor_mf.csv':
        SQL = """INSERT INTO floor_mf ( ceil,  wall, eff_floor, cavity_ratio, mf)
                 VALUES              ( :ceil, :wall, :eff_floor, :cavity_ratio, :mf)
              """        
    #endif
    
    return SQL
#enddef

#------------------------------------------------------------------------------
#Drop table and reload it to the database
#------------------------------------------------------------------------------
def reload_csv(settings, settings_file, xfile, result):
    print "Updating " + xfile + "..."
    
    table = os.path.splitext(xfile)[0]
    
    db_filename = get_db_filename(settings)
    conn = sqlite3.connect(db_filename)
    
    print "...dropping the table..."
    SQL = 'DROP TABLE IF EXISTS ' + table + ';'
    conn.executescript(SQL)
    
    print "...creating the table..."
    SQL = get_create_SQL(xfile)
    conn.executescript(SQL)
    
    print "...loading the table..."
    data_filename = get_data_filename(settings,xfile)
    with open(data_filename, 'rt') as csv_file:
        csv_reader    = csv.DictReader(csv_file)
        SQL           = get_load_SQL(xfile)        
        conn.executemany(SQL, csv_reader)    
    #endwith
    conn.commit()
    
    conn.close()
        
    update_hash(settings, settings_file, 'data_hashes', xfile, result)            
    print "...Done"
#enddef

#------------------------------------------------------------------------------
#Check if the data has changed
#------------------------------------------------------------------------------
def check_data(settings, settings_file):
    print "Checking each data file listed in the settings file..."
    data_path = settings.get('system', 'data_dir')
    data_file_hashes = dict(settings.items('data_hashes'))
    for file,hash in data_file_hashes.iteritems():
        fname = os.path.abspath(data_path + '/' + file)        
        result = check_hash(settings,'data_hashes',fname)        
        if result == True:
            print "OK " + file
        else:     
            #TODO make this interactive
            print "Data file differs from previous...Do you wish to update the database (Y/N)? [Y]"
            response = "y"
            if response == "y":
                reload_csv(settings, settings_file, file, result)
            #endif
        #endif      
    #endfor   
    print "...checking finished"
    return
#enddef

#------------------------------------------------------------------------------
#Get data filename
#------------------------------------------------------------------------------
def get_data_filename(settings,data):
    path          = settings.get('system','data_dir')    
    data_filename = os.path.abspath(path + '/' + data)
    return data_filename
#enddef

#------------------------------------------------------------------------------
#Get database filename
#this might should be in own module vs copy in each source file
#------------------------------------------------------------------------------
def get_db_filename(settings):
    db_path         = settings.get('system','data_dir')
    db_filename_org = settings.get('system','database')
    db_filename     = os.path.abspath(db_path + '/' + db_filename_org)
    return db_filename
#enddef

#------------------------------------------------------------------------------
#See if database exists, if not then touch it, if so do nothing
#------------------------------------------------------------------------------
def check_database(settings):
    db_filename = get_db_filename(settings)    
    db_exists   = os.path.exists(db_filename)

    if not db_exists:    
        print "Touching database"
        conn = sqlite3.connect(db_filename)
        conn.close()
    else:
        print "Database exists - doing nothing"
    #endif
    
    return
#enddef

#------------------------------------------------------------------------------
# Main Execution point
#------------------------------------------------------------------------------
if __name__ == '__main__':

    #read the system settings file (maybe should be in own module)
    settings = ConfigParser.SafeConfigParser()
    settings_file = os.path.abspath('system_settings.txt')
    settings.read(settings_file)

    check_database(settings)
        
    #check the data files are up to date(listed in the system_settings file)
    check_data(settings, settings_file)
        
    print "Done"    

#endif
