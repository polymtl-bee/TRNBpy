# Local
import src._Utils as utils
from src._Logging import logger 
# Lib
import os 
import json                 # To loads and save spacetypes.

# ================================================================================
# Reading ========================================================================
# ================================================================================

# ---- Read lists of inputs, outputs, zones -----

def _read_listOutput_fromB18(path_b18):
    """
    Return a list of all output of .b18 file in the path *path*. An output is named as following "output_name + airnode_name"

    Args:
        path_b18 (string): Path to the .b18 file where to read outputs.

    Return:
        list_output (list): A list of every output found in path_b18 file
    """

    # Load B18 file ----------------------
    with open(path_b18, "r", encoding="iso-8859-1") as b18_file:
        b18_lines = b18_file.readlines()

    # Go to OUTPUTS
    fcount = utils._checkStr(b18_lines, "O u t p u t s") + 2
    airnode_fcount = utils._checkStr(b18_lines, "AIRNODES =", begin=fcount, end_string="*----------------")

    # Initializing 
    list_output = []

    # Loop to get all cooling until none is found in Trnbuild cooling definition area.
    while airnode_fcount != None:
        # Get airnode name from 1st line
        line =utils._cleanString(b18_lines[airnode_fcount])
        airnode_name = line.split(" = ")[1]


        # Read first output for airnode
        output_count = 1
        line =utils._cleanString(b18_lines[airnode_fcount + output_count])
        # Save all output for airnode
        while ("AIRNODES =" not in line) and ("*-----" not in line):
                output_name = line.split(" : ")[1].split(" - ")[0]
                list_output.append(output_name+ "_" + airnode_name)

                output_count += 1
                line =utils._cleanString(b18_lines[airnode_fcount + output_count])

        # Go to next airnode
        airnode_fcount = utils._checkStr(b18_lines, "AIRNODES =", begin=airnode_fcount+1, end_string="*----------------", raise_error=False)
    return list_output

def _read_listInput_fromB18(path_b18):
    """
    Return a list of all input of .b18 file in the path *path*. An input is named as following "input_name + airnode_name"

    Args:
        path_b18 (string): Path to the .b18 file where to read inputs.

    Return:
        list_inputs (list): A list of every input found in path_b18 file
    """

    # Load B18 file ----------------------
    with open(path_b18, "r", encoding="iso-8859-1") as b18_file:
        b18_lines = b18_file.readlines()

    # Go to input
    fcount = utils._checkStr(b18_lines, "I n p u t s") + 2

    # Initializing :
    line = b18_lines[fcount]
    clean_line =utils._cleanString(line)
    clean_list = clean_line.split(" ")[1:]
    step, list_inputs = 0, []
    
    # For each new line detected :
    while ";" in clean_list[-1]:
        # Save list of name except last item (always ";" except for last zone)
        list_inputs += clean_list[:-1]
        
        # Get next line as a list of zone
        step += 1
        new_line =utils._cleanString(b18_lines[fcount+step])
        clean_list = new_line.split(" ")

    # Save last zone name without \n part of the string
    list_inputs += clean_list[:]

    return list_inputs

def _read_listZones_from_b18(b18_lines):
    """
    Given a b18 list-like file, this function will return a dict of all zones in the file. 
    Each zone is a dictionary containing its own name in key "Name".

    Args:
        b18_lines (list-like): a list-like object of a TRNSYS building.

    Return: 
        dict_zone (dict): dict of all zones defined in the file. Each zone is a dictionary containing its own name in key "Name".
    """
    # Get line of zones list of names
    fcount = utils._checkStr(b18_lines, "Z o n e s") + 2

    # Get line (without first string "ZONES")
    line = b18_lines[fcount]
    clean_line =utils._cleanString(line)
    clean_list = clean_line.split(" ")[1:]
    # Initializing :
    step, list_zone_names = 0, []

    # For each new line detected :
    while ";" in clean_list[-1]:
           
        # Save list of name except last item (always ";" except for last zone)
        list_zone_names += clean_list[:-1]
        
        # Get next line as a list of zone
        step += 1
        new_line =utils._cleanString(b18_lines[fcount+step])
        clean_list = new_line.split(" ")

    # Save last zone name without \n part of the string
    list_zone_names += clean_list[:]

    # Convert to dict
    dict_zone = {}
    for zonename in list_zone_names:
        dict_zone[zonename] = {}
        dict_zone[zonename]["Name"] = zonename


        # Some basic verification
        match_ = 0
        for zone in list_zone_names:
            if zone == zonename:
                match_ += 1
        if match_>1:
            logger.critical("Duplicate zone found in file. Zone name: "+zonename)
            print("======================================")
            print("======================================")
            print("======================================")
            print(list_zone_names)

    return dict_zone

# ---- Update JSON from B18 template -----

def update_json_with_b18_coolings(b18_name, b18_lines, json_dict, k):
    """
    Given a b18 list-like file, this function will update the json dict with all cooling defined in the file.

    Return:
        json_dict (dict): The json_dict udapted with all the cooling defined in b18_lines.
    Args:
        b18_name (str): Name of the spacetype we are reading.
        b18_lines (list-like): a list-like object of a spacetype (as a TRNSYS building).
        json_dict (dict): a nested dictionnaries where the spacetype data is to be stored.
        key (dict): A subset of the json key dictionnary containing keys for coolings definition.
    """
    
    # Get line of cooling zones and line of 1st cooling
    fcount_min = utils._checkStr(b18_lines, "C o o l i n g") + 2
    coolcount = utils._checkStr(b18_lines, "COOLING", begin=fcount_min, end_string="*----------------")
    
    # Initializing 
    list_cooling = []

    # Loop to get all cooling until none is found in Trnbuild cooling definition area.
    while coolcount != None:
        # Get cooling name from 1st line
        line1 = utils._cleanString(b18_lines[coolcount])
        coolName = line1.split(" ")[1]

        # Get values from 2nd line
        line2 = utils._cleanString(b18_lines[coolcount+1])
        preline2 = line2.split(":")

        for element in preline2:
            label, value = utils._cleanString(element).split("=")

            coolType, Tconsigne = "CONSTANT", "26"
            if "ON" in label:
                if "INPUT" in value:
                    coolType = "INPUT"
                    # Get value from "INPUT 1*inputname"
                    preTconsigne = value.split("1*")[1]
                    Tconsigne = utils._cleanString(preTconsigne)
                elif "SCHEDULE" in value:
                    coolType = "SCHEDULE"
                    # Get value from "SCHEDULE 1*schedulename"
                    preTconsigne = value.split("1*")[1]
                    Tconsigne = utils._cleanString(preTconsigne)
                else:
                    coolType = "CONSTANT"
                    Tconsigne = value

            coolPower = "100"
            if "POWER" in label:
                coolPower = value
            
            humidity = "0"
            if "HUMIDITY" in label:
                humidity = value
            
            arelpower = "0"
            if "AREA_RELATED_POWER" in label:
                arelpower = value
            
            elpowerfrac = "0"
            if "ELPOWERFRAC" in label:
                elpowerfrac = value
            
            rrad = "0"
            if "RRAD" in label:
                rrad = value
            
        # Save cooling
        item_number = len(json_dict["Types"]["Coolings"].keys())
        key = k["Types"]["Coolings"]["0"]
        json_dict["Types"]["Coolings"][item_number][key["Name"]] = coolName
        json_dict["Types"]["Coolings"][item_number][key["Source"]] = "From file:" + b18_name
        json_dict["Types"]["Coolings"][item_number][key["Description"]] = " "
        json_dict["Types"]["Coolings"][item_number][key["Type"]] = coolType
        json_dict["Types"]["Coolings"][item_number][key["Power"]] = coolPower
        json_dict["Types"]["Coolings"][item_number][key["TdbConsigne"]] = Tconsigne
        json_dict["Types"]["Coolings"][item_number][key["AreaRelPower"]] = arelpower
        json_dict["Types"]["Coolings"][item_number][key["RadFrac"]] = rrad
        json_dict["Types"]["Coolings"][item_number][key["Humidity"]] = humidity
        json_dict["Types"]["Coolings"][item_number][key["ElecPowerFrac"]] = elpowerfrac
     
        # Look for next cooling
        coolcount = utils._checkStr(b18_lines, "COOLING", begin=coolcount+1, end_string="*----------------", raise_error=False)

    return json_dict

def update_json_with_b18_gains(b18_name, b18_lines, json_dict, k):
    """
    Given a b18 list-like file, this function will update the json dict with all gains defined in the file.

    Return:
        json_dict (dict): The json_dict udapted with all the gains defined in b18_lines.
    Args:
        b18_name (str): Name of the spacetype we are reading.
        b18_lines (list-like): a list-like object of a spacetype (as a TRNSYS building).
        json_dict (list-like): a nested dictionnaries where the spacetype data is to be stored.
        key (dict): A subset of the json key dictionnary containing keys for gains definition.

    """
    
    # Get line of gain zones and line of 1st gain
    fcount_min = utils._checkStr(b18_lines, "G a i n s / L o s s e s") + 2
    gaincount = utils._checkStr(b18_lines, "GAIN", begin=fcount_min, end_string="*----------------")
    
    # Initializing 
    list_gain = []

    # Loop to get all gain until none is found in Trnbuild gain definition area.
    while gaincount != None:
        # Get gain name from 1st line
        line1 = utils._cleanString(b18_lines[gaincount])
        gainName = line1.split(" ")[1]
        
        # Get values from 2nd line
        line2 = utils._cleanString(b18_lines[gaincount+1])
        preline2 = line2.split(":")

        for element in preline2:
            # Sepatate "LABEL=value"
            try:
                label, value = utils._cleanString(element).split("=")

                # Get gain Attributes :
                convective = "100"
                if "CONVECTIVE" in label:
                    convective = value

                radiative = "0"
                if "RADIATIVE" in label:
                    radiative = value
                
                humidity = "0"
                if "HUMIDITY" in label:
                    humidity = value
                
                elpowerfrac = "0"
                if "ELECPOWERFRAC" in label:
                    elpowerfrac = value

                gainCategory = "0"
                if "CATEGORY" in label:
                    gainCategory = value
            except:
                gainType = utils._cleanString(element)

        # Save gain
        item_number = len(json_dict["Types"]["Gains"].keys())
        key = k["Types"]["Gains"]["0"]
        json_dict["Types"]["Gains"][item_number][key["Name"]] = gainName
        json_dict["Types"]["Gains"][item_number][key["Source"]] = "From file: "+b18_name
        json_dict["Types"]["Gains"][item_number][key["Description"]] = " "
        json_dict["Types"]["Gains"][item_number][key["GainCategory"]] = gainCategory
        json_dict["Types"]["Gains"][item_number][key["GainType"]] = gainType
        json_dict["Types"]["Gains"][item_number][key["Convective"]] = convective
        json_dict["Types"]["Gains"][item_number][key["Radiative"]] = radiative
        json_dict["Types"]["Gains"][item_number][key["Humidity"]] = humidity
        json_dict["s"]["Gains"][item_number][key["ElecPowerFrac"]] = elpowerfrac

        # Look for next gain
        gaincount = utils._checkStr(b18_lines, "GAIN", begin=gaincount+1, end_string="*----------------", raise_error=False)

    return json_dict

def update_json_with_b18_heatings(b18_name, b18_lines, json_dict, k):
    """
    Given a b18 list-like file, this function will update the json dict with all heating defined in the file.

    Return:
        json_dict (dict): The json_dict udapted with all the heating defined in b18_lines.
    Args:
        b18_name (str): Name of the spacetype we are reading.
        b18_lines (list-like): a list-like object of a spacetype (as a TRNSYS building).
        json_dict (list-like): a nested dictionnaries where the spacetype data is to be stored.
    """
    
    # Get line of heating zones and line of 1st heating
    fcount_min = utils._checkStr(b18_lines, "H e a t i n g") + 2
    heatcount = utils._checkStr(b18_lines, "HEATING", begin=fcount_min, end_string="*----------------")
    
    # Initializing 
    list_heating = []

    # Loop to get all heating until none is found in Trnbuild heating definition area.
    while heatcount != None:
        # Get heating name from 1st line
        line1 = utils._cleanString(b18_lines[heatcount])
        heatName = line1.split(" ")[1]

        # Get values from 2nd line
        line2 = utils._cleanString(b18_lines[heatcount+1])
        preline2 = line2.split(":")

        for element in preline2:
            # Sepatate "LABEL=value"
            label, value = utils._cleanString(element).split("=")

            # Get Heating Attributes :

            heatType, Tconsigne = "CONSTANT", "20"
            if "ON" in label:
                if "INPUT" in value:
                    heatType = "INPUT"
                    # Get value from "INPUT 1*inputname"
                    preTconsigne = value.split("1*")[1]
                    Tconsigne = utils._cleanString(preTconsigne)
                elif "SCHEDULE" in value:
                    heatType = "SCHEDULE"
                    # Get value from "SCHEDULE 1*schedulename"
                    preTconsigne = value.split("1*")[1]
                    Tconsigne = utils._cleanString(preTconsigne)
                else:
                    heatType = "CONSTANT"
                    Tconsigne = value

            heatPower = "100"
            if "POWER" in label:
                heatPower = value

            humidity = "0"
            if "HUMIDITY" in label:
                humidity = value
            
            arelpower = "0"
            if "AREA_RELATED_POWER" in label:
                arelpower = value

            elpowerfrac = "0"
            if "ELPOWERFRAC" in label:
                elpowerfrac = value
            
            rrad = "0"
            if "RRAD" in label:
                rrad = value
            
        # Save heating
        item_number = len(json_dict["Types"]["Heatings"].keys())
        key = k["Types"]["Heatings"]["0"]
        json_dict["Types"]["Heatings"][item_number][key["Name"]] = heatName
        json_dict["Types"]["Heatings"][item_number][key["Source"]] = "From file:" + b18_name
        json_dict["Types"]["Heatings"][item_number][key["Description"]] = " "
        json_dict["Types"]["Heatings"][item_number][key["Type"]] = heatType
        json_dict["Types"]["Heatings"][item_number][key["PowerHeat"]] = heatPower
        json_dict["Types"]["Heatings"][item_number][key["TdbConsigne"]] = Tconsigne
        json_dict["Types"]["Heatings"][item_number][key["AreaRelPower"]] = arelpower
        json_dict["Types"]["Heatings"][item_number][key["RadFrac"]] = rrad
        json_dict["Types"]["Heatings"][item_number][key["Humidity"]] = humidity
        json_dict["Types"]["Heatings"][item_number][key["ElecPowerFrac"]] = elpowerfrac
     
        # Look for next heating
        heatcount = utils._checkStr(b18_lines, "HEATING", begin=heatcount+1, end_string="*----------------", raise_error=False)

    return json_dict

def update_json_with_b18_infiltrations(b18_name, b18_lines, json_dict, k):
    """
    Given a b18 list-like file, this function will update the json dict with all infiltration defined in the file.

    Return:
        json_dict (dict): The json_dict udapted with all the infiltration defined in b18_lines.
    Args:
        b18_name (str): Name of the spacetype we are reading.
        b18_lines (list-like): a list-like object of a spacetype (as a TRNSYS building).
        json_dict (list-like): a nested dictionnaries where the spacetype data is to be stored.
        key (dict): A subset of the json key dictionnary containing keys for infiltration definition.

    """
    
    # Get line of Infiltrations zones and line of 1st Infiltrations
    fcount_min = utils._checkStr(b18_lines, "I n f i l t r a t i o n") + 2
    infcount = utils._checkStr(b18_lines, "INFILTRATION", begin=fcount_min, end_string="*----------------")
    
    # Initializing 
    list_infiltration = []

    # Loop to get all Infiltrations until none is found in Trnbuild Infiltrations definition area.
    while infcount != None:
        # Get Infiltrations name from 1st line
        line1 = utils._cleanString(b18_lines[infcount])
        infName = line1.split(" ")[1]
        
        # Get Infiltrations name from 1st line
        line2 = utils._cleanString(b18_lines[infcount+1])
        preline2 = line2.split("=")[1]

        infType, infVar = "CONSTANT", "0"
        if "INPUT" in preline2:
            infType = "INPUT"
            infVar = preline2.split("1*")[1]
        elif "SCHEDULE" in preline2:
            infType = "SCHEDULE"
            infVar = preline2.split("1*")[1]
        else:
            infType = "CONSTANT"
            infVar = preline2

        # Save Infiltrations 
        item_number = len(json_dict["Types"]["Infiltrations"].keys())
        key = k["Types"]["Infiltrations"]["0"]
        json_dict["Types"]["Infiltrations"][item_number][key["Name"]] = infName
        json_dict["Types"]["Infiltrations"][item_number][key["Source"]] = "From file: "+b18_name
        json_dict["Types"]["Infiltrations"][item_number][key["Description"]] = " "
        json_dict["Types"]["Infiltrations"][item_number][key["InfType"]] = infType
        json_dict["Types"]["Infiltrations"][item_number][key["InfRate"]] = infVar

        # Look for next Infiltrations
        infcount = utils._checkStr(b18_lines, "INFILTRATION", begin=infcount+1, end_string="*----------------", raise_error=False)
    # End while
    # ------------------------------------------------------------------------------------------------------------ 
    return json_dict

def update_json_with_b18_schedules(b18_name, b18_lines, json_dict, k):
    """
    Given a b18 list-like file, this function will update the json dict with all schedules defined in the file.

    Return:
        json_dict (dict): The json_dict udapted with all the schedules defined in b18_lines.
    Args:
        b18_name (str): Name of the spacetype we are reading.
        b18_lines (list-like): a list-like object of a spacetype (as a TRNSYS building).
        json_dict (list-like): a nested dictionnaries where the spacetype data is to be stored.
        key (dict): A subset of the json key dictionnary containing keys for schedules definition.
    """
    
    # Get line of schedules zones and line of 1st schedule
    fcount_min = utils._checkStr(b18_lines, "S c h e d u l e s") + 2
    schedcount = utils._checkStr(b18_lines, "SCHEDULE", begin=fcount_min, end_string="*----------------")
    
    # Initializing 
    list_schedule = []

    # Loop to get all schedules until none is found in Trnbuild schedule definition area.
    while schedcount != None:
        # Get schedule name from 1st line
        line1 = utils._cleanString(b18_lines[schedcount])
        schedName = line1.split()[1]

        # Get time values from 2nd line
        line2 = utils._cleanString(b18_lines[schedcount+1])
        preType, preTime = line2.split("=")
        listTime = preTime.split()

        if "DAYS" in preType:
            schedType = "DAY"
        else:
            if float(listTime[-1]) > 24:
                schedType = "ANNUAL"
            else:
                schedType = "HOUR"

        # Get values from 3rd line
        line3 = utils._cleanString(b18_lines[schedcount+2]) 
        preValues  = line3.split("=")[1]
        listValues = preValues.split()

        
        # check length errors 
        if len(listValues) != len(listTime):
            logger.info ("Error while reading schedule " + schedName + ". Make sure time ande values have the same length.")

        # Save schedule
        item_number = len(json_dict["Types"]["Schedules"].keys())
        key = k["Types"]["Schedules"]["0"]
        json_dict["Types"]["Schedules"][item_number][key["Name"]] = schedName
        json_dict["Types"]["Schedules"][item_number][key["Source"]] = "From file: "+b18_name
        json_dict["Types"]["Schedules"][item_number][key["Description"]] = " "
        json_dict["Types"]["Schedules"][item_number][key["SchedType"]] = schedType
        json_dict["Types"]["Schedules"][item_number][key["TimeList"]] = listTime
        json_dict["Types"]["Schedules"][item_number][key["ValueList"]] = listValues

        # Look for next schedule
        schedcount = utils._checkStr(b18_lines, "SCHEDULE", begin=schedcount+1, end_string="*----------------", raise_error=False)
    return json_dict

def update_json_with_b18_ventilations(b18_name, b18_lines, json_dict, k):
    """
    Given a b18 list-like file, this function will update the json dict with all ventilation defined in the file.

    Return:
        json_dict (dict): The json_dict udapted with all the ventilation defined in b18_lines.
    Args:
        b18_name (str): Name of the spacetype we are reading.
        b18_lines (list-like): a list-like object of a spacetype (as a TRNSYS building).
        json_dict (list-like): a nested dictionnaries where the spacetype data is to be stored.
        key (dict): A subset of the json key dictionnary containing keys for ventilation definition.
    """
    
    # Get line of ventilation zones and line of 1st ventilation
    fcount_min = utils._checkStr(b18_lines, "V e n t i l a t i o n") + 2
    ventcount = utils._checkStr(b18_lines, "VENTILATION", begin=fcount_min, end_string="*----------------")
    
    # Initializing 
    list_ventilation = []

    # Loop to get all ventilation until none is found in Trnbuild ventilation definition area.
    while ventcount != None:
        # Get ventilation name from 1st line
        line1 = utils._cleanString(b18_lines[ventcount])
        ventName = line1.split(" ")[1]

        # Loop for next lines
        nb_line = 1
        line = utils._cleanString(b18_lines[ventcount+nb_line])
        
        # ------------------------------------------------------------------------------------------------------------
        while ("=" in line):

            # Get label & value
            label, value = line.split("=")

            # Get ventTdb and ventTdbType from TEMPERATURE label
            ventTdb, ventTdbType = "OUTSIDE", "OUTSIDE"
            if "TEMPERATURE" in label:
                if value == "OUTSIDE":
                    ventTdb = "OUTSIDE"
                    ventTdbType = "OUTSIDE"
                if "INPUT" in value:
                    ventTdb = value.split("1*")[1]
                    ventTdbType = "INPUT"
                if "SCHEDULE" in value:
                    ventTdb = value.split("1*")[1]
                    ventTdbType = "SCHEDULE" 

            # Get ventMode, ventFlow & ventFlowType from 3rd line
            ventMode, ventFlow, ventFlowType = "AIRCHANGE", "1", "CONSTANT"
            if "AIRCHANGE" in label:
                ventMode = label
            if "AIRFLOW" in label:
                ventMode = label
            if "AIRFLOWSPEC" in label:
                ventMode = label
            if "VAIRFLOW" in label:
                ventMode = label
            if "VAIRFLOWSPEC" in label: 
                ventMode = label

            if ventMode == label:   
                if "INPUT" in value:
                    ventFlow = value.split("1*")[1]
                    ventFlowType = "INPUT"
                elif "SCHEDULE" in value:
                    ventFlow = value.split("1*")[1]
                    ventFlowType = "SCHEDULE"   
                else:
                    ventFlow = value
                    ventFlowType = "CONSTANT"          

            # Get ventHumidity & relorabs
            ventHumidity, ventHumidityType, relorabs = "OUTSIDE", "OUTSIDE", "abs"
            if "ABSMINHUM" in label: 
                relorabs = "Aabs"
            if "ABSMAXHUM" in label: 
                relorabs = "Aabs"
            if "RELMINHUM" in label: 
                relorabs = "Arel"
            if "RELMAXHUM" in label: 
                relorabs = "Arel"

            if relorabs == "Arel" or relorabs == "Aabs":
                relorabs = relorabs[1:]
                if "INPUT" in value:
                    ventHumidity = value.split("1*")[1]
                    ventHumidityType = "INPUT"
                elif "SCHEDULE" in value:
                    ventHumidity = value.split("1*")[1]
                    ventHumidityType = "SCHEDULE"   
                else:
                    ventHumidity = value
                    ventHumidityType = "CONSTANT"          

            # Get specfanpower
            specfanpower = "0"
            if "SPECFANPOWER" in label: 
                specfanpower = value

            senshr = "0"
            if "SENSHR" in label: 
                senshr = value

            calcqahu = "0"
            if "CALCQAHU" in label: 
                calcqahu = value

            # Read next line
            nb_line += 1
            line = utils._cleanString(b18_lines[ventcount+nb_line])
        # End while
        # ------------------------------------------------------------------------------------------------------------
        
        # Save ventilation 
        item_number = len(json_dict["Types"]["Ventilations"].keys())
        key = k["Types"]["Ventilations"]["0"]
        json_dict["Types"]["Ventilations"][item_number][key["Name"]] = ventName
        json_dict["Types"]["Ventilations"][item_number][key["Source"]] = "From file: "+b18_name
        json_dict["Types"]["Ventilations"][item_number][key["Description"]] = " "
        json_dict["Types"]["Ventilations"][item_number][key["Mode"]] = ventMode
        json_dict["Types"]["Ventilations"][item_number][key["Flow"]] = ventFlow
        json_dict["Types"]["Ventilations"][item_number][key["FlowType"]] = ventFlowType
        json_dict["Types"]["Ventilations"][item_number][key["Tdb"]] = ventTdb
        json_dict["Types"]["Ventilations"][item_number][key["TdbType"]] = ventTdbType
        json_dict["Types"]["Ventilations"][item_number][key["Humidity"]] = ventHumidity
        json_dict["Types"]["Ventilations"][item_number][key["HumidityType"]] = ventHumidityType
        json_dict["Types"]["Ventilations"][item_number][key["RelOrAbs"]] = relorabs
        json_dict["Types"]["Ventilations"][item_number][key["SpecFanPower"]] = specfanpower
        json_dict["Types"]["Ventilations"][item_number][key["SensHr"]] = senshr
        json_dict["Types"]["Ventilations"][item_number][key["Calcqahu"]] = calcqahu

        # Look for next ventilation
        ventcount = utils._checkStr(b18_lines, "VENTILATION", begin=ventcount+1, end_string="*----------------", raise_error=False)
    # End while
    # ------------------------------------------------------------------------------------------------------------ 
    return json_dict

# ================================================================================
# Writing ========================================================================
# ================================================================================

# ----- Write definition ---------------

def write_JSONDefCooling_ToB18(b18_lines, c, key):
    """
    Write a cooling definition in a b18_lines object representing a .b18 file.
    The function type indicate if *TdbConsigne* data is given as a constant, as an input in the file or as a schedule in the file.

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        c (dict): A subset of a JSON dict containing the cooling definition.
        key (dict): A subset of the json key dictionnary containing keys for cooling definition.
    """
   
   # Remove if gain already exist
    fcount = utils._checkStr(b18_lines, "C o o l i n g")
    utils._removeStr(b18_lines, " COOLING " + str(c[key["Name"]]) + "\n", begin=fcount ,end_string="Z o n e s", nb=2)

    # Get line
    fcount = utils._checkStr(b18_lines, "C o o l i n g")  + 1

    # Write cooling definition
    b18_lines.insert( fcount + 1, " COOLING " + str(c[key["Name"]]) + "\n")
    if c[key["Type"]] == "INPUT":
        b18_lines.insert( fcount + 2,
                        " ON=INPUT 1*" + str(c[key["TdbConsigne"]]) +
                        " : POWER=" + str(c[key["Power"]]) +
                        " : ABSHUMIDITY=" + str(c[key["Humidity"]]) +
                        " : ELPOWERFRAC=" + str(c[key["ElecPowerFrac"]]) +
                        " : AREA_RELATED_POWER=" + str(c[key["AreaRelPower"]]) +
                        "\n",)
    elif c[key["Type"]] == "SCHEDULE":
        b18_lines.insert( fcount + 2,
                        "ON=SCHEDULE 1*" + str(c[key["TdbConsigne"]]) +
                        " : POWER=" + str(c[key["Power"]]) +
                        " : ABSHUMIDITY=" + str(c[key["Humidity"]]) +
                        " : ELPOWERFRAC=" + str(c[key["ElecPowerFrac"]]) +
                        " : AREA_RELATED_POWER=" + str(c[key["AreaRelPower"]]) +
                        "\n",)
    else:
        utils._isStringToFloat(str(c[key["Name"]]), str(c[key["TdbConsigne"]]))
        b18_lines.insert( fcount + 2,
                        "ON=" + str(c[key["TdbConsigne"]]) +
                        " : POWER=" + str(c[key["Power"]]) +
                        " : ABSHUMIDITY=" + str(c[key["Humidity"]]) +
                        " : ELPOWERFRAC=" + str(c[key["ElecPowerFrac"]]) +
                        " : AREA_RELATED_POWER=" + str(c[key["AreaRelPower"]]) +
                        "\n",)

def write_JSONDefGain_ToB18(b18_lines, g, key):
    """
    Write a gain definition in a b18_lines object representing a .b18 file.
    The gains category are the ones recognized by TRNBuild (people, light, equipment, thermal bridges and miscellanious).

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        g (dict): A subset of a JSON dict containing the gain definition.
        key (dict): A subset of the json key dictionnary containing keys for gain definition.
    """
    # Remove if gain already exist
    utils._removeStr(b18_lines, "GAIN " + g[key["Name"]] +"\n", end_string="Z o n e s", nb=2)

    # Get line
    fcount = utils._checkStr(b18_lines, "G a i n s") + 1

    # Get Convective, radiative and humidity sentence
    CONVECTIVE_GAIN = str(g[key["Convective"]])
    RADIATIVE_GAIN = str(g[key["Radiative"]])
    HUMIDITY_GAIN = str(g[key["Humidity"]])

    if (g[key["GainInput"]] != ""):
        CONVECTIVE_GAIN = "INPUT "+str(g[key["Convective"]])+" * "+str(g[key["GainInput"]])
        RADIATIVE_GAIN = "INPUT " +str(g[key["Radiative"]]) +" * "+str(g[key["GainInput"]])
        HUMIDITY_GAIN = "INPUT "  +str(g[key["Humidity"]])  +" * "+str(g[key["GainInput"]])
    
    if (g[key["GainSchedule"]] != ""):
        CONVECTIVE_GAIN = "INPUT "+str(g[key["Convective"]])+" * "+str(g[key["GainSchedule"]])
        RADIATIVE_GAIN  = "INPUT "+str(g[key["Radiative"]]) +" * "+str(g[key["GainSchedule"]])
        HUMIDITY_GAIN   = "INPUT "+str(g[key["Humidity"]])  +" * "+str(g[key["GainSchedule"]])
        
        if (g[key["GainInput"]] != ""):
            logger.warning("Duplicate definition for gain "+ g[key["Name"]]+". Keeping FlowInput definition.")

    # Write gain definition
    b18_lines.insert( fcount + 1, " GAIN " + g[key["Name"]] + "\n")
    b18_lines.insert( fcount + 2,
                          " CONVECTIVE=" + CONVECTIVE_GAIN
                        + " : RADIATIVE=" + RADIATIVE_GAIN
                        + " : HUMIDITY=" + HUMIDITY_GAIN
                        + " : ELPOWERFRAC=" + str(g[key["ElecPowerFrac"]])
                        + " : " + g[key["GainType"]]
                        + " : CATEGORY=" + str(g[key["GainCategory"]]) + "\n",)
    
def write_JSONDefHeating_ToB18(b18_lines, h, key):
    """
    Write a heating definition in a b18_lines object representing a .b18 file.
    The function type indicate if *TdbConsigne* data is given as a constant, as an input in the file or as a schedule in the file.

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        h (dict): A subset of a JSON dict containing the heating definition.
        key (dict): A subset of the json key dictionnary containing keys for heating definition.
    """
    # Remove if gain already exist
    utils._removeStr(b18_lines, " HEATING " + str(h[key["Name"]]) + "\n", end_string="Z o n e s", nb=2)

    # Get line
    fcount = utils._checkStr(b18_lines, "H e a t i n g")  + 1

    # Write gain definition
    b18_lines.insert( fcount + 1, " HEATING " + str(h[key["Name"]]) + "\n")
    if str(h[key["Type"]]) == "INPUT":
        b18_lines.insert( fcount + 2,
                        " ON=INPUT 1*" + str(h[key["TdbConsigne"]]) +
                        " : POWER=" + str(h[key["Power"]]) +
                        " : ABSHUMIDITY=" + str(h[key["Humidity"]]) +
                        " : RRAD=" + str(h[key["RadFrac"]]) + 
                        " : ELPOWERFRAC=" + str(h[key["ElecPowerFrac"]]) +
                        " : AREA_RELATED_POWER=" + str(h[key["AreaRelPower"]]) +
                        "\n",)
    elif str(h[key["Type"]]) == "SCHEDULE":
        b18_lines.insert( fcount + 2,
                        "ON=SCHEDULE 1*" + str(h[key["TdbConsigne"]]) +
                        " : POWER=" + str(h[key["Power"]]) +
                        " : ABSHUMIDITY=" + str(h[key["Humidity"]]) +
                        " : RRAD=" + str(h[key["RadFrac"]]) + 
                        " : ELPOWERFRAC=" + str(h[key["ElecPowerFrac"]]) +
                        " : AREA_RELATED_POWER=" + str(h[key["AreaRelPower"]]) +
                        "\n",)
    else: # Type == constant
        utils._isStringToFloat(str(h[key["Name"]]), str(h[key["TdbConsigne"]]))
        b18_lines.insert( fcount + 2,
                        "ON=" + str(h[key["TdbConsigne"]]) +
                        " : POWER=" + str(h[key["Power"]]) +
                        " : ABSHUMIDITY=" + str(h[key["Humidity"]]) +
                        " : RRAD=" + str(h[key["RadFrac"]]) + 
                        " : ELPOWERFRAC=" + str(h[key["ElecPowerFrac"]]) +
                        " : AREA_RELATED_POWER=" + str(h[key["AreaRelPower"]]) +
                        "\n",)

def write_JSONDefInfiltration_ToB18(b18_lines, f, key):
    """
    Function to write the definition of an infiltration in a .b18 file.
    The *InfType* indicate if *InfRate* data is given as a constant, as an input in the file or as a schedule in the file.

    Arg:
        b18_lines :: list-liked containing the lines of the .b18
        f (dict): A subset of a JSON dict containing the infiltration definition.
        key (dict): A subset of the json key dictionnary containing keys for infiltration definition.
    """
    # Get line number where to write
    infiltNum = utils._checkStr(b18_lines, "I n f i l t r a t i o n") + 1

    # Remove infiltration and airchange if already exist:
    utils._removeStr(b18_lines, "INFILTRATION " + str(f[key["Name"]]) + "\n", nb=2)

    # Write in infiltration section

    b18_lines.insert(infiltNum + 1, "INFILTRATION " + str(f[key["Name"]]) + "\n")

    if str(f[key["InfType"]]) == "INPUT":
        b18_lines.insert(infiltNum + 2, " AIRCHANGE=INPUT 1*" + str(f[key["InfRate"]]) + "\n")
    if str(f[key["InfType"]]) == "SCHEDULE":
        b18_lines.insert(infiltNum + 2, " AIRCHANGE=SCHEDULE 1*" + str(f[key["InfRate"]]) + "\n")
    else: #InfType="CONSTANT"
        utils._isStringToFloat(str(f[key["Name"]]), str(f[key["InfRate"]]))
        b18_lines.insert(infiltNum + 2, " AIRCHANGE=" + str(f[key["InfRate"]]) + "\n")

def write_JSONDefVentilation_ToB18(b18_lines, v, key):
    """
    Write a ventilation definition in a b18_lines object representing a .b18 file.
    The function type indicate if *ventAirflow* data is given as a constant, as an input in the file or as a schedule in the file.
    The function mode indicate the ventilation method to be used (so ventAirflow unit is linked to the Mode parameter).
    
    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        v (dict): A subset of a JSON dict containing the ventilation definition.
        key (dict): A subset of the json key dictionnary containing keys for ventilation definition.
    """

    # Remove 8 lines if ventilation definition already exist
    utils._removeStr(b18_lines, "VENTILATION " + str(v[key["Name"]]) + "\n" ,end_string="Z o n e s", nb=8)

    # Get line
    fcount = utils._checkStr(b18_lines, "V e n t i l a t i o n")  + 1
    # ------------------------------
    # Write ventilation definition :
    b18_lines.insert( fcount + 1, "VENTILATION " + str(v[key["Name"]]) + "\n")
    
    # Write temperature
    if str(v[key["TdbType"]]) == "OUTSIDE":
        b18_lines.insert( fcount + 2, " TEMPERATURE=OUTSIDE" +  "\n")
    else:
        b18_lines.insert( fcount + 2, " TEMPERATURE=" + str(v[key["TdbType"]]) + " 1*"+ str(v[key["Tdb"]]) +  "\n")

    # Write ventilation flow as constant
    VENTILATION_DEF = str(v[key["Mode"]]) + "=" + str(v[key["FlowValue"]])  +"\n"

    # Update if input entry detected
    if (str(v[key["FlowInput"]]) != ""):
        utils._isStringToFloat(str(v[key["Name"]]), str(v[key["FlowValue"]]) )
        VENTILATION_DEF = str(v[key["Mode"]])+ "=INPUT " + str(v[key["FlowValue"]]) + " * " + str(v[key["FlowInput"]])  +"\n"

    # Update if scheudle entry detected
    if (str(v[key["FlowSchedule"]]) != ""):
        VENTILATION_DEF = str(v[key["Mode"]])+ "=SCHEDULE " + str(v[key["FlowValue"]]) + " * " + str(v[key["FlowSchedule"]])  +"\n"
    
        if (str(v[key["FlowInput"]]) != ""):
            logger.warning("Duplicate definition for ventilation "+ v[key["Name"]]+". Keeping FlowInput definition.")

   # Write other
    b18_lines.insert( fcount + 3, VENTILATION_DEF)
    b18_lines.insert( fcount + 4, " SPECFANPOWER=" + str(v[key["SpecFanPower"]]) +"\n")
    b18_lines.insert( fcount + 5, " SENSHR=" + str(v[key["SensHr"]]) +"\n")

    # Write ventilation humidity 
    if v[key["HumidityType"]] == "OUTSIDE":
        b18_lines.insert( fcount + 6, " " + str(v[key["RelOrAbs"]]).upper() + "MINHUM=OUTSIDE" +"\n")
        b18_lines.insert( fcount + 7, " " + str(v[key["RelOrAbs"]]).upper() + "MAXHUM=OUTSIDE" +"\n")
    else:
        b18_lines.insert( fcount + 6, " " + str(v[key["RelOrAbs"]]).upper() + "MINHUM=" + str(v[key["HumidityType"]]) + "1*" + str(v[key["Humidity"]]) +"\n")
        b18_lines.insert( fcount + 7, " " + str(v[key["RelOrAbs"]]).upper() + "MAXHUM=" + str(v[key["HumidityType"]]) + "1*" + str(v[key["Humidity"]]) +"\n")

    # Write other
    b18_lines.insert( fcount + 8, " CALCQAHU=" + str(v[key["Calcqahu"]]) + "\n")

# ----- Write in zones -----------------

def write_JSONZoneCooling_ToB18(b18_lines, zones, c, key):
    """
    This function will write the cooling *coolName* in all TRNbuild zones given in the zones list argument. 

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        zones (list of string): List of zone where the cooling is to be used.
        c (dict): A subset of a JSON dict containing the cooling definition.
        key (dict): A subset of the json key dictionnary containing keys for cooling definition.    """

    # Write cooling in all zones
    for zone in zones:
        # Get Zone line number
        f_count = utils._checkStr(b18_lines, "Z o n e  " + zone + " ")
        # Get zone regime line number
        regimeNum = utils._checkStr(b18_lines, "REGIME", f_count) + 1
        # Remove Cooling if found
        utils._removeStr(b18_lines, "COOLING", begin=regimeNum, end_string="Z o n e ")
        # Write new Cooling 
        b18_lines.insert(regimeNum, " COOLING = " + c[key["Name"]] + "\n",)

def write_JSONZoneGain_ToB18(b18_lines, zones, g, key, scale1="1", scale2="1", scale1Type="CONSTANT", scale2Type="CONSTANT"):
    """
    This function will write the gain in all TRnbuild zones given in the zones list argument. 
    The scale parameters are used to add multiplier (such as occupation or use schedules...).

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        zones (list of string): List of zone where the gain is to be used.
        g (dict): A subset of a JSON dict containing the gains definition.
        key (dict): A subset of the json key dictionnary containing keys for gains definition.
        scale1 (string): String used as a multiplicator for the gain.
        scale2 (string): String used as a multiplicator for the gain.
        scale1Type (string): Default is "CONSTANT" : scale1 must be an existing schedule name. scale1Type can also be "CONSTANT" 
                        (then scale1 must be float-convertible) or "INPUT" (then scale1 must be an existing input name).
        scale2Type (string): Default is "CONSTANT" : scale2 must be an existing schedule name. scale2Type can also be "CONSTANT" 
                        (then scale2 must be float-convertible) or "INPUT" (then scale2 must be an existing input name).
    """
    
    # Write gain in all zones
    for zone in zones:
        # Get Zone line number
        f_count = utils._checkStr(b18_lines, "Z o n e  " + zone  + " ")
        # Get zone regime line number
        regimeNum = utils._checkStr(b18_lines, "REGIME", f_count) + 1
        # Remove Gains if found
        utils._removeStr(b18_lines, "GAIN= " + g[key["Name"]], begin=regimeNum, end_string="Z o n e ")
        
        if g[key["GainType"]] == "ABSOLUTE":
            frac_ref_area = "-1"
        elif g[key["GainType"]] == "AREA_RELATED":
            frac_ref_area = "1"
        else:
            frac_ref_area = "1"
            logger.info("ERROR Gain" + g[key["Name"]] + "have a unknown type")
        
        # Write new Gain 
        if scale1Type == "CONSTANT" and scale2Type == "CONSTANT":
            b18_lines.insert(
                            regimeNum,
                            " GAIN= " + g[key["Name"]] +
                            " : SCALE= "+ scale1 +
                            " : GEOPOS=0" +
                            " : SCALE2= " + scale2 +
                            " : FRAC_REFAREA="+frac_ref_area + "\n",)

        elif scale1Type == "CONSTANT":
            b18_lines.insert(
                            regimeNum,
                            " GAIN= " + g[key["Name"]] +
                            " : SCALE= "+  scale1 +
                            " : GEOPOS=0" +
                            " : SCALE2= " + scale2Type + " 1*"+ scale2 +
                            " : FRAC_REFAREA="+frac_ref_area + "\n",)

        elif scale2Type == "CONSTANT":
            b18_lines.insert(
                            regimeNum,
                            " GAIN= " + g[key["Name"]] +
                            " : SCALE= "+ scale1Type + " 1*" +  scale1 +
                            " : GEOPOS=0" +
                            " : SCALE2= " + scale2 +
                            " : FRAC_REFAREA="+frac_ref_area + "\n",)

        else: 
            b18_lines.insert(
                            regimeNum,
                            " GAIN= " + g[key["Name"]] +
                            " : SCALE= "+ scale1Type + " 1*" +  scale1 +
                            " : GEOPOS=0" +
                            " : SCALE2= " + scale2Type + " 1*"+ scale2 +
                            " : FRAC_REFAREA="+frac_ref_area + "\n",)

def write_JSONZoneHeating_ToB18(b18_lines, zones, h, key):
    """
    This function will write the heating *heatName* in all TRNbuild zones given in the zones list argument. 

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        zones (list of string): List of zone where the heating is to be used.
        h (dict): A subset of a JSON dict containing the heating definition.
        key (dict): A subset of the json key dictionnary containing keys for heating definition.    
    """

    # Write heating in all zones
    for zone in zones:
        # Get Zone line number
        f_count = utils._checkStr(b18_lines, "Z o n e  " + zone + " ")
        # Get zone regime line number
        regimeNum = utils._checkStr(b18_lines, "REGIME", f_count) + 1

        # remove heating lines
        utils._removeStr(b18_lines, "HEATING", begin=regimeNum, end_string="Z o n e ")
 
        # Write new Heating 
        b18_lines.insert(regimeNum, " HEATING = " + h[key["Name"]] + "\n",)

def write_JSONZoneInfiltration_ToB18(b18_lines, zones, f, key):
    """
    This function will write the infiltration *infName* in all TRNbuild zones given in the zones list argument. 

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        zones (list of string): List of zone where the infiltration is to be used.
        f (dict): A subset of a JSON dict containing the infiltration definition.
        key (dict): A subset of the json key dictionnary containing keys for infiltration definition. 
    """

    # Write infiltration in all zones
    for zone in zones:
        # Get Zone line number
        f_count = utils._checkStr(b18_lines, "Z o n e  " + zone  + " ")
        # Get zone regime line number
        regimeNum = utils._checkStr(b18_lines, "REGIME", f_count) + 1
        # Remove infiltration if found
        utils._removeStr(b18_lines, "INFILTRATION", begin=regimeNum, end_string="Z o n e ")
        # Write new infiltration 
        b18_lines.insert(regimeNum, " INFILTRATION = " + f[key["Name"]] + "\n",)

def write_JSONZoneVentilation_ToB18(b18_lines, zones, v, key):
    """
    This function will write the ventilation *ventName* in all TRNbuild zones given in the zones list argument. 

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        zones (list of string): List of zone where the ventilation is to be used.
        v (dict): A subset of a JSON dict containing the ventilation definition.
        key (dict): A subset of the json key dictionnary containing keys for ventilation definition.
    """

    # Write ventilation in all zones
    for zone in zones:
        # Get Zone line number
        f_count = utils._checkStr(b18_lines, "Z o n e  " + zone  + " ")
        # Get zone regime line number
        regimeNum = utils._checkStr(b18_lines, "REGIME", f_count) + 1
        # Remove ventilation if found
        utils._removeStr(b18_lines, "VENTILATION", begin=regimeNum, end_string="Z o n e ")
        # Write new ventilation 
        b18_lines.insert(regimeNum, " VENTILATION = " + v[key["Name"]] + "\n",)

# ----- Advanced writing functions ------

def write_input_ToB18(b18_lines, inputName):
    """
    Write a new input in a new line right after last input line of a B18 file.

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        inputName (string): A input name.
    """
    # Initializing
    list_inputs = []
    
     # Go to input
    fcount = utils._checkStr(b18_lines, "I n p u t s") + 2
    
    # Initializing :
    line = b18_lines[fcount]
    cleanline =utils._cleanString(line)
    clean_list = cleanline.split(" ")[1:]
    step, list_inputs = 0, []
    
    # For each new line detected :
    while ";" in clean_list[-1]:
        # Save list of name except last item (always ";" except for last zone)
        list_inputs += clean_list[:-1]
    
        # Get next line as a list of zone
        step += 1
        new_line =utils._cleanString(b18_lines[fcount+step])
        clean_list = new_line.split(" ")

    # Save last zone name without \n part of the string
    list_inputs += clean_list[:]
    
    if not inputName in list_inputs:

        # If only one line of input, write at the end of the line
        if not ";" in cleanline:
            b18_lines.pop(fcount)
            b18_lines.insert(fcount, cleanline+" ;\n")
            b18_lines.insert(fcount+1, inputName + "\n")

        # If multiple lines of input, go to last line, then write at end of line
        else:
            # Go to last line
            while ";" in cleanline: 
                fcount+=1
                cleanline = utils._cleanString(b18_lines[fcount])
            # Add input to line
            b18_lines.pop(fcount)
            b18_lines.insert(fcount, cleanline+" ;\n")
            b18_lines.insert(fcount+1, inputName + "\n")
            
def write_schedule_ToB18(b18_lines, s, key, c):
    """
    This function add a schedule to a B18 file.
    If the schedule is defined as an input, then it is added to the file input.
    If the schedule is to be defined locally, then the schedule is written in Schedules definition
    The function allows the definition of schedules of type "HOUR", "DAY", "ANNUAL".

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        s (dict): A subset of a JSON dict containing the schedules definition.
        key (dict): A subset of the json key dictionnary containing keys for schedules definition.
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    # Get line number where to write
    infiltNum = utils._checkStr(b18_lines, "S c h e d u l e s") + 1

    # Remove schedule if already exist:
    utils._removeStr(b18_lines, "SCHEDULE " + s[key["Name"]] + "\n", begin=infiltNum, nb=3)

    # Write schedule name :
    infiltNum = utils._checkStr(b18_lines, "S c h e d u l e s") + 1
    b18_lines.insert(infiltNum + 1, "SCHEDULE " + s[key["Name"]] + "\n")
    
    # Get list of time and values
    if type(s[key["ValueList"]]) != list:
        if s[key["ValueList"]].startswith("["):
            s[key["ValueList"]] = s[key["ValueList"]][1:]
        if s[key["ValueList"]].endswith("]"):
            s[key["ValueList"]] = s[key["ValueList"]][:-1]
        s[key["ValueList"]] = s[key["ValueList"]].split(" ")

    if type(s[key["TimeList"]]) != list:
        if s[key["TimeList"]].startswith("["):
            s[key["TimeList"]]= s[key["TimeList"]][1:]
        if s[key["TimeList"]].endswith("]"):
            s[key["TimeList"]] = s[key["TimeList"]][:-1]
        s[key["TimeList"]] = s[key["TimeList"]].split(" ")

    # Write schedule DAY =============================================================
    if s[key["SchedType"]] == "DAY":
        b18_lines.insert(infiltNum + 2, "DAYS=1 2 3 4 5 6 7 \n")

        if len(s[key["ValueList"]]) == 7:
            l = s[key["ValueList"]]
            b18_lines.insert(infiltNum + 3, "HOURLY=" +l[0]+" "+l[1]+" "+l[2]+" "+l[3]+" "+l[4]+" "+l[5]+" "+l[6]+ "\n")
        else:
            message ="For schedule " + s[key["Name"]] + " of type DAYS, incorrect number of values given (should be 7)"
            logger.warning(message)
            logger.warning(s[key["ValueList"]])
            logger.warning(s[key["TimeList"]])

    # Write schedule HOUR & ANNUAL ===================================================
    if s[key["SchedType"]] == "HOUR" or s[key["SchedType"]] == "ANNUAL":
        
        # Check length of lists
        if len(s[key["ValueList"]]) != len(s[key["TimeList"]]):
            message ="For schedule " + s[key["Name"]] + " of type "+s[key["SchedType"]]+ ", incorrect number of values given (should be same as listTime)"
            logger.warning(message)
            logger.warning(s[key["ValueList"]])
            logger.warning(s[key["TimeList"]])

        else:
            # Create string of all values 
            hours = ""
            values = ""
            for index in range(0,len(s[key["TimeList"]])):
                hours += str(s[key["TimeList"]][index]) + " "
                values += str(s[key["ValueList"]][index]) + " "
            
            # Write schedule definition
            b18_lines.insert(infiltNum + 2, "HOURS=" + hours + "\n")
            b18_lines.insert(infiltNum + 3, "VALUES=" + values + "\n")

def write_outputs_ToB18(b18_lines, c):
    """
    A simple function that remove every single outputs for every airnodes in a B18 file (as list-like object of lines).
    Then, for each airnode, the function will add every output defined in the OutputDict defined in the parameters in c ClassConfiguration object.

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    # Go to input first line of definition
    fcount = utils._checkStr(b18_lines, "O u t p u t s") + 2
    cleanline = utils._cleanString(b18_lines[fcount])

    # Pop output
    while "END" not in cleanline:
        b18_lines.pop(fcount)
        cleanline = b18_lines[fcount]
    
    b18_lines.insert( fcount, "*---------------------------------------------------------------\n")
    b18_lines.insert( fcount, "* E n d \n")
    b18_lines.insert( fcount, "*---------------------------------------------------------------\n")

    # Add outputs
    listzone = _read_listZones_from_b18(b18_lines)
    for zone in listzone:
        for output_id in c.DictOutput.keys():
            output_name = c.DictOutput[output_id]
            b18_lines.insert(fcount, "       =   "+output_id+" : "+output_name+"\n")
        b18_lines.insert(fcount, "NTYPE  =   1 : Tair - node temperature\n")
        b18_lines.insert(fcount, "AIRNODES = "+zone+"\n")
    b18_lines.insert(fcount, "TRANSFER : TIMEBASE=1.000\n")
    b18_lines.insert(fcount, "OUTPUTS\n") 

def write_furnitures_ToB18(b18_lines, c):
    """
    This function change the CAPACITANCE parameter of each thermal zone to account for room furnitures.
    We choose to have a capacitance ten times higher than what is proposed for each thermal zone to represent the furniture.

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    fcount = 0
     # Get line of zones list of names
    while fcount != None:
        fcount = utils._checkStr(b18_lines, "CAPACITANCE=", begin=fcount, raise_error=False) 

        if fcount != None:
            # Get line (without first string "ZONES")
            line = b18_lines[fcount]
            value = line.split(":")[0].split("=")[1]
            new_value = str(float(value) * 10)
            new_line =  "CAPACITANCE= " + new_value
            for item in line.split(":")[1:]:
                new_line = new_line + ":" + item

            b18_lines.pop(fcount)
            b18_lines.insert(fcount, new_line)

            fcount+= 1

def write_surfaceComposition_FromTemplate_ToB18(b18_lines, c):
    """
    This function basically copy&paste a template surface composition in the B18_lines given as an entry.
    The template is taken from ClassConfiguration attribute `c.path_TemplateB18_ForSurfaceComposition`.
    Surface composition of the B18 lines where to paste will be overwritten.

    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    # Get template ===================================================================================
    with open(c.path_TemplateB18_ForSurfaceComposition, "r", encoding="iso-8859-1") as b18_file:
                b18_lines_template = b18_file.readlines()


    # LAYERS =========================================================================================
    fcount_start = utils._checkStr(b18_lines, "L a y e r s", raise_error=False) +2 
    fcount_end   = utils._checkStr(b18_lines, "-----------", begin=fcount_start, raise_error=False)    
    fcount_start_template = utils._checkStr(b18_lines_template, "L a y e r s", raise_error=False) +2 
    fcount_end_template   = utils._checkStr(b18_lines_template, "-----------", begin=fcount_start_template, raise_error=False)

    utils._removeStr(b18_lines, "LAYER", begin=fcount_start, nb=fcount_end-fcount_start)

    for nb_line in range(0, fcount_end_template - fcount_start_template):
        new_line = b18_lines_template[fcount_start_template + nb_line]
        b18_lines.insert(fcount_start, new_line)
        fcount_start += 1
    
    # CONSTRUCTION ===================================================================================
    fcount_start = utils._checkStr(b18_lines, "C O N S T R U C T I O N", raise_error=False) +2 
    fcount_end   = utils._checkStr(b18_lines, "-----------", begin=fcount_start, raise_error=False)    
    fcount_start_template = utils._checkStr(b18_lines_template, "C O N S T R U C T I O N", raise_error=False) +2 
    fcount_end_template   = utils._checkStr(b18_lines_template, "-----------", begin=fcount_start_template, raise_error=False)

    utils._removeStr(b18_lines, "CONSTRUCTION", begin=fcount_start, nb=fcount_end-fcount_start)

    for nb_line in range(0, fcount_end_template - fcount_start_template):
        new_line = b18_lines_template[fcount_start_template + nb_line]
        b18_lines.insert(fcount_start, new_line)
        fcount_start += 1
    # WINDOW =========================================================================================
    fcount_start = utils._checkStr(b18_lines, "W i n d o w s", raise_error=False) +2 
    fcount_end   = utils._checkStr(b18_lines, "-----------", begin=fcount_start, raise_error=False)    
    fcount_start_template = utils._checkStr(b18_lines_template, "W i n d o w s", raise_error=False) +2 
    fcount_end_template   = utils._checkStr(b18_lines_template, "-----------", begin=fcount_start_template, raise_error=False)

    utils._removeStr(b18_lines, "WINDOW", begin=fcount_start, nb=fcount_end-fcount_start)

    for nb_line in range(0, fcount_end_template - fcount_start_template):
        new_line = b18_lines_template[fcount_start_template + nb_line]
        b18_lines.insert(fcount_start, new_line)
        fcount_start += 1

    # WINDOW EXTENSION ===============================================================================
    fcount_start = utils._checkStr(b18_lines, "_EXTENSION_WINPOOL_START_", raise_error=False)
    fcount_end   = utils._checkStr(b18_lines, "_EXTENSION_WINPOOL_END_", begin=fcount_start, raise_error=False)    
    fcount_start_template = utils._checkStr(b18_lines_template, "_EXTENSION_WINPOOL_START_", raise_error=False)
    fcount_end_template   = utils._checkStr(b18_lines_template, "_EXTENSION_WINPOOL_END_", begin=fcount_start_template, raise_error=False)

    utils._removeStr(b18_lines, "_EXTENSION_WINPOOL_START_", begin=fcount_start, nb=fcount_end-fcount_start)

    for nb_line in range(0, fcount_end_template - fcount_start_template):
        new_line = b18_lines_template[fcount_start_template + nb_line]
        b18_lines.insert(fcount_start, new_line)
        fcount_start += 1

# ------ Zone's spacetype writing function ------

def write_zone_spacetype(b18_lines, zone, c):
    """
    This function will write all gains, coolings, heatings, infiltrations, ventilations of a spacetype in a set of thermal zones.
    This thermal zone set is obtain from zone-spacetype attribution results stored in JSON files.
    
    Args:
        b18_lines (list-like): a list-like object of a .b18 file.
        zone (string): Zone name.
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    k = c.keys
    spacetype = zone["Spacetype"]

    # Try schedule writing ------------------------
    for nb in spacetype["Schedules"]:
        key = k["Types"]["Schedules"]["0"]
        zone_schedule = spacetype["Schedules"][str(nb)]
        
        if "INPUT" in zone_schedule[key["SchedType"]]:
            write_input_ToB18(b18_lines=b18_lines, inputName=c.targetkey_INPUT + zone_schedule[key["Name"]])
        if not "INPUT" in zone_schedule[key["SchedType"]]:
            write_schedule_ToB18(b18_lines=b18_lines, s=zone_schedule, key=key, c=c)
    # Try gains writing ---------------------------
    for nb in spacetype["Gains"]:
        
        # Get  zone gain object from spacetype
        zone_gain = spacetype["Gains"][str(nb)]
        key = k["Types"]["Gains"]["0"]

        # Write gains to B18
        write_JSONDefGain_ToB18(b18_lines, zone_gain, key)
        write_JSONZoneGain_ToB18(b18_lines, [zone["Name"]], zone_gain, key)
 
    
    # Try heating writing -------------------------
    for nb in spacetype["Heatings"]:
        
        # Get  zone heating object from spacetype
        zone_heating = spacetype["Heatings"][str(nb)]
        key = k["Types"]["Heatings"]["0"]
        
        # Write heating to B18
        write_JSONDefHeating_ToB18(b18_lines, zone_heating, key)
        write_JSONZoneHeating_ToB18(b18_lines, [zone["Name"]], zone_heating, key)

    # Try cooling writing -------------------------
    for nb in spacetype["Coolings"]:
        
        # Get  zone cooling object from spacetype
        zone_cooling = spacetype["Coolings"][str(nb)]
        key = k["Types"]["Coolings"]["0"]
        
        # Write cooling to B18
        write_JSONDefCooling_ToB18(b18_lines, zone_cooling, key)
        write_JSONZoneCooling_ToB18(b18_lines, [zone["Name"]], zone_cooling, key)

    # Try ventilation writing ---------------------
    for nb in spacetype["Ventilations"]:
        
        # Get zone ventilation object from spacetype
        zone_ventilation = spacetype["Ventilations"][str(nb)]
        key = k["Types"]["Ventilations"]["0"]

        # Write ventilation to B18
        write_JSONDefVentilation_ToB18(b18_lines, zone_ventilation, key)
        write_JSONZoneVentilation_ToB18(b18_lines, [zone["Name"]], zone_ventilation, key)

    # Try infiltration writing --------------------
    for nb in spacetype["Infiltrations"]:
        
        # Get zone infiltration object from spacetype
        zone_infiltration = spacetype["Infiltrations"][str(nb)]
        key = k["Types"]["Infiltrations"]["0"]

        # Write infiltration to B18
        write_JSONDefInfiltration_ToB18(b18_lines, zone_infiltration, key)
        write_JSONZoneInfiltration_ToB18(b18_lines, [zone["Name"]], zone_infiltration, key)
  
    return b18_lines

# ------ Main writing function ------

def convert_FromJSON_ToB18(c):
    """
    Main function for writing a set of template spacetype on a set of B18 building input files (i.e. structurals archetypes).
    It gets the different files and call writeSpacetypeJSON_InB18() to write each spacetype in corresponding subset of zones in every B18 file.

    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    logger.info("Starting conversion of JSON file to B18 deck")

    # --------------------------------------
    # READ SPACETYPES FROM DIR -------------
    #---------------------------------------
    # Get list of spacetype files name in directory
    ListOf_SpaceType_Filenames = next(os.walk(c.path_SpacetypeJSON_updated), (None, None, []))[2]  # [] if no file
    ListOf_SpaceType_Dict = []

    # LOOP for each asserted file :
    for file in ListOf_SpaceType_Filenames:

        if file.endswith(".json") or file.endswith(".JSON"):
            # Read current spacetype
            with open(c.path_SpacetypeJSON_updated + file) as file:
                spacetype_dict = json.load(file)

            # Store current spacetype in ListOf_SpaceType_Dict
            ListOf_SpaceType_Dict.append(spacetype_dict)

    # ----------------------------------------------------------
    # WRITE SPACETYPE IN B18 -----------------------------------
    #-----------------------------------------------------------

    # LOOP for each of the asserted building files (.b18) ---
    for file in c.models:
        logger.info("> Starting to convert " + file + "---------")

        # OPEN B18 FILE 
        with open(c.path_InputB18 + file + ".b18", "r", encoding="iso-8859-1") as b18_file:
            b18_lines = b18_file.readlines()

        # OPEN ZONE-SPACETYPE ATTRIBUTION 
        with open(c.path_AttributionFile + file + ".json") as json_file:
            attributionFile = json.load(json_file)

        # WRITE OUTPUTS
        write_outputs_ToB18(b18_lines=b18_lines, c=c)    

        # WRITE FURNITURES
        write_furnitures_ToB18(b18_lines=b18_lines, c=c)
        write_surfaceComposition_FromTemplate_ToB18(b18_lines=b18_lines, c=c)
        
        # WRITE EACH SPACETYPES 
        for zone in attributionFile.values():
            write_zone_spacetype(b18_lines=b18_lines, zone=zone, c=c)

        # SAVING B18 FILES ---------------------
        logger.info("> Saving b18 in " + c.path_OutputSIM)
        with open(c.DictSIMpath[file]+file + ".b18", "w", encoding="iso-8859-1") as converted_file:
            for line in b18_lines:
                converted_file.writelines(str(line))

# ================================================================================
# ================================================================================
# ================================================================================
