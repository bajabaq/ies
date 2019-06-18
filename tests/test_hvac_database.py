
import pytest

import ConfigParser
import os

from .. import hvac_database

 
def test_hvac_database():
    #read the system settings file (maybe should be in own module - along w/ get_database name)
    settings      = ConfigParser.SafeConfigParser()
    settings_file = os.path.relpath('../system_settings.txt')
    settings.read(settings_file)    

    assert hvac_database.get_db_filename(settings) == os.path.relpath('../data/ies.sqlite')

def test_do_query():
    #read the system settings file (maybe should be in own module - along w/ get_database name)
    settings      = ConfigParser.SafeConfigParser()
    settings_file = os.path.abspath('../system_settings.txt')
    settings.read(settings_file)    
    SQL = """SELECT cu FROM coef_util WHERE luminaire_id = ? AND eff_ceil = ? AND wall = ? and cavity_ratio = ?"""    
    SQL_vars = (5, 50,50,1,)    
    assert hvac_database.do_query(settings, SQL, SQL_vars) == [(1.03,)]
