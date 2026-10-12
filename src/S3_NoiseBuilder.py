# Local
from _Logging import logger 

# Lib
import os
import json
import pandas as pd
import numpy as np
import random
# ===========================================================================
# Main workflow =============================================================
# ===========================================================================

def randomIntervalSelection(ListOfValues, Coef):
    """
    This function introduce a random noise from a controlled interval to the values of a specific attribute of eeach zone. 
    This function keep the specific attribute mean constant.
    For instance, a noise of +- Coef % will be introduced to every zone lighting gains, while keeping the total/mean lighting gain of the building identical.

    Args:
        ListOfValues (List): A list of all zones nominal value for a specific category. For instance, it could be a list of all nominal values for equipment gains.
        Coef (Float): Interval coefficient for introducing noise.

    Return:
        ListOfValues (List): The previous ListOfValues, updated with the noise.
    """
    if sum(ListOfValues) > 0:
        # Choose epsilon
        epsilon = 0.01
        # Initialize
        ListUpBound = [x*(1+Coef*(1-epsilon))  for x in ListOfValues]
        ListLowBound = [x*(1-Coef*(1-epsilon))  for x in ListOfValues]
        
        # Choose random value 
        random.seed(0)
        
        while epsilon < 1:
            
            # Choose random value
            ListOfRandomValues = [] 
            for i in range(0 ,len(ListOfValues)):
                r = random.uniform(ListLowBound[i], ListUpBound[i])
                ListOfRandomValues.append(r)

            # Correction for preservation of Total sum
            CoefCorrection = sum(ListOfValues)/sum(ListOfRandomValues)
            ListOfRandomValuesCorrected = [x*CoefCorrection for x in ListOfRandomValues]     

            # Check if correction Coeffifient allows values outside of boundaries
            if abs(1-CoefCorrection) < epsilon:
                # Noise accepted
                # print("Noise accepted (epsilon="+str(epsilon)+")")
                return ListOfRandomValuesCorrected
            
            else:
                # Noise refused
                # print("Noise refused for epsilon: ",epsilon, "(Correction at ",abs(1-CoefCorrection),")")
                epsilon += 0.01
    else:
        return ListOfValues

def noiseValues(c):
    """
    Generate noise for nominal value of zone's dhw, gains and ventilation, using the previously defined randomIntervalSelection() function.
    Sum of building radiative, convective and humidification gains are kept constant for the 3 categories (people, equipment, lights)

    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.    
    """
    LL = len(c.models)
    Lcurrent = 0
    print("Noise v2")
    for buildingName in c.models:
        Lcurrent += 1
        print("Noise generation for values - Building "+buildingName+" [ "+str(Lcurrent)+"/"+str(LL)+ " ]")

        # 0. Load file of zones attribution and characteristics ======================================
        try:
            with open(c.path_AttributionFile + buildingName + ".json", "r") as f:
                DictOfZonesProperties = json.load(f)
        except:
            logger.critical("No Zone Attribution files found for "+ buildingName +". Please generate them first.")
        
        logger.info(">> Starting to load zone characteristics files for "+buildingName)
    
        # 1. Noise coefficient ======================================================================
        noiseCoefDHW            = 0.3
        noiseCoefGainConvective = 0.3
        noiseCoefGainRadiative  = 0.3
        noiseCoefGainHumidity   = 0.3
        noiseCoefVentilation    = 0.3

        # 2.a Get list of residential ===============================================================
        list_zone_residential = [] 
        for zone in DictOfZonesProperties.keys():
            if DictOfZonesProperties[zone]["ScheduleSource"] in ["horexGMoyen", "horexGFami", "horexGEtud", "horexGRetr", "horexGTele"]:
                list_zone_residential.append(zone)
        
        # 2.b Get list of equal gains ==============================================================
        list_list_zone = {}
        for zone in list_zone_residential:
            for KEY in ["horexGMoyen", "horexGFami", "horexGEtud", "horexGRetr", "horexGTele"]:
                if KEY in DictOfZonesProperties[zone]["ScheduleSource"]:
                    try:
                        list_list_zone[KEY].append(zone)
                    except:
                        list_list_zone[KEY] = [zone]
                                      
        # 3. Get mean values ========================================================================
        ListDHW, ListEqConv, ListEqRad, ListLightConv, ListLightRad, ListOccConv, ListOccRad, ListOccHum = [], [], [], [], [], [], [], []
        for list_zone in list_list_zone.values():
            for zone in list_zone:
                # Append list of DHW
                ListDHW.append(float(DictOfZonesProperties[zone]["Spacetype"]["Dhw"]["Value"]))
                # Append list of DHW
                for gain in DictOfZonesProperties[zone]["Spacetype"]["Gains"].keys():
                    G = DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]
                    Su = DictOfZonesProperties[zone]["Surface"]

                    if G["GainCategory"] == "PEOPLE":
                        ListOccConv.append(float(G["Convective"])*Su)
                        ListOccRad.append(float(G["Radiative"])*Su)
                        ListOccHum.append(float(G["Humidity"])*Su)
                    if G["GainCategory"] == "EQUIPMENT":
                        ListEqConv.append(float(G["Convective"])*Su)
                        ListEqRad.append(float(G["Radiative"])*Su)
                    if G["GainCategory"] == "LIGHTS":
                        ListLightConv.append(float(G["Convective"])*Su)
                        ListLightRad.append(float(G["Radiative"])*Su)               
                
            # 4. Build that noise ----------------------------------------------------------------------
            ListRandomDHW               = randomIntervalSelection(ListOfValues=ListDHW,       Coef=noiseCoefDHW)
            ListRandomGainPeopleConv    = randomIntervalSelection(ListOfValues=ListOccConv,   Coef=noiseCoefGainConvective)
            ListRandomGainPeopleRad     = randomIntervalSelection(ListOfValues=ListOccRad,    Coef=noiseCoefGainRadiative)
            ListRandomGainPeopleHum     = randomIntervalSelection(ListOfValues=ListOccHum,    Coef=noiseCoefGainHumidity)
            ListRandomGainEquipmentConv = randomIntervalSelection(ListOfValues=ListEqConv,    Coef=noiseCoefGainConvective)
            ListRandomGainEquipmentRad  = randomIntervalSelection(ListOfValues=ListEqRad,     Coef=noiseCoefGainRadiative)
            ListRandomGainLightConv     = randomIntervalSelection(ListOfValues=ListLightConv, Coef=noiseCoefGainConvective)
            ListRandomGainLightRad      = randomIntervalSelection(ListOfValues=ListLightRad,  Coef=noiseCoefGainRadiative)

            # 5. Write that noise ----------------------------------------------------------------------
            i_dhw, i_vent = 0,0
            i_gainsP, i_gainsE, i_gainsL = 0,0,0

            for zone in list_zone:
                # Save to DHW
                DictOfZonesProperties[zone]["Spacetype"]["Dhw"]["Value"] = ListRandomDHW[i_dhw]
                i_dhw += 1
                
                # Save to Gains
                for gain in DictOfZonesProperties[zone]["Spacetype"]["Gains"].keys():
                    G = DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]
                    Su = DictOfZonesProperties[zone]["Surface"]
                    if G["GainCategory"] == "PEOPLE":
                        DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Convective"] = ListRandomGainPeopleConv[i_gainsP] / Su                         
                        DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Radiative"] = ListRandomGainPeopleRad[i_gainsP]  / Su                          
                        DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Humidity"] = ListRandomGainPeopleHum[i_gainsP]   / Su
                        i_gainsP += 1
                    if G["GainCategory"] == "EQUIPMENT":
                        DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Convective"] = ListRandomGainEquipmentConv[i_gainsE]  / Su
                        DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Radiative"]  = ListRandomGainEquipmentRad[i_gainsE] / Su
                        i_gainsE += 1
                    if G["GainCategory"] == "LIGHTS":
                        DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Convective"] = ListRandomGainLightConv[i_gainsL]  / Su 
                        DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Radiative"]  = ListRandomGainLightRad[i_gainsL] / Su  
                        i_gainsL += 1
                
                # Give unique name for gain in DictOfZonesProperties
                tag = ""
                schedHorex = DictOfZonesProperties[zone]["ScheduleSource"]
                if zone not in DictOfZonesProperties[zone]["ScheduleSource"]:
                    tag = zone
                    
                logger.info("Built custom schedules for "+buildingName+" in "+zone+", tagged "+schedHorex+tag)
                # Save schedule in DictOfZonesProperties
                for gg in DictOfZonesProperties[zone]["Spacetype"]["Gains"].keys():
                    DictOfZonesProperties[zone]["Spacetype"]["Gains"][gg]["Name"] = DictOfZonesProperties[zone]["Spacetype"]["Gains"][gg]["Name"]+tag
                    
        # 6. Save file --------------------------------------------------------------------------------
        with open(c.path_AttributionFile + buildingName + ".json", "w") as f:
            json.dump(DictOfZonesProperties, f, indent=4)
 
def noiseSchedules(c):
    """
    Generate noise to schedules. Annual occupancy schedule is read,every changes in occupancy are identified. Then those changes are moved by in an interval +- 2h with a gaussian-like probability.
    Schedules variation implies differents total electric consumption at the end of the day.

    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool. 
    """
    
    # Initialize 
    Schedules = pd.read_csv(c.path_SpacetypeJSON_updated+"ScheduleInput.csv")
    LL = len(c.models)
    Lcurrent = 0
    
    # Main loop
    for buildingName in c.models:
        Lcurrent += 1
        print("Noise generation for schedule - Building "+buildingName+" [ "+str(Lcurrent)+"/"+str(LL)+ " ]")
        SchedulesNoised = Schedules.copy()
        
        # 1. Load file of zones attribution and characteristics =====================================
        try:
            with open(c.path_AttributionFile + buildingName + ".json", "r") as f:
                DictOfZonesProperties = json.load(f)
        except:
            logger.critical("No Zone Attribution files found for "+ buildingName +". Please generate them first.")
        
        logger.info(">> Starting to load zone characteristics files for "+buildingName)

        
        # 2. Get list of residential ================================================================
        list_zone_residential = [] 
        for zone in DictOfZonesProperties.keys():
            if DictOfZonesProperties[zone]["ScheduleSource"] in ["horexGMoyen", "horexGFami", "horexGEtud", "horexGRetr", "horexGTele"]:
                list_zone_residential.append(zone)
        
        # 3. Create noise schedules =================================================================
        for zone in list_zone_residential:
            
            # 3.1. Get zones schedules --------------------------------------------------------------
            schedHorex = DictOfZonesProperties[zone]["ScheduleSource"]
            zone_schedules = []
            for column in Schedules.columns.difference(["TIME"]):
                if schedHorex+"_" in column:
                    zone_schedules.append(column)
                
            subSchedules = Schedules[zone_schedules].copy()
            sched = subSchedules[schedHorex+"_occ"]
            
            # 3.2. First, we add noise only to occupant profiles ------------------------------------
            intervalL = 2
            random.seed(999)
            cursor = 1
            while cursor < (len(sched) - 2):
                if sched.loc[cursor] != sched.loc[cursor+1]:
                    r = random.randint(0, intervalL)
                    for i in range(1, r+1):
                        subSchedules.iloc[cursor+i] = subSchedules.iloc[cursor]
                        cursor += 1
                cursor += 1

            while cursor > 1:
                if sched.loc[cursor] != sched.loc[cursor-1]:
                    r = random.randint(0, intervalL)
                    for i in range(1, r+1):
                        subSchedules.iloc[cursor-i] = subSchedules.iloc[cursor]
                        cursor -= 1
                cursor -= 1
            
            
                      
            # 2.3. Save file ------------------------------------------------------------------------
            # SchedulesNoised = SchedulesNoised[Schedules.columns.difference(subSchedules.columns)].copy()
            tag = ""
            if zone not in schedHorex:
                tag = zone
            logger.info("Built custom schedules for "+buildingName+" in "+zone+", tagged "+schedHorex+tag)
            # Save schedule in DictOfZonesProperties
            DictOfZonesProperties[zone] = recursive(DictOfZonesProperties[zone], schedHorex, schedHorex+tag)
            for hh in DictOfZonesProperties[zone]["Spacetype"]["Heatings"].keys():
                DictOfZonesProperties[zone]["Spacetype"]["Heatings"][hh]["Name"] = DictOfZonesProperties[zone]["Spacetype"]["Heatings"][hh]["Name"]+tag
            for cc in DictOfZonesProperties[zone]["Spacetype"]["Coolings"].keys():
                DictOfZonesProperties[zone]["Spacetype"]["Coolings"][cc]["Name"] = DictOfZonesProperties[zone]["Spacetype"]["Coolings"][cc]["Name"]+tag
            for gg in DictOfZonesProperties[zone]["Spacetype"]["Gains"].keys():
                DictOfZonesProperties[zone]["Spacetype"]["Gains"][gg]["Name"] = DictOfZonesProperties[zone]["Spacetype"]["Gains"][gg]["Name"]+tag
                                    
            # Update schedule CSV file
            zone_schedules_newname = []   
            for column in subSchedules.columns:             
                zone_schedules_newname.append(schedHorex+tag+"_"+column.split("_")[1])
            subSchedules.columns = zone_schedules_newname
            SchedulesNoised = pd.concat([SchedulesNoised,subSchedules], axis=1)
            
        # 4. Schedules in CSV - Stock building schedules in CSV =====================================          
        SchedulesNoised.to_csv(c.path_OutputSCH + buildingName+".csv", index=False)
        with open(c.path_AttributionFile + buildingName + ".json", "w") as f:
            json.dump(DictOfZonesProperties, f, indent=4)
          
def noiseTsetpoint(c):
    """
    Generate noise on schedule setpoint base value of every residential area for every schedule file.
    Using interval and wieght: 
        - interval = [-3, -2 , -1 , 0   , 1   , 2  , 3  ]  
        - weight   = [5%, 10%, 10%, 25% , 25% , 15%, 10%]
        
    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.    
    """
    logger.info("Modifying base value of T° setpoint for every residential profiles of each schedule file")
    Lcurrent = 0
    ListSched = next(os.walk(c.path_OutputSCH), (None, None, []))[2]
    LL = len(ListSched)

    for schedFile in ListSched:
        Lcurrent += 1
        print("Noise generation for T setpoint - Schedule file "+schedFile[:-4]+" [ "+str(Lcurrent)+"/"+str(LL)+ " ]")
        
        Schedules = pd.read_csv(c.path_OutputSCH + schedFile)
        SchedulesNoised =  Schedules.copy()

        random.seed(666)
        interval = [-3  , -2 , -1 , 0   , 1   , 2   , 3  ]    # Nb of °C around mean T°setpoint value is to be taken from
        weight   = [0.05, 0.1, 0.1, 0.25, 0.25, 0.15, 0.1]
        
        
        for column in Schedules.columns.difference(["TIME"]):
            
            if "horexG" in column and ("cool" in column or "heat" in column):
                r = random.choices(interval, weights=weight, k=1)[0]
                for i in range(0, len(SchedulesNoised.index)):
                    if "cool" in column:
                        if SchedulesNoised.loc[i,column] - r > 22:
                            SchedulesNoised.loc[i,column] -= r
                        else:
                            SchedulesNoised.loc[i,column] = 22          
                    if "heat" in column:
                        if SchedulesNoised.loc[i,column] + r < 22:
                            SchedulesNoised.loc[i,column] += r
                        else:
                            SchedulesNoised.loc[i,column] = 22
        
        SchedulesNoised.to_csv(c.path_OutputSCH + schedFile, index=False)
        
def recursive(d, stringcheck, extension):
    for k,v in d.items():
        if type(v)==str:
            if stringcheck in v :
                d[k] = d[k].replace(stringcheck, extension)
        elif type(v) is dict:
            recursive(v, stringcheck, extension)
    return d
   
def noise(c):
    """
    Main function for noise.
    Will call noise function if precision of occupancy is stochastic.

    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.    
    """
    if c.Precision_EXP == "stochastic":
        print("Step 3 - Creating noise (can take some time)")
        noiseValues(c)
        noiseSchedules(c)
        noiseTsetpoint(c)
    else:
        print("Step 3 - Skipping noise generation")
# ===========================================================================
# ===========================================================================
# ===========================================================================
