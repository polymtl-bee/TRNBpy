# Local
import src._TranslateToB18 as reader
import src._Utils as utils
from src._Logging import logger 
# Lib
import os
import json
import pandas as pd
import random


def _BuildSpacetypeSurface(c):
    """
    Function used to initialize Spacetype surfaces in the building surfaces CSV files.
    Read the building surface file, create new columns for each spacetype, update surface value for each {cluster, spacetype} according to cluster enduse surface, weight, and spacetype probability from parameters SpacetypeDict in ClassConfiguration object `c`.
    
    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    for file in os.listdir(c.path_UsedBuilding_SurfaceDetails):
        df  = pd.read_csv(c.path_UsedBuilding_SurfaceDetails + file, skipinitialspace=True, index_col="Name").fillna(0)

        # Get spacetype surface from wanted ratios -------------------------------------
        AllChoices = c.DictSpacetype
        list_choice = []
        for choice_type in AllChoices.keys():
            for choice in AllChoices[choice_type].keys():
                if choice not in list_choice:
                    list_choice.append(choice)

        # Initialize spacetype surfaces
        for ch in list_choice:
            df[ch] = [0.0] * len(df.index)

        # Get estimated spacetype surfaces for leftovers
        for choice_type in AllChoices.keys():
            if choice_type in df.columns:
                for choice in AllChoices[choice_type].keys():
                    for i in df.index:
                        df.loc[i, choice] += df.loc[i, choice_type] * df.loc[i, "Weight"] * AllChoices[choice_type][choice]
        df.to_csv(c.path_GeneratedSurfaceRecap + file, index=True, index_label="Name")


def _ChooseSpacetype_Probability(b18_lines, b18_dict_zone, file, c):
    """

      Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    
    Return:
        b18_dict_zone
    """
    logger.info("Attributing end use to zones with conditionnals objectives "+file)
    
    # Get Surface objectives -------------------------------------------------------
    try:
        # Areas decided for each spacetype
        decided      = pd.read_csv(c.path_GeneratedSurfaceRecap + file + ".csv", skipinitialspace=True, index_col="Name")
        # Will be used to update leftover area per spacetype after each attribution
        leftovers  = pd.read_csv(c.path_GeneratedSurfaceRecap + file + ".csv", skipinitialspace=True, index_col="Name")
    except: 
        logger.critical("No surface recap found for file "+file+". Surface recap files should contains Total surfaces and central weight for each SubBuilding of real building represented by the model.")

    # Get spacetype surface from wanted ratios -------------------------------------
    AllChoices = c.DictSpacetype
    list_choice = []
    for choice_type in AllChoices.keys():
        for choice in AllChoices[choice_type].keys():
            if choice not in list_choice:
                list_choice.append(choice)

    # Initialize spacetype surfaces
    for ch in list_choice:
        decided[ch] = [0.0] * len(decided.index)

    # By zone ----------------------------------------------------------------------
    
    # Get list of zones in random order
    list_zone = list(b18_dict_zone.keys()).copy()
    random.seed(111)
    random.shuffle(list_zone)

    # Choosing spacetype algorithm
    for zone in list_zone:

        # Get zone characteristics from zone name
        try:
            zonetype, zoneSubBuilding, zoneFloor, zoneId = zone.split("-")
            zonecluster = file + "_" + zoneSubBuilding + "_" + zoneFloor
        except:
            logger.critical("Wrong zone format for file " + file + " and zone " + zone)
        
        zonesurface = b18_dict_zone[zone]["Surface"]


        # Probability function
        p = {}
        chosen = None

        # Get total leftover for zonetype
        leftover_tot = 0

        if len(AllChoices[zonetype])>1:
            for choice in AllChoices[zonetype]:

                leftover_tot += leftovers.loc[zonecluster, choice] 
            
            if leftover_tot == 0:
                logger.critical("Problem occured while choosing spacetype for "+zonecluster+ " while looking for "+ str(AllChoices[zonetype])+". Please check your DictSpacetype and/or the building detailed area file !")
            # Get each choice new probability (leftover area on total leftover area)
            for choice in AllChoices[zonetype]:
                p[choice] = leftovers.loc[zonecluster, choice] / leftover_tot
        else:
            p[list(AllChoices[zonetype].keys())[0]] = 1
            
        # Choose choice
        random.seed(222)
        chosen = random.choices(population=list(AllChoices[zonetype].keys()), weights=p.values())[0]
        chosen_surface = b18_dict_zone[zone]["Surface"] * leftovers.loc[zonecluster, "Weight"]

        # Apply choice
        b18_dict_zone[zone]["Spacetype"]["Name"] = chosen
        leftovers.loc[zonecluster, chosen] = max(0, leftovers.loc[zonecluster, chosen] - chosen_surface)
        # Save zone surface, without weight
        try: decided.loc[zonecluster, chosen] += b18_dict_zone[zone]["Surface"]
        except: decided.loc[zonecluster, chosen] = b18_dict_zone[zone]["Surface"]

    # Save back decided surface.
    #decided.to_csv(c.path_GeneratedSurfaceRecap + "/" +  file + ".csv", index=True, index_label="Name")

    # Get real percentage
    """
    checkSP = {}
    STOT = 0
    for zone in list_zone:
        if "Habitation" in b18_dict_zone[zone]["Spacetype"]["Name"] and not "Couloir" in b18_dict_zone[zone]["Spacetype"]["Name"]:
            STOT += b18_dict_zone[zone]["Surface"]

    for zone in list_zone:
        if "Habitation" in b18_dict_zone[zone]["Spacetype"]["Name"] and not "Couloir" in b18_dict_zone[zone]["Spacetype"]["Name"]:
            try:
                checkSP[b18_dict_zone[zone]["Spacetype"]["Name"]] += b18_dict_zone[zone]["Surface"]/STOT
            except:
                checkSP[b18_dict_zone[zone]["Spacetype"]["Name"]] = b18_dict_zone[zone]["Surface"]/STOT
    print(checkSP)
    """
    return b18_dict_zone

def _ChooseSpacetype_Manually(b18_lines, b18_dict_zone, file, c):   
    """
    """  
    for zone in b18_dict_zone.keys():
        # Get zone characteristics ----------------------------------------------------
        try:
            zonetype, zoneSubBuilding, zoneFloor, zoneId = zone.split("-")
        except:
            logger.critical("Wrong zone format for file " + file + " and zone " + zone)

        # Attribute spacetype corresponding to zonetype identifier --------------------
        # Residential
        if zonetype == "RC":
            b18_dict_zone[zone]["Spacetype"]["Name"] = "HabitationCouloir"
        
        elif zonetype == "R":
            b18_dict_zone[zone]["Spacetype"]["Name"] = "Habitation"

        # Office
        elif zonetype == "B":
            b18_dict_zone[zone]["Spacetype"]["Name"] = "Bureaux"
        
        elif zonetype == "BC":
            b18_dict_zone[zone]["Spacetype"]["Name"] = "BureauxCouloir"

        # School
        elif zonetype == "IE":
            b18_dict_zone[zone]["Spacetype"]["Name"] = "Ecole"
        
        # Library
        elif zonetype == "IB":
            b18_dict_zone[zone]["Spacetype"]["Name"] = "Bibliotheque"
        
        # Gymnasium
        elif zonetype == "CG":
            b18_dict_zone[zone]["Spacetype"]["Name"] = "Gym"
        
        # Theater
        elif zonetype == "CT":
            b18_dict_zone[zone]["Spacetype"]["Name"] = "Theatre"
        
        # Workshop
        elif zonetype == "IA":
            b18_dict_zone[zone]["Spacetype"]["Name"] = "Atelier"

        # Commercial
        elif zonetype.startswith("C"):
            if zonetype == "CB":
                b18_dict_zone[zone]["Spacetype"]["Name"] = "Restauration"
            else: 
                b18_dict_zone[zone]["Spacetype"]["Name"] = "Commerce"
     
        # Parking
        elif zonetype == "P":
            b18_dict_zone[zone]["Spacetype"]["Name"] = "Parking"

        # If identifier not found, give "N/A" -----------------------------------------
        else:
            b18_dict_zone[zone]["Spacetype"]["Name"] = "N/A"
        # -----------------------------------------------------------------------------
    return b18_dict_zone

def _BuildJSONFile(c):
    """
    """
    # Get list of building file names in directory
    ListOf_Building_Filenames = c.models

    # Get files ready
    _BuildSpacetypeSurface(c)

    # for each of those building files (.B18) :
    for file in ListOf_Building_Filenames:
        logger.info("> Starting spacetype attribution for "+file)
        # Load input file ===========================================================================
        with open(c.path_InputB18 + file + ".b18", "r", encoding="iso-8859-1") as b18_file:
            b18_lines = b18_file.readlines()

        # 1. Get zone's JSON =======================================================================
        
        # Get zones
        b18_dict_zone = reader._read_listZones_from_b18(b18_lines=b18_lines)
        
        # Get zone surface and characteristics
        b18_dict_zone = utils._get_zonesCharacteristics(c=c, file=file+".b18", b18_lines=b18_lines, dict_zone=b18_dict_zone)
        
        # 2. Attribute spacetypes to zones =======================================================================

        # Initialize zone's spacetype attribute
        for zone in b18_dict_zone.keys():
            b18_dict_zone[zone]["Spacetype"] = {}

    
        
        # Get zone's spacetype name  
        if c.Precision_BLD == "detailed":
            b18_dict_zone = _ChooseSpacetype_Probability(b18_lines, b18_dict_zone, file, c)
        else:
            b18_dict_zone = _ChooseSpacetype_Manually(b18_lines, b18_dict_zone, file, c)
        
        # Get zone's spacetype data
        list_spacetype = (x for x in next(os.walk(c.path_SpacetypeJSON_updated), (None, None, []))[2] if ".json" in x)
        
        for filee in list_spacetype:
            # Get spacetype data
            with open(c.path_SpacetypeJSON_updated + filee, "r") as f:
                spacetype = json.load(f)
            # Check
            for zone in b18_dict_zone.keys():
                if b18_dict_zone[zone]["Spacetype"]["Name"] == spacetype["Name"]:
                    b18_dict_zone[zone]["Spacetype"] = json.loads(json.dumps(spacetype))

        # 3. Get dict of spacetype horex ===============================================================
        dict_sp_sched = {}
        for filee in (x for x in next(os.walk(c.path_SpacetypeJSON_raw), (None, None, []))[2] if ".json" in x):
            with open(c.path_SpacetypeJSON_raw + filee, "r") as f:
                spacetype = json.load(f)
            dict_sp_sched[spacetype["Name"]] = {"ScheduleSource": spacetype["ScheduleSource"], "LoadsDhw": spacetype["Dhw"]["Value"]}
        
        # Get schedule and DHW ======================================================================
        for zone in b18_dict_zone.keys():
            try:
                b18_dict_zone[zone]["ScheduleSource"] = dict_sp_sched[b18_dict_zone[zone]["Spacetype"]["Name"]]["ScheduleSource"]
                b18_dict_zone[zone]["LoadsDhw"]       = dict_sp_sched[b18_dict_zone[zone]["Spacetype"]["Name"]]["LoadsDhw"]
            except:
                logger.critical("Attribution failed. Trying to push a non-existent spacetype to zone: " + str(zone))

            # Get floor
            try:
                floor = b18_dict_zone[zone]["Name"].split("-")[2]
                b18_dict_zone[zone]["Floor"] = floor

            except:
                b18_dict_zone[zone]["Floor"] =  "N/A"
        
        # Build value for zone dependant item ========================================================
        infooverflow = 0
        for zone in b18_dict_zone.keys():

            # Check for
            WhereToLookFor = ["Schedules", "Gains", "Ventilations", "Infiltrations", "Heatings", "Coolings"]

            # Check for zone dependant items
            for LookingHere in WhereToLookFor:
                for nb in b18_dict_zone[zone]["Spacetype"][LookingHere].keys():

                    item = b18_dict_zone[zone]["Spacetype"][LookingHere][str(nb)]

                    if utils._check_ZoneDependantItem(item=item, c=c):
                        new_item = utils._make_ZoneDependantItem_FromZoneDependantValue(zone=b18_dict_zone[zone], item=item, c=c)
                        b18_dict_zone[zone]["Spacetype"][LookingHere][str(nb)] = new_item

                        if infooverflow == 0:
                            logger.info(">>> Detected zone dependant item")
                            infooverflow = 1


        # Save file ==================================================================================
        with open(c.path_AttributionFile + file + ".json", "w") as f:
            json.dump(b18_dict_zone, f, indent=4)
