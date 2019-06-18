#!/usr/bin/python


# Get the projects in the project folder to run

import sys
import os
import curses

def get_param(prompt_string):
    screen.clear()
    screen.border(0)
    screen.addstr(2, 2, prompt_string)
    screen.refresh()
    input = screen.getstr(10, 10, 60)
    return input
#enddef

def execute_cmd(pname):
    os.system("clear")
    os.system("python ies_lighting_calc.py " + pname)
    raw_input("Press Enter")
    print ""
#enddef

#---------------------------------------------
#MAIN program here
#---------------------------------------------

projdir   = "./projects"
listfiles = os.listdir(projdir)
numproj   = len(listfiles)

x = 1
while x != ord('0'):
    screen    = curses.initscr()
    screen.clear()
    screen.border(0)

    fline = 2
    screen.addstr(fline, 2, "There are " + str(numproj) + " project files.")
    if numproj > 9:
        fline = fline+1
        screen.addstr(fline, 2, "Please enter (N)ext or P(revious) to navigate")
    #endif
    fline = fline+1
    screen.addstr(fline, 2, "Please enter the number of the project file to run...")
    
    screen.addstr(5, 4, "0 - Exit")
    i = 1
    for pfile in listfiles:
        screen.addstr(5+i, 4, str(i) + " - " + pfile)
        i = i + 1
    #endfor

    screen.refresh()

    x = screen.getch()
    
    if x != ord('0'):
        if x == ord('n'):
            print "show next 9 proj here"
        elif x == ord('p'):
            print "show prev 9 proj here"
        else:
            curses.endwin()
            pnum = chr(x)
            proj = listfiles[int(pnum)-1]
            project_name = projdir + "/" + proj
            execute_cmd(project_name)
        #endif
    #endif
#end_while

curses.endwin()
sys.exit()
