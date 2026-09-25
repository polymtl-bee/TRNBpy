# Local
import src._Utils as utils
import src._TranslateToB18 as reader
from src._Logging import logger 
# Lib
import os                   # To manage cwd path and access files in dir.
import json                 # To loads and save spacetypes.
import pandas as pd
import datetime

# ================================================================================
# Building and site Builder ======================================================
# ================================================================================

# ----- Builder for Namur -----

def NamurSiteBuilder_v2(c):

    s = pd.read_csv(c.path_UsedBuilding_SurfaceDetails + "Site.csv", skipinitialspace=True, index_col="SubBuilding")
    SurfaceRecapDict = {}

    for SuBbuilding in s.index:
        print("=========")
        print("Start ", SuBbuilding)
        print("=========")

        # Get building data ---------------------------------------
        surf_res = s.loc[SuBbuilding, "SurfaceResid"]
        surf_com = s.loc[SuBbuilding, "SurfaceCommerce"]
        surf_bur = s.loc[SuBbuilding, "SurfaceBureaux"]
        surf_ins = s.loc[SuBbuilding, "SurfaceInst"]
        surf_par = s.loc[SuBbuilding, "Parking"]
        nb_maxFloor = s.loc[SuBbuilding, "NbFloor"]
        building = s.loc[SuBbuilding, "Building"]

        # Create building file-------------------------------------
        try:
            b = SurfaceRecapDict[SuBbuilding]
        except:
            SurfaceRecapDict[SuBbuilding] = pd.DataFrame(columns=["Name", "Building", "SubBuilding", "Floor", "Weight"])
    
        # Create floors in building file --------------------------

        SurfaceRecap = SurfaceRecapDict[SuBbuilding]
        for floorID in ["Fcave", "F0", "F1", "Fstack" , "Ftop"]:
            # Update global data
            row = str(building) + "_"+str(SuBbuilding)+"_" + str(floorID)
            if row not in list(SurfaceRecap.Name):
                SurfaceRecap.loc[row, "Name"] = row
                SurfaceRecap.loc[row, "Building"] = building
                SurfaceRecap.loc[row, "SubBuilding"] = SuBbuilding
                SurfaceRecap.loc[row, "Floor"] = floorID
                SurfaceRecap.loc[row, "Weight"] = 1
                SurfaceRecap.loc[row, "BureauxCouloir"] =  0
                SurfaceRecap.loc[row, "Bureaux"] = 0
                SurfaceRecap.loc[row, "Parking"] = 0
                SurfaceRecap.loc[row, "Theatre"] = 0
                SurfaceRecap.loc[row, "Gym"] = 0
                SurfaceRecap.loc[row, "Restauration"] = 0
                SurfaceRecap.loc[row, "Commerce"] = 0
                SurfaceRecap.loc[row, "Bibliotheque"] = 0
                SurfaceRecap.loc[row, "HabitationCouloir"] = 0
                SurfaceRecap.loc[row, "Habitation"] = 0
                SurfaceRecap.loc[row, "Ecole"] = 0
                SurfaceRecap.loc[row, "Atelier"] = 0

        # Attribution rules
        ratio_mall_resto = 0.3
        ratio_office_corridor = 0.1
        ratio_dwelling_corridor = 0.05
        ratio_inst = 0.5
     
        # Tailored mixt + residentiel
        if surf_res > 0:
            for  row in SurfaceRecap.index:
                if SurfaceRecap.loc[row, "SubBuilding"] == SuBbuilding:
                    
                    if SurfaceRecap.loc[row, "Floor"] == "Fcave":
                        SurfaceRecap.loc[row, "Parking"] =  surf_par
                    
                    if SurfaceRecap.loc[row, "Floor"] == "F0":
                        # Res + Mixt
                        SurfaceRecap.loc[row, "Restauration"]      = surf_com * ratio_mall_resto
                        SurfaceRecap.loc[row, "Commerce"]          = surf_com * (1-ratio_mall_resto)
                        SurfaceRecap.loc[row, "Bureaux"]           = surf_bur 
                        # Some institutional in lot
                        SurfaceRecap.loc[row, "Theater"] = surf_ins * ratio_inst
                        SurfaceRecap.loc[row, "Library"] = surf_ins * (1 - ratio_inst)
                        # Rest is residential
                        SurfaceRecap.loc[row, "HabitationCouloir"] = max(surf_res/nb_maxFloor - surf_com - surf_bur - surf_ins, 0) * ratio_dwelling_corridor
                        SurfaceRecap.loc[row, "Habitation"]        = max(surf_res/nb_maxFloor - surf_com - surf_bur - surf_ins, 0) * (1 - ratio_dwelling_corridor)

                    surf_res_restant = surf_res/nb_maxFloor - max(surf_res/nb_maxFloor - surf_com - surf_bur - surf_ins, 0)

                    if SurfaceRecap.loc[row, "Floor"] == "F1":
                        SurfaceRecap.loc[row, "HabitationCouloir"] = surf_res/nb_maxFloor * ratio_dwelling_corridor      
                        SurfaceRecap.loc[row, "Habitation"]        = surf_res/nb_maxFloor * (1 - ratio_dwelling_corridor)  

                  
                    if SurfaceRecap.loc[row, "Floor"] == "Fstack":
                        SurfaceRecap.loc[row, "HabitationCouloir"] = (surf_res/nb_maxFloor * max(0,nb_maxFloor-3) + surf_res_restant) * ratio_dwelling_corridor
                        SurfaceRecap.loc[row, "Habitation"]        = (surf_res/nb_maxFloor * max(0,nb_maxFloor-3) + surf_res_restant)* (1 - ratio_dwelling_corridor)
 
                    if SurfaceRecap.loc[row, "Floor"] == "Ftop":
                        SurfaceRecap.loc[row, "HabitationCouloir"] = surf_res/nb_maxFloor * ratio_dwelling_corridor
                        SurfaceRecap.loc[row, "Habitation"]        = surf_res/nb_maxFloor * (1 - ratio_dwelling_corridor)

        # Other inst
        for row in SurfaceRecap.index:
            if SurfaceRecap.loc[row, "SubBuilding"] == SuBbuilding:

                if building == "1E":
                    if SurfaceRecap.loc[row, "Floor"] in ["Ftop", "F0"]:
                        SurfaceRecap.loc[row, "Atelier"] = surf_ins  /nb_maxFloor * ratio_inst
                        SurfaceRecap.loc[row, "Atelier"] = surf_ins  /nb_maxFloor * (1-ratio_inst)
                    if SurfaceRecap.loc[row, "Floor"] == "Fstack":
                        SurfaceRecap.loc[row, "Atelier"] = surf_ins  /nb_maxFloor * max(0,(nb_maxFloor -2)) * ratio_inst
                        SurfaceRecap.loc[row, "Atelier"] = surf_ins  /nb_maxFloor * max(0,(nb_maxFloor -2)) * (1-ratio_inst)

                if building in ["3E", "4E2SCHOOL"]:
                    if SurfaceRecap.loc[row, "Floor"] in ["Ftop", "F0"]:
                        SurfaceRecap.loc[row, "Ecole"] = surf_ins  /nb_maxFloor
                    if SurfaceRecap.loc[row, "Floor"] == "Fstack":
                        SurfaceRecap.loc[row, "Ecole"] = surf_ins  /nb_maxFloor * (nb_maxFloor -2)

                if building in ["2E1", "2E3"]:
                    if SurfaceRecap.loc[row, "Floor"] == "F0":
                        SurfaceRecap.loc[row, "Gym"] = surf_ins

        # Add RCPI
        for roww in SurfaceRecap.index:
            for K in ["R", "P", "I", "C", "B"]:
                SurfaceRecap.loc[roww, K] = 0.0

        for roww in SurfaceRecap.index:
            for K in ["R", "P", "I", "C", "B"]:
                for subK in c.DictSpacetype[K].keys():
                    SurfaceRecap.loc[roww, K] += SurfaceRecap.loc[roww, subK]

        # Save 
        SurfaceRecapDict[SuBbuilding] = SurfaceRecap
    


    # Save
    for subbuilding in SurfaceRecapDict.keys():
        SurfaceRecapDict[subbuilding].to_csv(c.path_UsedBuilding_SurfaceDetails +  str(subbuilding) + ".csv", index=False)

# ----- Builder for data from detailed approach -----

def _make_Site(c):
    """
    Small function to build a site recap from reading all given B18 geometrics files descriptions. 
    Return a small CSV with recap of surfaces by Subbuilding, Building, Number of floor and enduse.

    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    # Create Site recap dictionnary
    SiteDict = {"SubBuilding":{},"Building":{}, "R": {}, "C":{},"B":{},"I":{},"P":{}, "NbFloor":{}, "EndUse":{}}

    # Get list of building file names in directory
    ListOf_Building_Filenames = next(os.walk(c.path_InputB18), (None, None, []))[2]  # [] if no file
    ListOf_Building_Dict = []

    # for each of those building files (.B18) :
    for file in ListOf_Building_Filenames:
        logger.info("> Starting spacetype attribution for "+file)
        if file.endswith(".B18") or file.endswith(".b18"):
            
            # Load input file ===========================================================================
            with open(c.path_InputB18 + file, "r", encoding="iso-8859-1") as b18_file:
                b18_lines = b18_file.readlines()

            # Get zonelist ==============================================================================
            b18_dict_zone = reader._read_listZones_from_b18(b18_lines=b18_lines)
            b18_dict_zone = utils._get_zonesCharacteristics(c=c, file=file, b18_lines=b18_lines, dict_zone=b18_dict_zone)
 
            for zone in b18_dict_zone:

                # Get zone type
                try:
                    zonetype, zoneSubBuilding, zoneFloor, zoneId = zone.split("-")
                    zonecluster = file.split(".")[0] + "_" + zoneSubBuilding
                except:
                    logger.critical("Wrong zone format for file " + file + " and zone " + zone)
                
                # Get zone category
                category = None
                if zonetype.startswith("R"): 
                    category = "R"
                if zonetype.startswith("B"): 
                    category = "B"
                if zonetype.startswith("C"): 
                    category = "C"
                if zonetype.startswith("P"): 
                    category = "P"
                if zonetype.startswith("I"): 
                    category = "I"
                
                # Add
                SiteDict["SubBuilding"][zonecluster] = zoneSubBuilding
                SiteDict["Building"][zonecluster] = file.split(".")[0]

                # Add surface to right counter
                try: 
                    SiteDict[category][zonecluster]  += b18_dict_zone[zone]["Surface"]
                except:
                    SiteDict[category][zonecluster] = b18_dict_zone[zone]["Surface"]

    pd.DataFrame(SiteDict).to_csv(c.path_GeneratedSurfaceRecap+"SITE_RECAP_v2.csv", index=True, index_label="Name")

def _make_Buildings(c):
    """
    Small function to build a an input surface file for every building given as an b18 input file.
    Should be used for a "real" or detailed or reference approach to get wanted surface for site. 
    Be careful if you model building with only 1 central floor, you must manually update CSV file to match what you really want.
    Return a small CSV with recap of surfaces by Subbuilding, Building, Number of floor and enduse.

    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    # Get list of building file names in directory
    ListOf_Building_Filenames = next(os.walk(c.path_InputB18), (None, None, []))[2]  # [] if no file
    ListOf_Building_Dict = []

    # for each of those building files (.B18) :
    for file in ListOf_Building_Filenames:
        logger.info("> Starting spacetype attribution for "+file)
        if file.endswith(".B18") or file.endswith(".b18"):
            
            
            # Create Building recap dictionnary =========================================================
            BuildingDict = {"SubBuilding":{},"Building":{}, "Floor": {}, "Weight":{}, "R": {}, "C":{},"B":{},"I":{},"P":{}, "BC":{}, "RC":{}, "CB":{},"CC":{},"CG":{},"CT":{},"IA":{}, "IE":{},"IB":{}, "NbFloor":{}, "EndUse":{}}

                
            # Load input file ===========================================================================
            file_name = file.split(".")[0]
            with open(c.path_InputB18 + file, "r", encoding="iso-8859-1") as b18_file:
                b18_lines = b18_file.readlines()

            # Get zonelist ==============================================================================
            b18_dict_zone = reader._read_listZones_from_b18(b18_lines=b18_lines)
            b18_dict_zone = utils._get_zonesCharacteristics(c=c, file=file, b18_lines=b18_lines, dict_zone=b18_dict_zone)
 
            for zone in b18_dict_zone:

                # Get zone type
                try:
                    zonetype, zoneSubBuilding, zoneFloor, zoneId = zone.split("-")
                    zonecluster = file_name + "_" + zoneSubBuilding + "_" + zoneFloor
                except:
                    logger.critical("Wrong zone format for file " + file + " and zone " + zone)
                
                # Get zone category
                category = zonetype
        
                # Add
                BuildingDict["SubBuilding"][zonecluster] = zoneSubBuilding
                BuildingDict["Building"][zonecluster] = file_name
                BuildingDict["Floor"][zonecluster] = zoneFloor
                BuildingDict["Weight"][zonecluster] = "1"

                # Add surface to right counter
                try: 
                    BuildingDict[category][zonecluster]  += b18_dict_zone[zone]["Surface"]
                except:
                    BuildingDict[category][zonecluster] = b18_dict_zone[zone]["Surface"]

            pd.DataFrame(BuildingDict).to_csv(c.path_GeneratedSurfaceRecap + file_name +".csv", index=True, index_label="Name")

# ================================================================================
# Builder for schedules (from daily to annual) ===================================
# ================================================================================

# ----- Schedule utils functions -----

def _schedules_generator(weekday, saturday, sunday, dayoff=[], holiday=[]):
    """
    This function takes several daily schedules, for weekdays, saturday, sunday, dayoff and holidays.
    Then it build an annual based on those schedules values and predetermined dayoff and holiday dates.

    Return:
        schedule (list): List of the hourly values of schedules during one year.

    Args:
        weekday (list): daily schedule values for weekday.
        saturday (list): daily schedule values for saturday.
        sunday (list): daily schedule values for sunday.
        dayoff (list): daily schedule values for a typical dayoff.
        holiday (list): daily schedule values for a typical holiday day.
    """
    # ===========================================
    # 0. Initialization =========================
    # ===========================================
    year = 2023

    # Initialize schedule
    schedule = [0] * 8784 if year%4==2028%4 else [0] * 8760 
    origin = datetime.datetime(year, 1, 1)  # Monday: 0 ... Tuedsay:1 ... Sunday:6

    # ===========================================
    # 1. Day off ================================
    # ===========================================
    if len(dayoff) > 1:
        dayoff = sunday

    dayoff_date = [
        # Get off day day_in_year
        datetime.datetime(year, 1, 1).strftime("%j"),  #New eve
        datetime.datetime(year, 4, 2).strftime("%j"),  #Good friday
        datetime.datetime(year, 4, 5).strftime("%j"),  #Easter friday
        datetime.datetime(year, 5, 25 - (int(datetime.datetime(year, 5, 25).strftime("%w")) - 1)%7).strftime("%j"), #National Patriot's day (Monday before 25 May)
        datetime.datetime(year, 6, 24).strftime("%j"), #QC National holiday
        datetime.datetime(year, 7, 2) if datetime.datetime(year, 7, 1).strftime("%A")=="Sunday" else datetime.datetime(year, 7, 1).strftime("%j"), #CAN National holiday
        datetime.datetime(year, 9, 1 + (8 - int(datetime.datetime(year, 9, 1).strftime("%w")))%7).strftime("%j"), #Labour day (1st monday of september)
        datetime.datetime(year, 10, 1 + 7 + (8 - int(datetime.datetime(year, 9, 1).strftime("%w")))%7).strftime("%j"), #Thanskfiving (2nd monday of october)
        datetime.datetime(year, 12, 24).strftime("%j"), #Chrismas eve
        datetime.datetime(year, 12, 25).strftime("%j"), #Chrismas day
    ]

    # ===========================================
    # 2. Holiday ================================
    # ===========================================
    if len(holiday)>1:
        holiday = sunday

    # Holiday dates (from 1st july to 20 august)
    holiday_date = [date for date in list(range(int(datetime.datetime(year, 7, 1).strftime("%j")), int(datetime.datetime(year, 8, 20).strftime("%j"))))]

    # ===========================================
    # 3. Schedule generation ====================
    # ===========================================
    for i in range(0, len(schedule)):    

        # Get today date, day of week and hour of day
        today = pd.to_datetime(i, origin=origin, unit="h")
        day_of_week = today.strftime("%A")
        hour_of_day = int(today.strftime("%H"))
        
        # Day type is Saturday
        if day_of_week=="Saturday":
            schedule[i] = saturday[hour_of_day]

        # Day type is Sunday
        elif day_of_week=="Sunday":
            schedule[i] = sunday[hour_of_day]

        # Day type is Weekday
        else:
            schedule[i] = weekday[hour_of_day]
        
        # Check if day is a day off
        if today.strftime("%j") in dayoff_date:
            schedule[i] = dayoff[hour_of_day]
        
        # Check if day is a day off
        if today.strftime("%j") in holiday_date:
            schedule[i] = holiday[hour_of_day]

    # Remove bisectil day
    if len(schedule)>8760:
        schedule= schedule[:24*(31+28)] + schedule[24*(31+29):]

    return schedule

def _get_scheduleList_FromSpacetype(spacetype_dict, c):
    """
    This function will recursively parse a json_object, returning every instance of a specific string target.
    We use this function to detect every schedule used in a JSON spacetype file.

    Args:
        spacetype_dict (dict): The JSON object we want to parse (so the JSON spacetype file).
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    list_of_schedule_input = []

    # Defined recursive parsing
    def parse_json_recursively(json_object, target_key, list_of_schedule_input):
        if type(json_object) is dict and json_object:
            for key in json_object:
                if target_key in json_object[key]: # Found key
                    # Value is
                    value = utils._cleanString(json_object[key]).split(" ")
                    itemInput = [item for item in value if target_key in item][0].split(target_key)[1]
                    list_of_schedule_input.append(itemInput)
                else: # Continue iterating
                    list_of_schedule_input = parse_json_recursively(json_object[key], target_key, list_of_schedule_input)
        return list_of_schedule_input

    # Do recursive parsing
    json_object = spacetype_dict
    target_key = c.targetkey_INPUT
    list_of_schedule_input = parse_json_recursively(json_object=json_object, target_key=target_key, list_of_schedule_input=list_of_schedule_input)
    
    list_of_schedule_input = list(set(list_of_schedule_input))
    return list_of_schedule_input

def _generate_InputSchedule(c, input_schedule_family = ["horexA", "horexB", "horexC", "horexG", "horexD", "horexK"], input_schedule_subfamily = ["occ", "lum", "eq", "dhw", "cool", "heat", "vent"],     input_schedule_daytype = ["WD", "Sat", "Sun"]):
    """
    This function will read the input schedule file (detected at c.path_ScheduleInput).
    Then it will create an annual schedule using  _schedules_generator() function and daily schedules found in inpout schedule file.
    Schedules names must follows "Schedule family" + "_" + "Schedule category" + "Schedule daytype".
    For instance: horexA_occSat, horexB_lumSat...

    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
        input_schedule_family (list): Schedule family (for instance: CNEB Schedule G for residential). Used in schedule name definition.
        input_schedule_subfamily (list): Schedule categories (for instance: occupant schedule, light schedule...). Used in schedule name definition.
        input_schedule_daytype (list): Schedule daytype identifier (for isntance: WD for Weekday, Sat for Saturday...).  Used in schedule name definition.


    """
    # Initialize dataframe of input schedule
    sched_input = pd.DataFrame({"TIME":list(range(0, 8760))})

    # Load CSV of daily schedules
    horex_daily = pd.read_csv(c.path_ScheduleInputFile)

    for horexType in input_schedule_family:
        for horexSubType in input_schedule_subfamily:
            logger.info("> Generating input schedule for: "+ horexType + "_" + horexSubType)
            # Get daily horex
            weekday  = horex_daily[horexType + "_" + horexSubType + input_schedule_daytype[0]]
            saturday = horex_daily[horexType + "_" + horexSubType + input_schedule_daytype[1]]
            sunday   = horex_daily[horexType + "_" + horexSubType + input_schedule_daytype[2]]

            # Generate input schedule
            schedule = _schedules_generator(weekday=weekday, saturday=saturday, sunday=sunday, dayoff=sunday, holiday=sunday)

            # Save in sched_input
            sched_input[horexType + "_" + horexSubType] = schedule
    
    # ===== SAVE to CSV ==================================
    sched_input.to_csv(c.path_ScheduleAnnualInputFile, index=False)
    sched_input.to_csv(c.path_SpacetypeJSON_updated+"ScheduleInput.csv", index=False)

# ---- Update JSON with csv schedules data -----

def _update_json_with_trnsys_schedules(file, json_dict, k, time_column="TIME", value_column="VALUES", schedName=""):
    """
    This function aims to convert a schedule in csv format (list-like) to a TRNBuild schedule. 
    It will retrieve the timeColumn and valueColumn columns from the csv file using pandas and convert it to an annual schedule.
    Then the schedule definition will be added as a schedule in the spacetype given in json_dict.

    Args:
        path_to_csv (str): A string containing the path to the csv file.
        json_dict (dict): A spacetype JSON definition stored in a dictionary. 
        k (dict): keys equivalence dictionary from ClassConfiguration.
        time_column (str): The name of the column to look for timestep values. Must be in hours.
        value_column (str): The name of the column to look for schedule values. Must be in interval [0,1].
        schedName (str): The name tu use for the schedule.
    
    Return:
        json_dict (dict): The spacetype definition where to add the schedule
    """
    # Save in schedule object
    if schedName == "":
        schedName = value_column

    # Check if columns name exist
    if value_column not in list(file.columns.values):
        logger.info("FileERROR : Loading of schedule "+ schedName+ " from .csv failed because "+ value_column+ " column not found.")
        return None
    if time_column not in list(file.columns.values):
        logger.info("FileERROR : Loading of schedule "+ schedName+ " from .csv failed because "+ time_column+ " column not found.")
        return None
    
    # Get time_column and value_column
    TimeList =   [str(file[time_column][0])]
    ValueList =  [str(file[value_column][0])]

    step = 1
    old_value = file[value_column][0]
    while step < len(file[time_column]):
        new_value = file[value_column][step]

        if new_value != old_value:
            ValueList.append(str(file[value_column][step]))
            TimeList.append(str(file[time_column][step]))
            old_value = new_value
        
        step += 1
    
    # Save schedule
    item_number = str(len(json_dict["Schedules"].keys()))
    key = k["Types"]["Schedules"]["0"]
    json_dict["Schedules"][item_number] = {}
    json_dict["Schedules"][item_number][key["Name"]] = schedName
    json_dict["Schedules"][item_number][key["Source"]] = "From CSV file"
    json_dict["Schedules"][item_number][key["Description"]] = " "

    if len(file[time_column]) == 7:
        json_dict["Schedules"][item_number][key["SchedType"]] = "DAY"
    elif len(file[time_column]) == 24:
        json_dict["Schedules"][item_number][key["SchedType"]] = "HOUR"
    elif len(file[time_column]) == 8760:
        json_dict["Schedules"][item_number][key["SchedType"]] = "ANNUAL"
    else:
        logger.info("FileERROR : Loading of schedule "+ schedName+ " from .csv failed because wrong number of values. Must be of length 7 (DAY), 24 (HOUR) or 8760 (ANNUAL).")
        logger.info("FileERROR : Current length: "+ str(len(file[time_column])))
    json_dict["Schedules"][item_number][key["TimeList"]] = TimeList
    json_dict["Schedules"][item_number][key["ValueList"]] = ValueList

    # Return schedule
    return json_dict

def _update_json_with_input_schedules(json_dict, k, schedName=""):
    """
    This function will write the schedule schedName in json_dict JSON spacetype file. 
    No time and values series are given because this schedule is an input in the B18 file.
    The schedule type will be input so that B18 update will interprete this schedule as an input.

    Return:
        json_dict (dict): The spacetype definition where to add the schedule

    Args:
        json_dict (dict): A spacetype JSON definition stored in a dictionary. 
        k (dict): keys equivalence dictionary from ClassConfiguration.
        schedName (str): The name tu use for the schedule.
    """
    # Save in schedule object
    if schedName == "":
        schedName = json_dict["Schedules"][item_number][key["Name"]]

    # Save schedule
    key = k["Types"]["Schedules"]["0"]

    already_exist = False
    for item_number in json_dict["Schedules"].keys():
        if schedName == json_dict["Schedules"][item_number][key["Name"]]:
            already_exist = True

    if not already_exist:
        item_number = str(len(json_dict["Schedules"].keys()))
        json_dict["Schedules"][item_number] = {}
        json_dict["Schedules"][item_number][key["Name"]] = schedName
        json_dict["Schedules"][item_number][key["Source"]] = "From CSV file"
        json_dict["Schedules"][item_number][key["Description"]] = " "
        json_dict["Schedules"][item_number][key["SchedType"]] = "INPUT"

    # Return schedule
    return json_dict

# ----- Main function -----

def _loadAllSchedules_InAllSpacetypes(c):
    """
    This function loads all schedules from c.path_ScheduleHourlyTRNSYS, c.path_ScheduleDailyTRNSYS, c.path_ScheduleAnnualTRNSYS and c.path_ScheduleInput files.
    Then those schedules are written in spacetypes where the schedule is used (where its name is detected in a spacetype JSON file).

    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """

    # ===============================================================================
    # ===== 1. Initialize spacetype =================================================
    # ===============================================================================
    logger.info("INITIALIZE SPACETYPE")

    # ===== SCHEDULES HOUR =============================
    try:
        sched_hourly = pd.read_csv(c.path_ScheduleHourlyTRNSYS)
    except:
        logger.info("> No files for hourly schedules detected")
        flag_horexhour = False
    else:
        logger.info("> Found hourly schedules for spacetype")
        flag_horexhour = True

    # ===== SCHEDULES DAY ==============================
    try:
        sched_daily = pd.read_csv(c.path_ScheduleDailyTRNSYS)
    except:
        logger.info("> No files for daily schedules detected")
        flag_horexday = False
    else:
        logger.info("> Found daily schedules for spacetype")
        flag_horexday = True

    # ===== SCHEDULES ANNUAL ===========================
    try:
        sched_annual = pd.read_csv(c.path_ScheduleAnnualTRNSYS)
    except:
        logger.info("> No files for annual schedules detected")
        flag_horexannual = False
    else:
        logger.info("> Found annual schedules for spacetype")
        flag_horexannual = True

    # ===== SCHEDULES INPUT =============================
    try:
        sched_input = pd.read_csv(c.path_SpacetypeJSON_updated+"ScheduleInput.csv")
    except:
        flag_horexinput = False
        logger.info("> No files for annual input schedules detected. Trying to generate one.")
        try:
            pd.read_csv(c.path_ScheduleInputFile)
        except:
            logger.info(">> No data detected for input schedules.")
        else:
            _generate_InputSchedule(c=c, input_schedule_family=c.InputFamily)  # If no 
            sched_input = pd.read_csv(c.path_SpacetypeJSON_updated+"ScheduleInput.csv")
            flag_horexinput = True
    else:
        flag_horexinput = True
        logger.info("> Input schedule file detected. Using this file instead of generating a new one: " +c.path_ScheduleAnnualInputFile)

      
    # ===============================================================================
    # ===== 2. WRITE SCHEDULES IN SPACETYPES ========================================
    # ===============================================================================
    logger.info("WRITING Schedules in SPACETYPE -----")

    ListOf_SpaceType_Filenames = (x for x in next(os.walk(c.path_SpacetypeJSON_raw), (None, None, []))[2] if ".json" in x)  # [] if no file
    ListOf_SpaceType_Dict = []

    # for each spacetype file (.json) ==========================
    for file in ListOf_SpaceType_Filenames:            
        # Read current spacetype
        with open(c.path_SpacetypeJSON_raw + file) as file:
            spacetype_dict = json.load(file)

        # Get list of schedule used
        list_schedules = _get_scheduleList_FromSpacetype(spacetype_dict, c=c)


        # For each schedule, get series from one of the files
        for schedule in list_schedules:
            scheduleFound = 0
            if flag_horexhour:
                if schedule in sched_hourly.columns:
                    spacetype_dict = _update_json_with_trnsys_schedules(sched_hourly, spacetype_dict, c.keys, time_column=sched_hourly.columns[0], value_column=schedule, schedName=schedule)
                    scheduleFound += 1

            if flag_horexday:
                if schedule in sched_daily.columns:
                    spacetype_dict = _update_json_with_trnsys_schedules(sched_daily, spacetype_dict, c.keys, time_column=sched_daily.columns[0], value_column=schedule, schedName=schedule)
                    scheduleFound += 1

            if flag_horexannual:
                if schedule in sched_annual.columns:
                    spacetype_dict = _update_json_with_trnsys_schedules(sched_annual, spacetype_dict, c.keys, time_column=sched_annual.columns[0], value_column=schedule, schedName=schedule)
                    scheduleFound += 1

            if flag_horexinput:
                if schedule in sched_input.columns:
                    spacetype_dict = _update_json_with_input_schedules(spacetype_dict, c.keys,schedName=schedule)
                    scheduleFound += 1

            # Schedule not detected in any schedule file ?
            if scheduleFound==0:
                logger.critical("No data detected for schedule: "+schedule)
            elif scheduleFound>1:
                logger.critical("Duplicate data found for: "+schedule)

        # ===== SAVE JSON ==================================
        with open(c.path_SpacetypeJSON_updated + spacetype_dict["Name"] + ".json", "w") as file:
            json.dump(spacetype_dict, file, indent=4)
            logger.info("SAVED for: "+str(spacetype_dict["Name"]))

# ================================================================================
# ================================================================================
# ================================================================================
