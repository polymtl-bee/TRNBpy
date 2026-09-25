# Local
from src._Logging import logger 
# Lib
import os
import json
import pandas as pd
import numpy as np

# ================================================================================
# Utils function =================================================================
# ================================================================================
  
def _get_ModelLoads_FromCSV(c, filee, Model_DictOfZonesProperties, path="", starttime=0.0):
    """
    Read a bunch of files found in directory 'path'. Read those files and stored them in a pandas dataframe.
    Make sure every files have the same time series, because this function will append on columns.

    Returns:
        Model_Loads (DataFrame): A panda DataFrame containing all columns in list_key categories for each files read.

    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
        filee (str): Name of an annual schedule file used (taken from c.path_OutpuSCH).
        Model_DictOfZonesProperties (Dict): JSON file description of zones properties.
        path (str): Path to the directory containing the loads resulting from a TRNSYS simulation of a deck.
        starttime (float): Starttime used to read the time series of the files.
    """

    # 1/ Initialize
    list_files_raw = os.listdir(path)
    list_key  = list(c.DictOutput.values())
    
    if c.Precision_EXP == "stochastic":
        try: 
            pd.read_csv(c.path_OutputSCH + filee + ".csv")
            PATH_SCHEDULE_FILE = c.path_OutputSCH + filee + ".csv"
        except:
            PATH_SCHEDULE_FILE = c.path_ScheduleAnnualInputFile     
    else:
        PATH_SCHEDULE_FILE = c.path_ScheduleAnnualInputFile


    schedules_csv = pd.read_csv(PATH_SCHEDULE_FILE, skipinitialspace=True, index_col="TIME")
    Model_Loads = {}

    # 2/ Raise error for wrong format
    list_fileDF = {}
    for file in list_files_raw:
        if ".csv" in file or ".CSV" in file:
            file_df = pd.read_csv(path + c.psep + file, sep="\t", skipinitialspace=True)
            file_df.columns = file_df.columns.str.strip()
            if len(file_df.index)<8759:
                logger.critical(">> Loading loads file have failed for " + file+". "+ c.path_OutputSIM + file + c.psep + str(len(file_df.index)))
            else:
                list_fileDF[file] = file_df

    # 3/ Get data for each file
    for file_df in list_fileDF.values():
        for columnName in file_df.columns:
            for key in list_key:
                if key in columnName:
                    try:
                        Model_Loads[key] = pd.concat([Model_Loads[key], file_df[[columnName]]], axis=1)
                    except:
                        Model_Loads[key] = file_df[['TIME']].copy()
                        Model_Loads[key] = pd.concat([Model_Loads[key], file_df[[columnName]]], axis=1)

    # 4/ Rename columns
    for key in list_key:
        colnew = []
        for col in Model_Loads[key].columns:
            colnew.append(col.replace(key+"_",""))
        Model_Loads[key].columns = colnew
    
    # 4/ Add data for DHW
    Model_Loads["DHW"] = file_df[['TIME']].copy()


    for zone in Model_DictOfZonesProperties.keys():
        # Get zone attributes

        DhwSched = Model_DictOfZonesProperties[zone]["ScheduleSource"] 
        DhwSurf = float(Model_DictOfZonesProperties[zone]["LoadsDhw"])  # [kJ/hr.m²]
        Surface = float(Model_DictOfZonesProperties[zone]["Surface"])  # [m²]

        # Get zone DHW
        AnnualSched = schedules_csv[DhwSched + "_dhw"].copy()

        AnnualSched = AnnualSched.rename(zone)
        AnnualSched.index += 1
        AnnualSched[0] = 0.0
        zone_DHW = AnnualSched * DhwSurf * Surface

        # Scale up from zone
        Model_Loads["DHW"] = pd.concat([Model_Loads["DHW"], zone_DHW], axis=1)


    # 5/ Add TOT
    Model_Loads["QCOOLTOT"] = Model_Loads["QCOOL"] + Model_Loads["QDEHUM"]
    Model_Loads["QHEATTOT"] = Model_Loads["QHEAT"] + Model_Loads["QHUM"]+ Model_Loads["DHW"]
    Model_Loads["QELECTOT"] = Model_Loads["QELEQUIP"] + Model_Loads["QELLIGHT"]
    Model_Loads["QCOOLTOT"]["TIME"] = file_df[['TIME']].copy()
    Model_Loads["QHEATTOT"]["TIME"] = file_df[['TIME']].copy()
    Model_Loads["QELECTOT"]["TIME"] = file_df[['TIME']].copy()

    if Model_Loads == {}:
        logger.warning("No csv files detected in "+ path)
    

    return Model_Loads
   
def _print_stats(DF, c, file, SurfaceSerie):
    """
    This function calculate and save annual statistics of a dataframe. 
    It calculate total annual consumption (kJ and GWh), min and max power values (kJ/hr and MW), and surfacic annual consumption (kWh/m²)
    Statistics are saved in c.path_OutputLOADS dircetory, under 'file + _STATS.csv' name.

    Args:
        DF (pd.DataFrame): A pandas dataframe (in [kJ/hr]) containing the building loads.
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
        file (str): Name of dir/file in which to read simulations results.
        SurfaceSerie (pd.Series): A pandas series containing total surfaces on which columns loads are applicable to. It is used to calculate surfacic loads.

    """
    # Define global metrics
    S_sum = DF.sum().rename("sum[kj]")
    S_min = DF.min().rename("min[kj/hr]")
    S_max = DF.max().rename("max[kj/hr]")
    S_sum_GWh = DF.sum().multiply(other=1/3600/1000/1000).rename("sum[GWh]")
    S_min_MW = DF.min().multiply(other=1/3600/1000).rename("min[MW]")
    S_max_MW = DF.max().multiply(other=1/3600/1000).rename("max[MW]")
    S_sum_GWhm2 = DF.sum().divide(SurfaceSerie).multiply(other=1/3600).rename("sum[kWh/m²]")

    # Create dataframe with metrics
    DF_STATS = pd.concat([SurfaceSerie, S_sum, S_min, S_max, S_sum_GWh, S_min_MW, S_max_MW, S_sum_GWhm2], axis=1)
    
    # Print & save dataframe
    pd.DataFrame(DF_STATS).to_csv(c.path_OutputLOADS + file, index=True)

def _ModelsLoader(c, deckList):
    """
    """
    DictOf_Model_Loads, DictOf_Model_DictOfZonesProperties = {}, {} 

    for model_filename in deckList:
        logger.info(">> Starting to load files for: "+model_filename)
        # 1.1 Load file of zones attribution and characteristics ------------------------------------
        try:
            with open(c.path_AttributionFile + model_filename + ".json", "r") as f:
                DictOf_Model_DictOfZonesProperties[model_filename] = json.load(f)
        except:
            logger.critical("No Zone Attribution files found. Please generate them first.")
        
        # 1.2 Load Models Loads ------------------------------------------------------------------
        try:
            DictOf_Model_Loads[model_filename] = _get_ModelLoads_FromCSV(c, model_filename, DictOf_Model_DictOfZonesProperties[model_filename], c.DictSIMpath[model_filename])
        except:
            logger.critical(">> Loading loads file have failed for " + model_filename+". "+ c.path_OutputSIM + model_filename)

    return DictOf_Model_Loads, DictOf_Model_DictOfZonesProperties

def _GetClusterLoads(Cluster_Dict, Model_Loads, Model_DictOfZonesProperties):
    """
    """
    for Cluster in Cluster_Dict.keys():
        
        # Initialize
        Cluster_Surface = 0.0

        # Calcul for cluster loads and surface verification
        for KEY in Model_Loads.keys():
            for zone in Model_DictOfZonesProperties.keys():
                zone_found = False
                zone_cluster = Model_DictOfZonesProperties[zone]["ClusterName"]
                for columnName in Model_Loads[KEY].columns.difference(['TIME']):
                    if (zone == columnName.replace(KEY+"_", "")):                
                        zone_found = True
                        if (zone_cluster == Cluster):
                            # Get Cluster Surface 
                            # (Because we do it for each KEY, we must divide by said number of KEY)
                            Cluster_Surface += Model_DictOfZonesProperties[zone]["Surface"] / len(Model_Loads.keys())

                            # Get Cluster load
                            try:
                                Cluster_Dict[Cluster]["LOADS"][KEY] += Model_Loads[KEY][columnName] 
                            except:
                                try:
                                    Cluster_Dict[Cluster]["LOADS"][KEY]  = Model_Loads[KEY][columnName]
                                except:
                                    Cluster_Dict[Cluster]["LOADS"] = Model_Loads[list(Model_Loads.keys())[0]][["TIME"]].copy()
                                    Cluster_Dict[Cluster]["LOADS"][KEY]  = Model_Loads[KEY][columnName]

                # Generate critical warning if no matching detected.
                if zone_found == False:
                    logger.critical("Matching failed. "+zone+ " not found in "+str(Model_Loads[KEY].columns.difference(['TIME'])))
        
        # Save in Cluster Dict
        if abs(Cluster_Dict[Cluster]["MODEL_SURFACE"] - Cluster_Surface) > 1:
            logger.critical(">>> Failed to get cluster loads for the right surface: "+ str(Cluster_Surface) + " (Calculated), "+ str(Cluster_Dict[Cluster]["MODEL_SURFACE"]) + " (Estimated)")
    return Cluster_Dict
    
def _GetBuildingLoads(Cluster_Dict, Model_Loads):
    """
    """
    # Initialize
    Building_Loads = Model_Loads[list(Model_Loads.keys())[0]][["TIME"]].copy()
    Building_Surface = 0
    
    # Sum for each cluster
    for cluster in Cluster_Dict.keys():
        Building_Surface += Cluster_Dict[cluster]["BUILDING_SURFACE"]
        
        for KEY in Model_Loads.keys():
            ratio = Cluster_Dict[cluster]["BUILDING_SURFACE"] / Cluster_Dict[cluster]["MODEL_SURFACE"]
            try:
                Building_Loads[KEY] += Cluster_Dict[cluster]["LOADS"][KEY] * ratio
            except:
                Building_Loads[KEY] = Cluster_Dict[cluster]["LOADS"][KEY] * ratio

    # Return
    return Building_Loads, Building_Surface

def _GetSurfacicZoneLoads(c, Model_Loads, Model_DictOfZonesProperties):
    """
    """
    # Calcul for cluster loads and surface verification
    
    try:
        DFSURF = pd.read_csv(c.path_OutputLOADS + "ZONESSURF"+c.psep + "ZONE.csv", index_col="NAME")
    except:
        DFSURF = pd.DataFrame(columns= ["QHEAT", "QCOOL"], index=list(Model_DictOfZonesProperties.keys()))
        
    for KEY in ["QHEAT", "QCOOL"]:
        
        for zone in Model_DictOfZonesProperties.keys():
            zone_found = False

            for columnName in Model_Loads[KEY].columns.difference(['TIME']):
                if (zone == columnName.replace(KEY+"_", "")):                
                    zone_found = True
                    DFSURF.loc[zone,KEY] = sum(Model_Loads[KEY][columnName].copy()) / Model_DictOfZonesProperties[zone]["Surface"]
                                
        DFSURF.to_csv(c.path_OutputLOADS + "ZONESSURF"+c.psep + "ZONE.csv", index=True, index_label="NAME")        
                
         
def _UpdateSiteLoads(Model_Loads, Site_Loads, Site_Surface, Building_Loads, Building_Surface):
    try:    Site_Surface += Building_Surface
    except: Site_Surface = Building_Surface
    for KEY in Building_Loads.keys():
        try:    Site_Loads[KEY] += Building_Loads[KEY]
        except: Site_Loads[KEY] = Building_Loads[KEY]

    return Site_Loads, Site_Surface

def _UpdateSpacetypeLoads(Model_Loads, Model_DictOfZonesProperties, Spacetype_Loads, Spacetype_Surface):
    Cluster_BySpacetype_Dict = {}
    for zoneName in Model_DictOfZonesProperties.keys():
        # Get cluster
        cluster = Model_DictOfZonesProperties[zoneName]["Spacetype"]["Name"]
        
        # Save zone'cluster in zone properties
        Model_DictOfZonesProperties[zoneName]["ClusterName"] = cluster

        # Get Cluster MODEL_SURFACE
        try:
            Cluster_BySpacetype_Dict[cluster]["MODEL_SURFACE"] += Model_DictOfZonesProperties[zoneName]["Surface"]
        except:
            try:
                Cluster_BySpacetype_Dict[cluster]["MODEL_SURFACE"] = Model_DictOfZonesProperties[zoneName]["Surface"]
            except:
                Cluster_BySpacetype_Dict[cluster] = {}
                Cluster_BySpacetype_Dict[cluster]["MODEL_SURFACE"] = Model_DictOfZonesProperties[zoneName]["Surface"]

    Cluster_BySpacetype_Dict = _GetClusterLoads(Cluster_BySpacetype_Dict, Model_Loads, Model_DictOfZonesProperties)

    for s in Cluster_BySpacetype_Dict.keys():
        try:
            Spacetype_Loads[s], Spacetype_Surface[s] = _UpdateSiteLoads(Model_Loads,  Spacetype_Loads[s], Spacetype_Surface[s], Cluster_BySpacetype_Dict[s]["LOADS"], Cluster_BySpacetype_Dict[s]["MODEL_SURFACE"])
        except:
            try: 
                Spacetype_Loads[s], Spacetype_Surface[s] = Model_Loads[list(Model_Loads.keys())[0]][["TIME"]].copy(), 0.0
                Spacetype_Loads[s], Spacetype_Surface[s] = _UpdateSiteLoads(Model_Loads,  Spacetype_Loads[s], Spacetype_Surface[s], Cluster_BySpacetype_Dict[s]["LOADS"], Cluster_BySpacetype_Dict[s]["MODEL_SURFACE"])           
            except:
                Spacetype_Loads, Spacetype_Surface = {}, {}
                Spacetype_Loads[s], Spacetype_Surface[s] = Model_Loads[list(Model_Loads.keys())[0]][["TIME"]].copy(), 0.0
                Spacetype_Loads[s], Spacetype_Surface[s] = _UpdateSiteLoads(Model_Loads,  Spacetype_Loads[s], Spacetype_Surface[s], Cluster_BySpacetype_Dict[s]["LOADS"], Cluster_BySpacetype_Dict[s]["MODEL_SURFACE"])
    return Spacetype_Loads, Spacetype_Surface

# ================================================================================
# Smoothing functions ============================================================
# ================================================================================

def smoothing(c):
    """
    
    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.   
    """ 
    ListOf_LoadFile = os.listdir(c.path_OutputLOADS + "LOADS"+c.psep)

    for LoadFile in ListOf_LoadFile:
        
        # Load file
        Model_Loads = pd.read_csv(c.path_OutputLOADS + "LOADS"+c.psep+ LoadFile, skipinitialspace=True, index_col="TIME")
        Model_Loads_SMOOTH = Model_Loads.copy()
        # Smoothing algorithm
        weights = [0.05, 0.2, 0.5, 0.2, 0.05]
        w_name = "smooth1_equal"

        # Calculate WMA
        for col in Model_Loads.columns:
            Model_Loads_SMOOTH.loc[:, col] = Model_Loads.loc[:,col].rolling(window=len(weights), center=True, min_periods=1).apply(lambda x: np.dot(x, weights[0:len(x)])/sum(weights), raw=True)


        # Save file
        pd.DataFrame(Model_Loads_SMOOTH).to_csv(c.path_OutputLOADS + "LOADS"+c.psep+ LoadFile , index=True)

# ================================================================================
# Main step functions ============================================================
# ================================================================================

def scaling_detailed(c):
    """
    Given the path_OutputSIM, will check for every model the presence of CSV files. 
    If any CSV file is found, then scaling up methods are started.
    
    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.   
    """
    # ============================================================================================
    # 0/ Initialize ==============================================================================
    # ============================================================================================
    logger.info("> Starting {0/ Initialize}")

    # Load all Models data
    DictOf_Model_Loads, DictOf_Model_DictOfZonesProperties = _ModelsLoader(c, c.models)

    # Initialize Site
    Site_Loads, Site_Surface = pd.DataFrame({"TIME": list(range(8760))}), 0.0
    
    # Initialize Spacetype
    Spacetype_Loads, Spacetype_Surface = {}, {}
    for S in c.DictSpacetype.values():
        for s in S.keys():
            Spacetype_Loads[s], Spacetype_Surface[s]  = pd.DataFrame({"TIME": list(range(8760))}), 0.0
    
    # ============================================================================================
    # 1/ Sizing Algorithm ========================================================================
    # ============================================================================================
    logger.info("> Starting {1/ Sizing Algorithm}")
    
    # Sizing algorithm for each file
    for current_building in c.models: 
        
        logger.info("---------------------------------------------------")
        logger.info(" ::::: " + current_building + " ::::: ")

        # ----------------------------------------------------------------------------------------
        # 1.0 Building data ----------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------
      
        try:
            Building_SurfaceDetails = pd.read_csv(c.path_GeneratedSurfaceRecap + current_building + ".csv" , skipinitialspace=True, index_col="Name")
            Building_SurfaceDetails.fillna(0.0, inplace=True)
        except: 
            logger.critical("No surface recap found for file "+current_building+". Surface recap files should contains Total surfaces and central weight for each SubBuilding of real building represented by the model. Check path: "+ c.path_GeneratedSurfaceRecap +"_"+current_building+".csv")  
        
        # ----------------------------------------------------------------------------------------
        # 1.1 Load files -------------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------
        # Choose model
        chosen_model  = current_building
        
        # Get Model data
        Model_Loads = DictOf_Model_Loads[chosen_model]
        Model_DictOfZonesProperties = DictOf_Model_DictOfZonesProperties[chosen_model]
        
        # ----------------------------------------------------------------------------------------
        # 1.2 Cluster definition for sizing algorithm --------------------------------------------
        # ----------------------------------------------------------------------------------------
        logger.info(">> Start scaling algorithm for " + current_building + ". Using "+chosen_model+" as load model.")

        # Initialize
        Cluster_Dict = {}
        for zoneName in Model_DictOfZonesProperties.keys():
            zone_type, zone_sub, zone_floor, zone_id = zoneName.split("-")
            
            # X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X
            # Clustering definition is mainly done here X°X°X°X°X°X°X°X°X°X°X°X
            cluster = zone_sub + "_" + zone_floor     # X°X°X°X°X°X°X°X°X°X°X°X
            # X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X
            
            Cluster_Dict[cluster] = {}
            Cluster_Dict[cluster]["MODEL_SURFACE"] = 0.0
            Cluster_Dict[cluster]["BUILDING_SURFACE"] = 0.0

        # Get list of spacetype
        ListSpacetype = []
        for  SpacetypeCategory in c.DictSpacetype.keys():
            for SpacetypeItem in c.DictSpacetype[SpacetypeCategory].keys(): 
                if SpacetypeItem not in ListSpacetype:
                    ListSpacetype.append(SpacetypeItem)

        # Get cluster MODEL_SURFACE
        for zoneName in Model_DictOfZonesProperties.keys():
            # Get cluster
            zone_type, zone_sub, zone_floor, zone_id = zoneName.split("-")
            
            # X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X
            # Clustering definition is mainly done here X°X°X°X°X°X°X°X°X°X°X°X
            cluster = zone_sub + "_" + zone_floor     # X°X°X°X°X°X°X°X°X°X°X°X
            # X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X

            # Save zone'cluster in zone properties
            Model_DictOfZonesProperties[zoneName]["ClusterName"] = cluster

            # Get Cluster MODEL_SURFACE
            Cluster_Dict[cluster]["MODEL_SURFACE"] += Model_DictOfZonesProperties[zoneName]["Surface"]

        # Get cluster BUILDING_SURFACE
        for row_index in Building_SurfaceDetails.index:
            for col_index in ListSpacetype:
                # Get cluster infos
                row_sub   = Building_SurfaceDetails.loc[row_index, "SubBuilding"]
                row_floor = Building_SurfaceDetails.loc[row_index, "Floor"]
                cluster = row_sub + "_" + row_floor      

                if cluster in Cluster_Dict.keys():
                    Cluster_Dict[cluster]["BUILDING_SURFACE"] += Building_SurfaceDetails.loc[row_index, col_index]
                else:
                    logger.warning("Missing cluster for "+ cluster)

        # Check for clusters inconstitencies
        for cluster in Cluster_Dict.keys():
            sb = Cluster_Dict[cluster]["BUILDING_SURFACE"]
            sm = Cluster_Dict[cluster]["MODEL_SURFACE"]
            if (sb>0 and sm==0):
                logger.critical("> Missing cluster ["+cluster+"] in selected model ("+chosen_model+")")
            if (sb==0 and sm>0):
                logger.warning("Unused cluster  ["+cluster+"] in selected model ("+chosen_model+")")
        
        # ----------------------------------------------------------------------------------------
        # 1.3 Loads calcul -----------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------
        # Get Clusters loads
        Cluster_Dict = _GetClusterLoads(Cluster_Dict, Model_Loads, Model_DictOfZonesProperties)

        # Scaling up to Building Loads
        Building_Loads, Building_Surface = _GetBuildingLoads(Cluster_Dict, Model_Loads)
        
        # Update Site Loads
        Site_Loads, Site_Surface = _UpdateSiteLoads(Model_Loads, Site_Loads, Site_Surface, Building_Loads, Building_Surface)

        # Update Spacetype Loads
        Spacetype_Loads, Spacetype_Surface = _UpdateSpacetypeLoads(Model_Loads, Model_DictOfZonesProperties, Spacetype_Loads, Spacetype_Surface)

        _GetSurfacicZoneLoads(c=c, Model_Loads=Model_Loads, Model_DictOfZonesProperties=Model_DictOfZonesProperties  )
        # ----------------------------------------------------------------------------------------
        # 1.4 Saving building data ---------------------------------------------------------------
        # ----------------------------------------------------------------------------------------        
        # Save stats file
        BuildingSurfaceSeries = pd.Series(data=[Building_Surface]*len(Building_Loads.keys()), index=Building_Loads.keys())
        _print_stats(Building_Loads, c=c, file="BUILDING"+c.psep+current_building+ ".csv", SurfaceSerie=BuildingSurfaceSeries)
        
        # Save loads file
        pd.DataFrame(Building_Loads).to_csv(c.path_OutputLOADS + "LOADS"+c.psep+ current_building + ".csv", index=False)
    
    # ============================================================================================
    # 2/ Saving Site & Spacetype data ============================================================
    # ============================================================================================
    logger.info("> Starting {2/ Saving Site & Spacetype data}")

    # Save Spacetype stats files
    for spacetype in Spacetype_Loads.keys():
        SpacetypeSurfaceSerie = pd.Series(data=[Spacetype_Surface[spacetype]]*len(Spacetype_Loads[spacetype].keys()), index=Spacetype_Loads[spacetype].keys())
        _print_stats(Spacetype_Loads[spacetype], c=c, file="SPACETYPE"+c.psep+spacetype+ ".csv", SurfaceSerie=SpacetypeSurfaceSerie)

    # Save Site stats files
    SiteSurfaceSerie = pd.Series(data=[Site_Surface]*len(Site_Loads.keys()), index=Site_Loads.keys())
    _print_stats(Site_Loads, c=c, file="SITE"+c.psep+"STATISTICS.csv", SurfaceSerie=SiteSurfaceSerie)

def scaling_tailored(c):
    """
    Given the path_OutputSIM, will check for every model the presence of CSV files. 
    If any CSV file is found, then scaling up methods are started.
    
    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.   
    """
    # ============================================================================================
    # 0/ Initialize ==============================================================================
    # ============================================================================================
    logger.info("> Starting {0/ Initialize}")

    # Get list of deckDir to look for
    deckList = c.models
    # Load all Models data
    DictOf_Model_Loads, DictOf_Model_DictOfZonesProperties = _ModelsLoader(c, deckList)

    # Initialize Site
    Site_Loads, Site_Surface = pd.DataFrame({"TIME": list(range(8760))}), 0.0
    
    # Initialize Spacetype
    Spacetype_Loads, Spacetype_Surface = {}, {}
    for S in c.DictSpacetype.values():
        for s in S.keys():
            Spacetype_Loads[s], Spacetype_Surface[s]  = pd.DataFrame({"TIME": list(range(8760))}), 0.0
    
    # ============================================================================================
    # 1/ Sizing Algorithm ========================================================================
    # ============================================================================================
    logger.info("> Starting {1/ Sizing Algorithm}")
    
    # Sizing algorithm for each file
    for current_building in os.listdir(c.path_GeneratedSurfaceRecap):  
        
        current_building = current_building.split(".csv")[0]
        logger.info("---------------------------------------------------")
        logger.info(" ::::: " + current_building + " ::::: ")

        # ----------------------------------------------------------------------------------------
        # 1.0 Building data ----------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------
      
        try:
            Building_SurfaceDetails = pd.read_csv(c.path_GeneratedSurfaceRecap + current_building + ".csv" , skipinitialspace=True, index_col="Name")
            Building_SurfaceDetails.fillna(0.0, inplace=True)
        except: 
            logger.critical("No surface recap found for file "+current_building+". Surface recap files should contains Total surfaces and central weight for each SubBuilding of real building represented by the model. Check path: "+ c.path_GeneratedSurfaceRecap +"_"+current_building+".csv")  
        
        # ----------------------------------------------------------------------------------------
        # 1.1 Load files -------------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------
        Tailored_push = 0
        TailoredBuilding = "default"

        # 1/ Get booleans for surface categories
        if Tailored_push == 0:
            try:    is_res = (sum(Building_SurfaceDetails["R"]) > 0)
            except: is_res = False
            try:    is_com = (sum(Building_SurfaceDetails["C"]) > 0)
            except: is_com = False
            try:    is_bur = (sum(Building_SurfaceDetails["B"]) > 0)
            except: is_bur = False
            try:    is_ins = (sum(Building_SurfaceDetails["I"]) > 0)
            except: is_ins = False
            try:    is_sch = (sum(Building_SurfaceDetails["Ecole"]) > 0)
            except: is_sch = False
            try:    is_gym = (sum(Building_SurfaceDetails["Gym"]) > 0)
            except: is_gym = False
            try:    is_the = (sum(Building_SurfaceDetails["Theatre"]) > 0)
            except: is_the = False
            try:    is_wor = (sum(Building_SurfaceDetails["Atelier"]) > 0)
            except: is_wor = False
            try:    is_lib = (sum(Building_SurfaceDetails["Bibliotheque"]) > 0)
            except: is_lib = False
            # Mixt building .
            is_mix = (int(is_res) + int(is_com) + int(is_bur) + int(is_the) + int(is_sch) + int(is_gym) + int(is_wor) + int(is_lib))
        # 2/ Deciding which tailored model to use based on building used spacetype
        if is_mix == 1:
            Tailored_push += 1
            if is_sch: TailoredBuilding = "TECOLE"
            if is_gym: TailoredBuilding = "TGYM"
            if is_bur: TailoredBuilding = "TBUREAUX"
            if is_wor: TailoredBuilding = "TATELIER"
            if is_res: TailoredBuilding = "TRESID"
            if is_the: TailoredBuilding = "TTHEATRE"
            if is_lib: TailoredBuilding = "TLIBRARY"
            if is_com: pass
        else: 
            if is_res and is_com and is_the and not is_gym:
                TailoredBuilding = "TMIXT_CB_CV_CT"
                Tailored_push += 1
            elif is_res and is_com and is_gym and not is_the:
                TailoredBuilding = "TMIXT_CB_CV_CG"
                Tailored_push += 1
            elif is_res and is_com and not is_gym and not is_the:
                TailoredBuilding = "TMIXT_CB_CV"
                Tailored_push += 1
            elif is_res and is_com and is_gym and is_the:
                TailoredBuilding = "TMIXT_CB_CV_CG_CT"
                Tailored_push += 1
            elif (is_com or is_lib) and is_sch:
                TailoredBuilding = "TINST"
                Tailored_push += 1
            else:
                pass

        # 3/ Load zoneAttr file of used tailored model
        # Raise error
        if Tailored_push == 0:
            logger.critical("No tailored building seems to be compatible for: "+current_building + "  /  " + TailoredBuilding)
        if Tailored_push > 1:
            logger.critical("Trying to push several tailored building on: "+current_building)
        
        # Chose Model
        logger.info(">> Choosing "+ TailoredBuilding+" for " + current_building)
        chosen_model  = TailoredBuilding
        
        # Get Model data
        Model_Loads = DictOf_Model_Loads[chosen_model]
        Model_DictOfZonesProperties = DictOf_Model_DictOfZonesProperties[chosen_model]
        
        # ----------------------------------------------------------------------------------------
        # 1.2 Cluster definition for sizing algorithm --------------------------------------------
        # ----------------------------------------------------------------------------------------
        logger.info(">> Start scaling algorithm for " + current_building + ". Using "+chosen_model+" as load model.")

        Cluster_Dict = {}
        list_spacetype_in_model, list_model_floor = [], []
        
    
        # Initialize
        for zoneName in Model_DictOfZonesProperties.keys():
            zone_type, zone_sub, zone_floor, zone_id = zoneName.split("-")
            spacetype = Model_DictOfZonesProperties[zoneName]["Spacetype"]["Name"]
            cluster = spacetype + "_" + zone_floor
            Cluster_Dict[cluster] = {}
            Cluster_Dict[cluster]["MODEL_SURFACE"] = 0.0
            Cluster_Dict[cluster]["BUILDING_SURFACE"] = 0.0
            if spacetype not in list_spacetype_in_model:
                list_spacetype_in_model.append(spacetype)
            if zone_floor not in list_model_floor:
                list_model_floor.append(zone_floor)

        # Get list spacetype
        ListSpacetype = []
        for  SpacetypeCategory in c.DictSpacetype.keys():
            for SpacetypeItem in c.DictSpacetype[SpacetypeCategory].keys(): 
                if SpacetypeItem not in ListSpacetype:
                    ListSpacetype.append(SpacetypeItem)
           
        # Get clusters MODEL_SURFACE
        for zoneName in Model_DictOfZonesProperties.keys():
            # Get cluster
            zone_type, zone_sub, zone_floor, zone_id = zoneName.split("-")
            spacetype = Model_DictOfZonesProperties[zoneName]["Spacetype"]["Name"]

            # X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X
            # Clustering definition is mainly done here X°X°X°X°X°X°X°X°X°X°X°X
            cluster = spacetype + "_" + zone_floor    # X°X°X°X°X°X°X°X°X°X°X°X
            # X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X°X

            # Save zone'cluster in zone properties
            Model_DictOfZonesProperties[zoneName]["ClusterName"] = cluster
            Model_DictOfZonesProperties[zoneName]["nbZoneInCluster"] = 0
    
            # Get Cluster MODEL_SURFACE
            Cluster_Dict[cluster]["MODEL_SURFACE"] += Model_DictOfZonesProperties[zoneName]["Surface"]

        # Remove doubles in list checkers
        list_model_floor = list(dict.fromkeys(list_model_floor))        
        list_spacetype_in_model = list(dict.fromkeys(list_spacetype_in_model))
        
        # Get clusters building surface
        for row_index in Building_SurfaceDetails.index:
            for col_index in ListSpacetype:
                # Get corresponding cluster
                floor =  Building_SurfaceDetails.loc[row_index, "Floor"]
                cluster = col_index + "_" + floor
                
                # If floor not in model, choose Fstack by default
                if floor not in list_model_floor:
                    cluster = col_index+"_Fstack"

                # Get cluster only if surface isn't null for said spacetype/floor
                if float(Building_SurfaceDetails.loc[row_index, col_index])>0:
                    if cluster in Cluster_Dict.keys():
                        Cluster_Dict[cluster]["BUILDING_SURFACE"] += float(Building_SurfaceDetails.loc[row_index, col_index])
                    else:
                        logger.warning("Missing cluster for "+ cluster)
        
        # Check for clusters inconstitencies
        for row_index in Building_SurfaceDetails.index:
            for col_index in Building_SurfaceDetails.columns:
                if (col_index not in list_spacetype_in_model) and (col_index not in ["R","C", "B", "P", "I", "RC", "BC", "IA", "IB", "IE", "CB", "CC", "CG", "CT", "TIME", "Floor", "EndUse", "Name", "SubBuilding", "Building", "NbFloor", "Weight"]) and (Building_SurfaceDetails.loc[row_index, col_index] > 0):
                    logger.critical("> Missing cluster spacetype ["+col_index+"] in selected model ("+chosen_model+")")

        
        for cluster in Cluster_Dict.keys():
            sb = Cluster_Dict[cluster]["BUILDING_SURFACE"]
            sm = Cluster_Dict[cluster]["MODEL_SURFACE"]
            if (sb>0 and sm==0):
                logger.critical("> Missing cluster ["+cluster+"] in selected model ("+chosen_model+")")
            if (sb==0 and sm>0):
                logger.info("Unused cluster  ["+cluster+"] in selected model ("+chosen_model+")")
        
        # ----------------------------------------------------------------------------------------
        # 1.3 Loads calcul -----------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------
        # Get Clusters loads
        Cluster_Dict = _GetClusterLoads(Cluster_Dict, Model_Loads, Model_DictOfZonesProperties)

        # Scaling up to Building Loads
        Building_Loads, Building_Surface = _GetBuildingLoads(Cluster_Dict, Model_Loads)
        
        # Update Site Loads
        Site_Loads, Site_Surface = _UpdateSiteLoads(Model_Loads, Site_Loads, Site_Surface, Building_Loads, Building_Surface)

        # Update Spacetype Loads
        Spacetype_Loads, Spacetype_Surface = _UpdateSpacetypeLoads(Model_Loads, Model_DictOfZonesProperties, Spacetype_Loads, Spacetype_Surface)

        # ----------------------------------------------------------------------------------------
        # 1.4 Saving building data ---------------------------------------------------------------
        # ----------------------------------------------------------------------------------------        
        # Save stats file
        BuildingSurfaceSeries = pd.Series(data=[Building_Surface]*len(Building_Loads.keys()), index=Building_Loads.keys())
        _print_stats(Building_Loads, c=c, file="BUILDING"+c.psep+current_building+ ".csv", SurfaceSerie=BuildingSurfaceSeries)
        
        # Save loads file
        pd.DataFrame(Building_Loads).to_csv(c.path_OutputLOADS + "LOADS"+c.psep + current_building + ".csv", index=False)
    
    # ============================================================================================
    # 2/ Saving Site & Spacetype data ============================================================
    # ============================================================================================
    logger.info("> Starting {2/ Saving Site & Spacetype data}")

    # Save Spacetype stats files
    for spacetype in Spacetype_Loads.keys():
        SpacetypeSurfaceSerie = pd.Series(data=[Spacetype_Surface[spacetype]]*len(Spacetype_Loads[spacetype].keys()), index=Spacetype_Loads[spacetype].keys())
        _print_stats(Spacetype_Loads[spacetype], c=c, file="SPACETYPE"+c.psep+spacetype+ ".csv", SurfaceSerie=SpacetypeSurfaceSerie)

    # Save Site stats files
    SiteSurfaceSerie = pd.Series(data=[Site_Surface]*len(Site_Loads.keys()), index=Site_Loads.keys())
    _print_stats(Site_Loads, c=c, file="SITE"+c.psep+"STATISTICS.csv", SurfaceSerie=SiteSurfaceSerie)

def scaling_energyplus(c):
    """
    Given the path_OutputSIM, will check for every model the presence of CSV files. 
    If any CSV file is found, then scaling up methods are started.
    
    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.   
    """

    # ============================================================================================
    # 0/ Initialize ==============================================================================
    # ============================================================================================
    logger.info("> Starting {0/ Initialize}")

    # Get list of deckDir to look for
    deckList = c.models
  
    # Load all Models data
    DictOf_Model_Loads, DictOf_Model_DictOfZonesProperties = _ModelsLoader(c, deckList)
    Model_DictOfZonesProperties = {}
    Model_Loads = {}

    for item in DictOf_Model_DictOfZonesProperties.keys():
        
        # Get current zone dict renamed
        current_Model_DictOfZonesProperties = DictOf_Model_DictOfZonesProperties[item]
        for k in current_Model_DictOfZonesProperties.keys():
            new_k = item +"__"+ k
            Model_DictOfZonesProperties[new_k] = current_Model_DictOfZonesProperties[k]

        # Get current model_Loads renamed
        current_Model_Loads =DictOf_Model_Loads[item]
        for KEY in current_Model_Loads.keys():
            colnew = ["TIME"]
            for col in current_Model_Loads[KEY].columns.difference(["TIME"]):
                colnew.append(item+"__"+col)
            current_Model_Loads[KEY].columns = colnew
            del current_Model_Loads[KEY]['TIME']

            try: Model_Loads[KEY] = pd.concat([Model_Loads[KEY], current_Model_Loads[KEY]], axis=1)
            except: 
                Model_Loads[KEY] = pd.DataFrame({"TIME": list(range(8760))})
                Model_Loads[KEY] = pd.concat([Model_Loads[KEY], current_Model_Loads[KEY]], axis=1)

    # Initialize Site
    Site_Loads, Site_Surface = pd.DataFrame({"TIME": list(range(8760))}), 0.0
    
    # Initialize Spacetype
    Spacetype_Loads, Spacetype_Surface = {}, {}
    for S in c.DictSpacetype.values():
        for s in S.keys():
            Spacetype_Loads[s], Spacetype_Surface[s]  = pd.DataFrame({"TIME": list(range(8760))}), 0.0
    
    # ============================================================================================
    # 1/ Sizing Algorithm ========================================================================
    # ============================================================================================
    logger.info("> Starting {1/ Sizing Algorithm}")
  
    # Sizing algorithm for each file
    for current_building in os.listdir(c.path_GeneratedSurfaceRecap):  
        
        current_building = current_building.split(".csv")[0]
        logger.info("---------------------------------------------------")
        logger.info(" ::::: " + current_building + " ::::: ")

        # ----------------------------------------------------------------------------------------
        # 1.0 Building data ----------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------
      
        try:
            Building_SurfaceDetails = pd.read_csv(c.path_GeneratedSurfaceRecap + current_building + ".csv" , skipinitialspace=True, index_col="Name")
            Building_SurfaceDetails.fillna(0.0, inplace=True)
        except: 
            logger.critical("No surface recap found for file "+current_building+". Surface recap files should contains Total surfaces and central weight for each SubBuilding of real building represented by the model. Check path: "+ c.path_GeneratedSurfaceRecap +"_"+current_building+".csv")  
        
        # ----------------------------------------------------------------------------------------
        # 1.1 Model data ----------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------
        # Nothing

        # ----------------------------------------------------------------------------------------
        # 1.2 Cluster definition for sizing algorithm --------------------------------------------
        # ----------------------------------------------------------------------------------------
        logger.info(">> Start scaling algorithm for " + current_building + ". Using prototype models.")
        
        # Initialize
        Cluster_Dict = {}
        dict_spacetype = {
                "Bureaux": "DOE_Office", "BureauxCouloir": "DOE_Office",
                "Habitation": "DOE_Resid", "HabitationCouloir": "DOE_Resid",
                "Commerce": "DOE_Mall", "Restauration": "DOE_Resto", "Parking": "DOE_Parking", "Gym":"DOE_Mall",
                "Atelier": "DOE_School", "Ecole": "DOE_School", "Theatre": "DOE_School", "Bibliotheque": "DOE_School",
            } 
        
        for zoneName in Model_DictOfZonesProperties.keys():
            cluster = zoneName.split("__")[0]
            Cluster_Dict[cluster] = {}
            Cluster_Dict[cluster]["MODEL_SURFACE"] = 0.0
            Cluster_Dict[cluster]["BUILDING_SURFACE"] = 0.0
        
        # Get clusters MODEL_SURFACE
        for zoneName in Model_DictOfZonesProperties.keys():
            cluster = zoneName.split("__")[0]
            Model_DictOfZonesProperties[zoneName]["ClusterName"] = cluster
            Cluster_Dict[cluster]["MODEL_SURFACE"] += Model_DictOfZonesProperties[zoneName]["Surface"]

        # Get clusters BUILDING_SURFACE
        for row_index in Building_SurfaceDetails.index:
            for col_index in Building_SurfaceDetails.columns:
                if col_index in dict_spacetype.keys():
                    Cluster_Dict[dict_spacetype[col_index]]["BUILDING_SURFACE"] += Building_SurfaceDetails.loc[row_index, col_index]


        # Check for surface mismatch between building and model
        for cluster in Cluster_Dict.keys():
            sb = Cluster_Dict[cluster]["BUILDING_SURFACE"]
            sm = Cluster_Dict[cluster]["MODEL_SURFACE"]
            if (sb>0 and sm==0):
                logger.critical("> Missing cluster ["+cluster+"] in selected model ("+current_building+")")
            if (sb==0 and sm>0):
                logger.info("Unused cluster  ["+cluster+"] in selected model ("+current_building+")")
        
        # ----------------------------------------------------------------------------------------
        # 1.3 Loads calcul -----------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------
        
        # Get clusters LOADS
        Cluster_Dict = _GetClusterLoads(Cluster_Dict, Model_Loads, Model_DictOfZonesProperties)

        # Scaling up to Building Loads
        Building_Loads, Building_Surface = _GetBuildingLoads(Cluster_Dict, Model_Loads)
        
        # Update Site Loads
        Site_Loads, Site_Surface = _UpdateSiteLoads(Model_Loads, Site_Loads, Site_Surface, Building_Loads, Building_Surface)

        # Update Spacetype Loads
        Spacetype_Loads, Spacetype_Surface = _UpdateSpacetypeLoads(Model_Loads, Model_DictOfZonesProperties, Spacetype_Loads, Spacetype_Surface)

        # ----------------------------------------------------------------------------------------
        # 1.4 Saving building data ---------------------------------------------------------------
        # ----------------------------------------------------------------------------------------        
        # Save stats file
        BuildingSurfaceSeries = pd.Series(data=[Building_Surface]*len(Building_Loads.keys()), index=Building_Loads.keys())
        _print_stats(Building_Loads, c=c, file="BUILDING"+c.psep+current_building+ ".csv", SurfaceSerie=BuildingSurfaceSeries)
        
        # Save loads file
        pd.DataFrame(Building_Loads).to_csv(c.path_OutputLOADS + "LOADS"+c.psep + current_building + ".csv", index=False)
    
    # ============================================================================================
    # 2/ Saving Site & Spacetype data ============================================================
    # ============================================================================================
    logger.info("> Starting {2/ Saving Site & Spacetype data}")

    # Save Spacetype stats files
    for spacetype in Spacetype_Loads.keys():
        SpacetypeSurfaceSerie = pd.Series(data=[Spacetype_Surface[spacetype]]*len(Spacetype_Loads[spacetype].keys()), index=Spacetype_Loads[spacetype].keys())
        _print_stats(Spacetype_Loads[spacetype], c=c, file="SPACETYPE"+c.psep+spacetype+ ".csv", SurfaceSerie=SpacetypeSurfaceSerie)

    # Save Site stats files
    SiteSurfaceSerie = pd.Series(data=[Site_Surface]*len(Site_Loads.keys()), index=Site_Loads.keys())
    _print_stats(Site_Loads, c=c, file="SITE"+c.psep+"STATISTICS.csv", SurfaceSerie=SiteSurfaceSerie)

# ================================================================================
# ================================================================================
# ================================================================================

def Scaling(c):
    """
    Main function for scaling, depending on c.Precision_BLD, will call adapted scaling method. 
    Then use smoothing algorithm.

    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.   
    """    
    if c.Precision_BLD=="detailed":
        scaling_detailed(c)

    elif c.Precision_BLD=="tailored":
        scaling_tailored(c)

    elif c.Precision_BLD=="prototype":
        scaling_energyplus(c)

    else: 
        scaling_tailored(c)

    # Smoothing
    smoothing(c)
