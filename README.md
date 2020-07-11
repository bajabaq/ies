# ies
lighting calculator

This calculates the lighting requirements for a room using the
zonal cavity method
as described in the 
IES Lighting Handbook 5th Edition
Illuminating Engineering Society (TK4161.I45)

It references the tables 9-11 and 9-12 heavily.
It interpolates and extrapolates where possible.

It currently only has 2 types of luminaries (pendant and recessed).
It also does not have a compelete set of the table data.

BUT it does work and seems to give reasonable results.

to add more data to the database, edit the CSV files in the "data" dir
and use the ./import_data.py command

edit the system_settings.txt file to add more data tables

rooms can be created in the projects folder

and these can be run by editing the ./ies_light_calc.py file
