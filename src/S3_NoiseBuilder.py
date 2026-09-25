# Local
from src._Logging import logger 

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

def noiseValues_v1(c):
    """
    Generate noise for nominal value of zone's dhw, gains and ventilation.
    Sum of building radiative, convective and humidification gains are kept constant for the 3 categories (people, equipment, lights)
    But schedules variation implies differents total electric consumption at the end of the day.

    Args:
        c (ClassConfiguration): _description_
    """
    LL = len(c.models)
    Lcurrent = 0
        
    for buildingName in c.models:
        Lcurrent += 1
        print("Noise generation for values - Building "+buildingName+" [ "+str(Lcurrent)+"/"+str(LL)+ " ]")

        # Load file of zones attribution and characteristics ----------------------------------------
        try:
            with open(c.path_AttributionFile + buildingName + ".json", "r") as f:
                DictOfZonesProperties = json.load(f)
        except:
            logger.critical("No Zone Attribution files found for "+ buildingName +". Please generate them first.")
        
        logger.info(">> Starting to load zone characteristics files for "+buildingName)

        # Check if there are residential zones ------------------------------------------------------
        DOit = False
        for zone in DictOfZonesProperties.keys():
            if "Habitation" in DictOfZonesProperties[zone]["Spacetype"]["Name"] and not "Couloir" in  DictOfZonesProperties[zone]["Spacetype"]["Name"]:
                DOit = True
                
        # ===========================================================================================
        # Noise on values ===========================================================================
        # ===========================================================================================
        if DOit:
            # 1. Noise coefficient------------------------------------------------------------------------
            noiseCoefDHW            = 0.3
            noiseCoefGainConvective = 0.3
            noiseCoefGainRadiative  = 0.3
            noiseCoefGainHumidity   = 0.3
            noiseCoefVentilation    = 0.3
    
            # 2. Get mean values ------------------------------------------------------------------------
            for KEY in ["horexGMoyen", "horexGFami", "horexGEtud", "horexGRetr", "horexGTele"]:
                ListDHW, ListVent  = [], []
                ListOccConv, ListOccRad, ListOccHum = [], [], []
                ListEqConv, ListEqRad = [], []
                ListLightConv, ListLightRad =  [], []
                        
                for zone in DictOfZonesProperties.keys():
                    if KEY == DictOfZonesProperties[zone]["ScheduleSource"]:
                        if "Habitation" in DictOfZonesProperties[zone]["Spacetype"]["Name"] and not "Couloir" in DictOfZonesProperties[zone]["Spacetype"]["Name"]:
                            ListDHW.append(float(DictOfZonesProperties[zone]["Spacetype"]["Dhw"]["Value"]))
                            G = DictOfZonesProperties[zone]["Spacetype"]["Gains"]
                            for gain in G.keys():
                                if G[gain]["GainCategory"] == "PEOPLE":
                                    ListOccConv.append(float(G[gain]["Convective"]))
                                    ListOccRad.append(float(G[gain]["Radiative"]))
                                    ListOccHum.append(float(G[gain]["Humidity"]))
                                if G[gain]["GainCategory"] == "EQUIPMENT":
                                    ListEqConv.append(float(G[gain]["Convective"]))
                                    ListEqRad.append(float(G[gain]["Radiative"]))
                                if G[gain]["GainCategory"] == "LIGHTS":
                                    ListLightConv.append(float(G[gain]["Convective"]))
                                    ListLightRad.append(float(G[gain]["Radiative"]))                    
                            for ventilation in DictOfZonesProperties[zone]["Spacetype"]["Ventilations"].keys():
                                ListVent.append(float(DictOfZonesProperties[zone]["Spacetype"]["Ventilations"][ventilation]["FlowValue"]))

                # 3. Build that noise ----------------------------------------------------------------------
                ListRandomDHW               = randomIntervalSelection(ListOfValues=ListDHW,              Coef=noiseCoefDHW)
                ListRandomGainPeopleConv    = randomIntervalSelection(ListOfValues=ListOccConv,   Coef=noiseCoefGainConvective)
                ListRandomGainPeopleRad     = randomIntervalSelection(ListOfValues=ListOccRad,    Coef=noiseCoefGainRadiative)
                ListRandomGainPeopleHum     = randomIntervalSelection(ListOfValues=ListOccHum,    Coef=noiseCoefGainHumidity)
                ListRandomGainEquipmentConv = randomIntervalSelection(ListOfValues=ListEqConv,Coef=noiseCoefGainConvective)
                ListRandomGainEquipmentRad  = randomIntervalSelection(ListOfValues=ListEqRad, Coef=noiseCoefGainRadiative)
                ListRandomGainLightConv     = randomIntervalSelection(ListOfValues=ListLightConv,    Coef=noiseCoefGainConvective)
                ListRandomGainLightRad      = randomIntervalSelection(ListOfValues=ListLightRad,     Coef=noiseCoefGainRadiative)
                ListRandomVentilation       = randomIntervalSelection(ListOfValues=ListVent,      Coef=noiseCoefVentilation)

                # 4. Write that noise ----------------------------------------------------------------------
                i_dhw, i_vent = 0,0
                i_gainsP, i_gainsE, i_gainsL = 0,0,0

                for zone in DictOfZonesProperties.keys():
                    if KEY == DictOfZonesProperties[zone]["ScheduleSource"]:

                        if "Habitation" in DictOfZonesProperties[zone]["Spacetype"]["Name"] and not "Couloir" in DictOfZonesProperties[zone]["Spacetype"]["Name"]:
                            # Save to DHW
                            DictOfZonesProperties[zone]["Spacetype"]["Dhw"]["Value"] = ListRandomDHW[i_dhw]
                            i_dhw += 1
                            
                            # Save to Gains
                            G = DictOfZonesProperties[zone]["Spacetype"]["Gains"]
                            for gain in G.keys():
                                if G[gain]["GainCategory"] == "PEOPLE":
                                    DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Convective"] = ListRandomGainPeopleConv[i_gainsP]                         
                                    DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Radiative"] = ListRandomGainPeopleRad[i_gainsP]                            
                                    DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Humidity"] = ListRandomGainPeopleHum[i_gainsP]   
                                    i_gainsP += 1
                                if G[gain]["GainCategory"] == "EQUIPMENT":
                                    DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Convective"] = ListRandomGainEquipmentConv[i_gainsE]  
                                    DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Radiative"]  = ListRandomGainEquipmentRad[i_gainsE] 
                                    i_gainsE += 1
                                if G[gain]["GainCategory"] == "LIGHTS":
                                    DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Convective"] = ListRandomGainLightConv[i_gainsL]   
                                    DictOfZonesProperties[zone]["Spacetype"]["Gains"][gain]["Radiative"]  = ListRandomGainLightRad[i_gainsL]   
                                    i_gainsL += 1
                            # Save to Ventilation
                            for ventilation in DictOfZonesProperties[zone]["Spacetype"]["Ventilations"].keys():
                                DictOfZonesProperties[zone]["Spacetype"]["Ventilations"][ventilation]["FlowValue"] = ListRandomVentilation[i_vent]
                                i_vent += 1

        # Save file --------------------------------------------------------------------------------
        with open(c.path_AttributionFile + buildingName + ".json", "w") as f:
            json.dump(DictOfZonesProperties, f, indent=4)

def noiseValues(c):
    """
    Generate noise for nominal value of zone's dhw, gains and ventilation.
    Sum of building radiative, convective and humidification gains are kept constant for the 3 categories (people, equipment, lights)
    But schedules variation implies differents total electric consumption at the end of the day.

    Args:
        c (ClassConfiguration): _description_
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

def noiseSchedules_v1(c):
    """
    Full schedules in b18 files
    """
    Schedules = pd.read_csv(c.path_SpacetypeJSON_updated+"ScheduleInput.csv")
    LL = len(c.models)
    Lcurrent = 0
    
    for buildingName in c.models:
        Lcurrent += 1
        print("Noise generation for schedule - Building "+buildingName+" [ "+str(Lcurrent)+"/"+str(LL)+ " ]")
        SchedulesNoised = Schedules.copy()
        
        # Load file of zones attribution and characteristics ----------------------------------------
        try:
            with open(c.path_AttributionFile + buildingName + ".json", "r") as f:
                DictOfZonesProperties = json.load(f)
        except:
            logger.critical("No Zone Attribution files found for "+ buildingName +". Please generate them first.")
        
        logger.info(">> Starting to load zone characteristics files for "+buildingName)

        for zone in DictOfZonesProperties.keys():
            if "Habitation" in DictOfZonesProperties[zone]["Spacetype"]["Name"] and not "Couloir" in  DictOfZonesProperties[zone]["Spacetype"]["Name"]:

                # 1/ Get zones schedules ----------------------------------------------------------------
                schedHorex = DictOfZonesProperties[zone]["ScheduleSource"]
                zone_schedules = []
                zone_schedules_newname = []   
                for column in SchedulesNoised.columns.difference(["TIME"]):
                    if schedHorex+"_" in column:
                        zone_schedules.append(column)
                        zone_schedules_newname.append(schedHorex+zone+"_"+column.split("_")[1])
                    
                subSchedules = Schedules[zone_schedules].copy()
                sched = subSchedules[schedHorex+"_occ"]

                subSchedules.columns = zone_schedules_newname

                # 2/ First, we add noise only to occupant profiles --------------------------------------
                random.seed(999)
                interval_size = 2    # Nb of hour for the size of the random interval 
                i=interval_size
                
                while i < (len(sched)-interval_size-1):
                    # Get interval
                    interval = sched.loc[i-interval_size:i+interval_size]
                    # Check if value changes for central value of interval
                    if interval[i] != interval[i-1]:
                        
                        r = random.randint(-interval_size, interval_size)

                        if r>0:
                            subSchedules.iloc[i+r] = subSchedules.iloc[i].copy()
                            for k in [i, i+(r-1)]:
                                subSchedules.iloc[k] = subSchedules.iloc[i-1].copy()   
                            i+=r
                        if r<0:
                            subSchedules.iloc[i+r] = subSchedules.iloc[i-1].copy()
                            for k in [i-(r-1), i]:
                                subSchedules.iloc[k] = subSchedules.iloc[i].copy()
                    i+=1
                # Schedules in CSV - Stock building schedules in CSv
                DictOfZonesProperties[zone] = recursive(DictOfZonesProperties[zone], schedHorex, schedHorex+zone)
                
                """
                # Schedules in B18 - Rewrite schedule name in spacetype 
                DictOfZonesProperties[zone] = recursive(DictOfZonesProperties[zone], c.targetkey_INPUT, c.targetkey_SCHEDULE)
                for s in DictOfZonesProperties[zone]["Spacetype"]["Schedules"].keys():
                    schedule = DictOfZonesProperties[zone]["Spacetype"]["Schedules"][s]
                    schedule["SchedType"] = "ANNUAL"
                    schedule["ValueList"] = list(subSchedules[schedule["Name"]])
                    schedule["TimeList"]  = list(subSchedules.index)
                    DictOfZonesProperties[zone]["Spacetype"]["Schedules"][s] = schedule
                """
                # Save file --------------------------------------------------------------------------------
                logger.info("Built custom schedules for "+zone+" in "+buildingName+", tagged "+schedHorex+zone)
               
                # 2/Now we save zone schedules -----------------------------------------------------------------
                SchedulesNoised = pd.concat([SchedulesNoised,subSchedules], axis=1)
            
        SchedulesNoised.to_csv(c.path_OutputSCH + buildingName+".csv", index=False)
        with open(c.path_AttributionFile + buildingName + ".json", "w") as f:
            json.dump(DictOfZonesProperties, f, indent=4)
   
def noiseSchedules(c):
    """
    Full schedules in b18 files
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

    Args:
        c (ClassConfiguration): _description_
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
   
# ===========================================================================
# ===========================================================================
# ===========================================================================
