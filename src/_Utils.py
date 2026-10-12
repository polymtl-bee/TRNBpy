# local
import _TranslateToB18 as reader
from _Logging import logger 
# packages
import re
import os
import json
import pandas as pd
from pandas import read_csv

# ----- B18 utils functions -----------

def _cleanString(string):
    """
    Simple function to strip a string from empty space at the start an end. Also remove return to line character.

    Args:
        string (str): The string to clean.

    Return: 
        string (str): The string cleaned.
    """

    # Removing retunr to line
    if string.endswith("\n"):
        string = string[:-1]

    # Removing last space
    if string.endswith(" "):
        string = string[:-1]

    # Removing startspace
    if string.startswith(" "):
        string = string[1:]

    return string

def _checkStr(datafile, string, begin=0, end_string="ThisWillNeverAppearAsAStringInAnyFile", raise_error=True):
    """
    Find the first occurrence of a string and return its line number
    If the string is not found, raise error. If raise_error is false, then just return "None". 

    Args:
        datafile (list-like): a list-like object
        string (str): the string to find in the txt file
        begin (int): Number of lines to skip before looking for the string. Default 0.
        end_string (str): String that represent the last line to read while looking for the string. If a line contains end_line_string, then it stop. Default end of datafile.
        raise_error (Bool): If True, will raise error if string not found. If False, will return "None" if string not found. Default is True.
    
    Returns: the list index containing the string. None if not found.

    """

    value = []
    count = 0
    for line in datafile:
        if count < begin:
            count += 1
            continue
    
        if string in str(line):
            return count
            break

        # Check if limit is passed
        if end_string in str(line):
            if raise_error:
                logger.warning("MatchError : the string " + string + " was not found in given interval.")
                return None
            else:
                return None
            break
        
        # Increase line count
        count += 1

    if raise_error:
        logger.warning("MatchError : the string " + string + " was not found in given interval.")
        return None
    else:
        return None

def _isStringToFloat(name, string):
    """
    Check if a string is convertible to a float. Replace "," by "." if needed. Raise an error if not convertible.

    Args:
        name (string): The gain-heat-cool-schedule where the conversion problem occurs.
        string (string): The string that is not convertible to float.
    """

    # Trnbuild float format
    if "," in string:
        string.replace(",", ".")
    # Try conversion to float
    try:
        to_float = float(string)
    except:
        message = "In " + name + ", the value of " + string + " is wrong. Make sure it is representing a float." 
        logger.warning(message)

def _removeStr(datafile, string, begin=0, end_string="ThisWillNeverAppearAsAStringInAnyFile", nb=1):
    """
    Remove the line containing the first occurrence of a string and return the file

    Args:
        datafile (list-like): a list-like object
        string (str): the string to find in the txt file
        begin(int): Number of lines to skip before looking for the string. Default 0.
        end_string (str): String that represent the last line to read while looking for the string. If a line contains end_line_string, then it stop. Default end of datafile.
        nb (int): number of line to remove (starting from the first line containing the string). Default 1.
    
    Returns: the datafile without the first line that include the string
    """
    value = []
    count = 0
    for line in datafile:
        if count < begin:
            count += 1
            continue
        match = re.search(string, str(line))
        if match:
            while nb >= 1:
                datafile.pop(count)
                nb -= 1
            break

        # Check if limit is passed
        limit = re.search(end_string, str(line))
        if limit:
            break
        count += 1

# ----- B18 related functions -----

def _get_zonesCharacteristics(c, file, b18_lines, dict_zone):
    """
    This function extract some zones properties (floor surface, volume, exterior surface).
    Thoses properties are then added as {"key": "value"} in the building zones dictionary.
    For example, the first value of dict_zone (i.e. {"Name": "MyZone1"}) is returned as {"Name": "MyZone1", "Surface": 25.0, "Extsurface": 85.0, "Volume": 75.0}.
    While reading the file, the function will also check for errors in floor/roof definition, and correct them before saving back the B18 file.
    
    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
        file (string): Name of the file where to save the b18_lines object.
        b18_lines (list-like): The b18 lines of the current building from which extract zones properties.
        dict_zone (dict): The zones nested-dictionary of the current building, containing a dictionary for all zones in building definition.

    Return:
        dict_zone (dict): The zones nested-dictionary updated with each zone properties.

    """
    
    for zone in dict_zone.values():
        # -------------------------------------------------------------
        # Get line of zone airnode
        zonename = zone["Name"]
        fcount = _checkStr(b18_lines, "A i r n o d e ") + 2
        zone_fcount = _checkStr(b18_lines, "AIRNODE " + zonename, begin=fcount, end_string="O u t p u t s")
    
        # Initialize
        Volume = 0.0
        Surface = 0.0
        SurfaceExt = 0.0

        # -------------------------------------------------------------
        # Read Surface
        isroof = False
        zone_floor_fcount = _checkStr(b18_lines, "FLOOR", begin=zone_fcount, end_string="REGIME", raise_error=False)
        while zone_floor_fcount != None:
            floor_line_attribute = _cleanString(b18_lines[zone_floor_fcount]).split(":")
            for attribute in floor_line_attribute:
                if "ROOF" in attribute:
                        isroof = True
                if "AREA" in attribute:
                    if not isroof:
                        Surface += float(attribute.split("=")[1])
            zone_floor_fcount = _checkStr(b18_lines, "FLOOR", begin=zone_floor_fcount + 1, end_string="REGIME", raise_error=False)
            isroof = False

        if Surface == 0:
            logger.warning("Surface is null for zone "+ zonename)

        zone_floor_fcount = _checkStr(b18_lines, "REFAREA", begin=zone_fcount, end_string="ZONE", raise_error=False)
        floor_line_attribute = _cleanString(b18_lines[zone_floor_fcount]).split(":")
        new_line = ""
        for attribute in floor_line_attribute:
            if "REFAREA" in attribute:
                Surface2 = float(attribute.split("=")[1])

                if Surface2 == 0:
                    logger.info("Correct REFAREA values with calculated floor area" + zonename)
                    attribute = "REFAREA = " + str(Surface)
            new_line += attribute + " : "

        if Surface2 == 0:
            b18_lines.pop(zone_floor_fcount)
            print(new_line)
            new_line = new_line[:-1] + "\n"
            b18_lines.insert(zone_floor_fcount, new_line)

        # -------------------------------------------------------------
        # Read SurfaceExt

        # ALL EXT_WALL
        extwall_fcount = _checkStr(b18_lines, "EXT_WALL", begin=zone_fcount, end_string="REGIME", raise_error=False)
        while extwall_fcount != None:
            floor_extwall_attribute = _cleanString(b18_lines[extwall_fcount]).split(":")
            # Get area of ext wall
            for attribute in floor_extwall_attribute:
                        if "AREA" in attribute:
                            SurfaceExt += float(attribute.split("=")[1])
            # Next exterior wall
            extwall_fcount = _checkStr(b18_lines, "EXT_WALL", begin=extwall_fcount + 1, end_string="REGIME", raise_error=False)

        # ALL EXT_ROOF
        extroof_fcount = _checkStr(b18_lines, "EXT_ROOF", begin=zone_fcount, end_string="REGIME", raise_error=False)
        while extroof_fcount != None:
            extroof_line_attribute = _cleanString(b18_lines[extroof_fcount]).split(":")
            # Get area of ext roof
            for attribute in extroof_line_attribute:
                if "AREA" in attribute:
                    SurfaceExt += float(attribute.split("=")[1])
            # Next exterior wall
            extroof_fcount = _checkStr(b18_lines, "EXT_ROOF", begin=extroof_fcount + 1, end_string="REGIME", raise_error=False)

        # ALL EXT_FLOOR
        extfloor_fcount = _checkStr(b18_lines, "EXT_FLOOR", begin=zone_fcount, end_string="REGIME", raise_error=False)
        while extfloor_fcount != None:
            extfloor_line_attribute = _cleanString(b18_lines[extfloor_fcount]).split(":")
            # Get area of ext roof
            for attribute in extfloor_line_attribute:
                if "AREA" in attribute:
                    SurfaceExt += float(attribute.split("=")[1])
            # Next exterior wall
            extfloor_fcount = _checkStr(b18_lines, "EXT_FLOOR", begin=extfloor_fcount + 1, end_string="REGIME", raise_error=False)

        # -------------------------------------------------------------
        # Read Volume
        volume_fcount = _checkStr(b18_lines, "VOLUME", begin=zone_fcount, end_string="*--------")
        volume_line_attribute = _cleanString(b18_lines[volume_fcount]).split(":")
        for attribute in volume_line_attribute:
            if "VOLUME" in attribute:
                Volume = float(attribute.split("=")[1])

        # -------------------------------------------------------------
        # Save in dict_zone
        dict_zone[zonename]["Surface"] = Surface
        dict_zone[zonename]["Extsurface"] = SurfaceExt
        dict_zone[zonename]["Volume"] = Volume

    # SAVING B18 FILES ---------------------
    with open(c.path_InputB18 + file, "w", encoding="iso-8859-1") as converted_file:
        for line in b18_lines:
            converted_file.writelines(str(line))

    return dict_zone

def _check_ZoneDependantItem(item, c):
    """
    Return True if a zone variable is used in the object definition. A variable start with c.targetkey_ZONE and is used to change the value of an attribute depending of zone parameters.

    Args:
        item (dict): A JSON object definition (heating, cooling, ventilation, infiltration, gain, schedule).
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.

    Return: 
        bool (Boolean): True or False.
    """
    for value in item.values():
        if c.targetkey_ZONE in value:

            try:
                value.index("{")
            except:
                logger.warning("ERROR: Missing an '{' for operation definition in "+ str(item["Name"]))

            try:
                value.index("}")
            except:
                logger.warning("ERROR: Missing an '}' for operation definition in "+ str(item["Name"]))
            return True
    return False   

def _make_ZoneDependantItem_FromZoneDependantValue(zone, item, c):
    """
    Modifiy item values with real values of $ZONEVOLUME, $ZONESURFACE, $ZONEEXTSURFACE or $ZONERATIOEXT.
    Assuming the dependencies is in a f(x)= A*x equation.
    Return item with f(x) instead of A*x.

    Args:
        zone (dict): dictionary of a zone (contains name,  $ZONEVOLUME, $ZONESURFACE, $ZONEEXTSURFACE.)
        item (dict): dictionnary of an REGIME item (cooling, heating, ventilation, infiltration, schedule, gains)
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.

    Return:
        item (dict): dictionnary of the given REGIME item but with calculated value using zone characteristics.
    """
    # Create new item
    item_for_zone = {}

    # Check every entries
    for k in item.keys():

        # if zone dependencies, make the change
        if c.targetkey_ZONE in str(item[k]):

            # Get {Operation zone}
            operation_start = item[k].index("{")
            operation_end = item[k].index("}")
            operation_zone = item[k][operation_start+1:operation_end] 
            # Calcul {f(x) = a * x}
            if "$ZONEVOLUME" in str(operation_zone):
                constant = float(operation_zone.split("*")[0])
                x = zone["Volume"]

            elif "$ZONESURFACE" in str(operation_zone):
                constant = float(operation_zone.split("*")[0])
                x = zone["Surface"]

            elif "$ZONEEXTSURFACE" in str(operation_zone):
                constant = float(operation_zone.split("*")[0])
                x = zone["Extsurface"] 

            elif "$ZONERATIOEXT" in str(operation_zone):
                constant = float(operation_zone.split("*")[0])
                x = zone["Extsurface"] / zone["Volume"]

            else:
                logger.warning("SpacetypeError: The variable in " + str(operation_zone) + " is not recognized.")
            
            # Calcul
            item_for_zone[k] = item[k][:operation_start] + str(constant * x) + item[k][operation_end+1:] 
        # Else just copy the entries to the new zone dependant ventilation
        else:
            item_for_zone[k] = item[k]

    # Rename the new ventilation
    item_for_zone["Name"] =  str(item["Name"] + "_" + zone["Name"])

    return item_for_zone   

# ----- JSON load spacetype  -----

def _checkB18_matching(c):
    """
    This function check walls and surfaces in building. If a zone have more thant 3 exteriors surfaces, 1 floor or 1 ceiling, then a warning is raised.
    
    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    # Get list of B18 building files name in directory
    ListOf_Building_Filenames = next(os.walk(c.path_InputB18), (None, None, []))[2]  # [] if no file
    ListOf_Building_Dict = []

    # LOOP for each of the asserted building files (.b18)
    for file in ListOf_Building_Filenames:
        if file.endswith(".B18") or file.endswith(".b18"):
            logger.info("> Starting to write writing " + file + "---------")

            # --------------------------------------
            # OPEN B18 FILE ------------------------
            with open(c.path_InputB18 + file, "r", encoding="iso-8859-1") as b18_file:
                b18_lines = b18_file.readlines()
    
            # --------------------------------------
            # GET LIST ZONE ------------------------
            listzone = reader._read_listZones_from_b18(b18_lines)

            # --------------------------------------
            # CHECK ZONE DEF -----------------------
            for zone in listzone:

                # Go to zone definition
                f_count = _checkStr(b18_lines, "AIRNODE " + zone)
                line = _cleanString(b18_lines[f_count])

                # Start counter
                extwall = 0
                extroof = 0
                extfloor= 0

                # Read airnode construction
                while not "REGIME" in line:
                    object_construction = line.split(":")[0].split("=")

                    if object_construction[0] == "WALL" and object_construction[1]=="EXT_WALL":
                        extwall += 1
                    if object_construction[0] == "ROOF" and object_construction[1]=="EXT_ROOF":
                        extroof += 1
                    if object_construction[0] == "FLOOR" and object_construction[1]=="EXT_FLOOR":
                        extfloor += 1
                
                    f_count += 1
                    line = _cleanString(b18_lines[f_count])


                # Generate log info
                logger.info("=========================================")
                logger.info("Checking b18 surface matching")
                logger.info("...")
                if extfloor > 0 and "Ftop" not in zone:
                    logger.warning("Found that "+ zone + " have 1 or more external floor. Make sure it is intended.")
                if (extroof > 0) and ("cave" not in zone):
                    logger.warning("Found that "+ zone + " have 1 or more external roof. Make sure it is intended.")
                if extwall > 2:
                    logger.warning("Found that "+ zone + " have 3 or more external walls. Make sure it is intended.")
                logger.info("=========================================")
