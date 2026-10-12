# import TRNBpy
from src.TRNBby import *

# ===========================================================================
# Preparatory Steps =========================================================
# ===========================================================================

#  Create site data function (used for detailed approach, to generate surfaces of each spacetype for each building, subbuilding, floor)

# Work in progress automated simulation of deck

def Get_c(scenario, Precision_THN):

    if "detailed" in scenario:
        Precision_BLD="detailed"
    elif "archetype" in scenario:
        Precision_BLD="archetype"
    else:
        Precision_BLD="prototype"
    if ("val" in scenario) or ("sch" in scenario) or ("sto" in scenario) or ("tset" in scenario):
        Precision_EXP = "stochastic"
    elif ("var" in scenario):
        Precision_EXP = "variable"
    else:
        Precision_EXP = "determinist"
    
    c = ClassConfiguration(scenarioName=scenario,    # Folder name.  Windows my\\path but Linux my/ 
                       Precision_BLD=Precision_BLD,             # "detailed" - "tailored" - "prototype"
                       Precision_EXP=Precision_EXP,          # "determinist" - "variable" - "stochastic"
                       Precision_THN=Precision_THN)   # "TopologyDetailed" - "TopologyReduced" - "TopologySimplified" 
    c._load_keys()
    return c

def main_1_BuildDCK(c):
    # Step 1: Preparation of spacetype ------------
    logger.info("===============================================")
    logger.info("Step 1 - Preparation of spacetype =============")
    logger.info("===============================================")
    print("Step 1 - Preparation of spacetype")
    sitedatabuilder._loadAllSchedules_InAllSpacetypes(c)
    logger.info(">> All good...")

    # Step 2 : Generate JSON Building file --------
    logger.info("===============================================")
    logger.info("Step 2 - Generate JSON Building file ==========")
    logger.info("===============================================")
    print("Step 2 - Generate JSON Building file")
    jsonbuilder._BuildJSONFile(c)
    logger.info(">> All good...")

    # Step 3 : Noise generation -------------------
    logger.info("===============================================")
    logger.info("Step 3 - Noise generation =====================")
    logger.info("===============================================")
    print("Step 3 - Noise generation: For non-deterministic approaches, add noise & variability to some values")
    noisebuilder.noise(c)
    logger.info(">> All good...")

    # Step 4 : Generate DECK Building file --------
    logger.info("===============================================")
    logger.info("Step 4 - DECK Generation ======================")
    logger.info("===============================================")
    print("Step 4.1 - Convert JSON Building file to B18")
    convert.convert_FromJSON_ToB18(c)

    print("Step 4.2 - Deck generation")
    deckbuilder.generate_AllDeckForSimulations(c)
    logger.info(">> All good...")

def main_2_SimmulateModels(c):
    """
    """
    logger.info("STARTING STEP 3 ===========================")
    logger.info("RUNNING TRNSYS SIMULATION FOR EACH BUILDING")
    logger.info("===========================================")

    # 2) Running TRNSYS simulation
    trnsys_path =r"C:/Trnsys18/Exe/TRNExe64.exe"
    dck_path = c.path_OutputDCK + "5B/5B.dck"
    
    relpath_to_deck = os.path.relpath(c.path_OutputDCK, c.path_Cwd)


    
    print(relpath_to_deck)
    
    start_time=time.time()                    # Measuring time (start point)
    commande = [trnsys_path, dck_path,"/h"]   # Command to run TRNSYS 
    subprocess.run(commande, shell=True)      # Run simulation
    elapsed_time = time.time() - start_time   # Measuring time (end point)
    logger.info("Ran TRNSYS Simulation of "+ dck_path +" in "+ str(elapsed_time))
    
    """
    # 2) Running TRNSYS simulation
    start_time=time.time()                  # Measuring time (start point)
    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/bin:/usr/bin/wine:/opt/wine-staging/bin:" + env.get("PATH", "")
    
    # WINE & TRNSYS path
    wine_path = r'/home/gmlow/.wine/drive_c/TRNSYS18/Exe/'
    trnsys_file = r'TrnEXE64.exe'

    # File Path
    work_path = c.path_Cwd
    work_file = r"data/detailed2/4_Output/DCK_DeckTrnsys/10C/"
    work_obje = r"10C_1.dck"
    shutil.copy(work_path+work_file+work_obje, wine_path+work_obje)

    # Get relative paths
    commande_1 = r"cd " + wine_path
    commande_2 = r';ls ; winetricks ; exec env WINEPREFIX="/home/gmlow/.wine" wine64 ' + trnsys_file
    commande_3 = r"; wine64 /home/gmlow/.wine/drive_c/ProgramData/Microsoft/Windows/StartMenu/Programs/TRNSYS18/TRNEXE.lnk"
    commande = commande_1 + commande_3

    # New
    relpath_to_deck = os.path.relpath(c.path_OutputDCK, c.path_Cwd)
    path_to_file = relpath_to_deck + "10C/10C_1.dck"

    subprocess.run(commande, shell=True, env=env)    # result = subprocess.run([wine_path, path], capture_output=True, text=True)

    # os.system(r"cd " + os.path.relpath(common_path, work_path) + " ; " + wine_path + " " + work_path)    # result = subprocess.run([wine_path, path], capture_output=True, text=True)

    elapsed_time = time.time() - start_time # Measuring time (end point)
    logger.info(str(elapsed_time))
    """

def main_3_BuildBuildingLoads(c):
    # Step 6 : Scaling up ----------------------
    logger.info("===============================================")
    logger.info("Step 6 - Load Builder =========================")
    logger.info("===============================================")
    print("Step 6 - Load builder: Start scaling from model to building loads")
    loadbuilder.Scaling(c)
    logger.info(">> All good...")

def main_4_BuildThermalNetworkDCK(c):
    # Step 7 : Pipe sizing & cluster loads ------
    # As of now:
    # - Copy&Paste loads in "data/scenarioName/4_Output/CSV_loads/LOADS/" to a "data/scenarioName/" directory in PipeSizingTool_v2.1.
    # - Verify parameters and THN definition in tool.
    # - Run PipeSizingTool_v2.1.
    # - Copy&Paste cluster files from "output/scenarioName/" in PipeSizingTool_v2.1 to "data/scenarioName/6_RTh/input/" in TRNBpy.
    # - Copy&Paste Pipes file "output/scenarioName/Pipe sizing results - Equivalents.csv" in PipeSizingTool_v2.1 to "data/scenarioName/6_RTh/sizing/" in TRNBpy.

    # Step 8 : Update THN deck file ------------
    logger.info("===============================================")
    logger.info("Step 8 - THN Generation =======================")
    logger.info("===============================================")
    print("Step 8 - THN Builder: Update THN deck file with equipment and pipe sizing.")
    thnbuilder.update_RTh(c)
    logger.info(">> All good...")

    # Step 9 : Simulate THN --------------------
    # As of now: 
    # - Open dck file "data/scenarioName/6_RTh/RTh_sized.dck" in TrnEdit
    # - Run simulation in TrnEdit

"""sitedatabuilder._make_Site(c)"""
"""NamurSiteBuilder_v2(c)"""
"""sitedatabuilder._make_Buildings(c)"""
"""main_3_SimmulateModels(c)"""

# ===========================================================================
# Main workflow =============================================================
# ===========================================================================

# Step 0 : Config ------------------------------

slist = ["data/RTH_detailed_sto/"]
for s in slist:
    
    print("====== DO FOR "+s+" ========")
    c = Get_c(scenario=s, Precision_THN="TopologyReduced")

    main_1_BuildDCK(c)
    main_2_SimmulateModels(c)
    main_3_BuildBuildingLoads(c)
    main_4_BuildThermalNetworkDCK(c)




    
