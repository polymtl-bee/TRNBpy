# Packages
import os
import json
import shutil

# ----- Class containing parameters of tools -----

class ClassConfiguration:
    """
    A class that contains all variables and parameters used for the tools.
    Those are the class attributes :

        path_Cwd (str): Path to working directory.
        path_Scenario (str): Main directory containing input folders, and where (by default) will be saved temporary and output dir and files. 

        # Paths to Inputs :
        path_ScenarioB18 (str): Absolute path to input directory used for storing your .b18 structural building files(path_Cwd + \\TRNBpy\\data\\input\\).
        path_SpacetypeJSON (str): Path to spacetype template directory (path_Cwd + \\TRNBpy\\data\\spacetype\\)
        path_ScheduleHourlyTRNSYS (str):  Path for the CSV schedule file to use for hourly schedules (24 timestep representing 1 day).
        path_ScheduleDailyTRNSYS (str): Path for the CSV schedule file to use for daily schedules (7 timestep representing 1 Week. Each value can be a hourly schedule defined in path_ScheduleHourlyTRNSYS file).
        path_ScheduleAnnualTRNSYS (str): Path for the CSV schedule file to use for annual schedules (8760 timestep representing 1 year. Be careful: if more than 100 different values, prefers using schedule as input. This is mainly for defining seasonality or holidays On\\Off days with integer values).
        path_ScheduleInput (str): Path for the CSV schedule file to use for input schedules (8760 timestep representing 1 year. Can be complex and long schedule with lot of different float values).
        
        # Paths to Temporary
        path_Temporary (str): Path to the main temporary dircertory. Default is (_temporary\\)
        path_SpacetypeJSON_updated (str): Path for saving and loading complete spacetype (spacetype archetypes with added schedule definition) 
        path_AttributionFile (str): Path of directories wwhere to save and load the csv files of spacetype attribution.
        path_SurfaceRecap (str): Path to save and load a surface recap file, with all surfaces by building. It is helkpful for scaling up models.
        path_ScheduleAnnualInputFile  Path for the annual schedule input generated from Weekday, saturday and sunday daily schedule.

        # Paths to Output
        path_OutputSIM (str): Path to output directory to stored .b18 full building file (structural and spacetype hypothesis). Default is (path_Cwd + \\TRNBpy\\data\\output\\)
        path_OutputSIM (str): Path for saving deck files generated for running each building file. Default is (path_Cwd + \\TRNBpy\\data\\outputDCK\\).
        path_OutputLOADS (str): Path for saving .csv loads files obtained after running TRNSYS simulation for each deck file. Default is (path_Cwd + \\TRNBpy\\data\\outputLOADS\\).
        
        # Paths to Template
        path_Meteo (str) : Path to meteo file for trnsys simulation (Default at self.path_Cwd  + "\\src\\template\\meteo.epw").
        path_TemplateDECK (str): Path for the template to use when generating deck. See deck generation in the wiki to see how to build a deck template. Default is "path_Cwd + \\src" + self.psep + "template\\template_GetLoads.dck"
        path_JSONkeyEq (str): Path for JSON template key equivalence file. This is used to navigate in JSON data between spacetype JSON data and building JSON data. (path_Cwd + \\TRNBpy\\src" + self.psep + "dataTemplate.json)
        
        # Variables and others
        path_TRNSYS_EXE (str): Path to the executable trnsys file to start a simulation (beta).
        schedKEY (str): A string of the common identifier found a the begening of every schedule name. Used for importing only specific columns from CSV file.
        targetkey_ZONE (str): String identifier of ZONE dependant variable name in JSON spacetype
        targetkey_INPUT (str): String identifier of INPUT schedule in shcedule name and type in json spacetype.
        DictOutput (dict): After loading schedule input CSV in Step 1, this variable will store the name of each schedule.
        keys (dict): a dictionary of key equivalence between path_JSONkeyEq and building JSON definition. This is used to navigate in JSON data between spacetype JSON data and building JSON data.
    """

    def __init__(self, scenarioName, Precision_BLD, Precision_EXP, Precision_THN):
        
        self.psep =  "\\" 
        # Path to current working directory
        self.path_Cwd = os.getcwd() + self.psep

        # Paths to project input data :
        self.path_Scenario = self.path_Cwd + scenarioName
        
        # ============================================================================
        # DECK GENERATION ============================================================
        # ============================================================================
        # Precision levels
        self.Precision_BLD = Precision_BLD
        self.Precision_EXP = Precision_EXP

        
        # -----------------------------
        # Input paths -----------------
        # -----------------------------

        # Input directory
        self.path_Input = self.path_Cwd + scenarioName

        # Input sub-directories
        self.path_UsedBuilding_SurfaceDetails  = self.path_Input  + "1_BuildingDescription_CSV" + self.psep  # Path for the template to use when generating deck
        self.path_InputB18          = self.path_Input  + "2_StructuralModels_B18" + self.psep     # Path for the .b18 structural archetype.
        self.path_SpacetypeJSON_raw = self.path_Input  + "3_Spacetype_JSON" + self.psep           # Path for providing spacetype (spacetype archetypes) 

        # Input files
        self.path_ScheduleHourlyTRNSYS     = self.path_Input + "3_Spacetype_JSON" + self.psep    + "HorexHour.csv"     # Path for the template to use when generating deck
        self.path_ScheduleDailyTRNSYS      = self.path_Input + "3_Spacetype_JSON" + self.psep    + "HorexDay.csv"      # Path for the template to use when generating deck
        self.path_ScheduleAnnualTRNSYS     = self.path_Input + "3_Spacetype_JSON" + self.psep    + "HorexAnnual.csv"   # Path for the template to use when generating deck
        self.path_ScheduleInputFile        = self.path_Input + "3_Spacetype_JSON" + self.psep    + "SchedulesToInput.csv"  # Path for the template to use when generating deck
  
        # Buildings 
        self.buildings = []
        for b in next(os.walk(self.path_UsedBuilding_SurfaceDetails), (None, None, []))[2]:
            self.buildings.append(b[:-4])
        self.models = []
        for b in next(os.walk(self.path_InputB18), (None, None, []))[2]:
            self.models.append(b[:-4])
        """
        self.buildings = ["5B", "4B"]
        """

        print("Step 0 - Modeles etudies: "+str(self.models))

        # -----------------------------
        # Output paths ----------------
        # -----------------------------

        # Output directory
        self.path_Output = self.path_Scenario + "4_Output" + self.psep                           

        # Output sub-directories
        self.path_OutputSIM         = self.path_Output  + "SimulationPack" + self.psep       # Path for saving deck files.
        self.path_OutputSCH         = self.path_Output  + "SimulationPack" + self.psep + "CSV_Schedules" + self.psep # Path for the template to use when generating deck"
        self.path_OutputLOADS       = self.path_Output  + "CSV_Loads" + self.psep            # Path for saving csv loads files

        # Output make directories
        os.makedirs(self.path_OutputSIM, exist_ok=True)
        os.makedirs(self.path_OutputSIM, exist_ok=True)
        os.makedirs(self.path_OutputLOADS, exist_ok=True)
        os.makedirs(self.path_OutputLOADS+"LOADS" + self.psep, exist_ok=True)
        os.makedirs(self.path_OutputLOADS+"SITE" + self.psep, exist_ok=True)
        os.makedirs(self.path_OutputLOADS+"BUILDING" + self.psep, exist_ok=True)
        os.makedirs(self.path_OutputLOADS+"SPACETYPE" + self.psep, exist_ok=True)
        os.makedirs(self.path_OutputLOADS+"ZONESSURF" + self.psep, exist_ok=True)
        
        self.DictSIMpath = {}
        for b in self.models:
            os.makedirs(self.path_OutputSIM + b + "" + self.psep, exist_ok=True)
            self.DictSIMpath[b] = self.path_OutputSIM + b + "" + self.psep
            
        # -----------------------------
        # Temporary paths -------------
        # -----------------------------

        # Temporary directory
        self.path_Temporary = self.path_Scenario + "5_(Temporary)" + self.psep

        # Temporary sub-directories
        self.path_SpacetypeJSON_updated    = self.path_Temporary + "JSON_SpacetypeUpdated" + self.psep          # Path for providing spacetype (spacetype archetypes) 
        self.path_AttributionFile          = self.path_Temporary + "JSON_SpacetypeAttribution" + self.psep      # Path for the csv file of spacetype attribution.
        self.path_GeneratedSurfaceRecap    = self.path_Temporary + "CSV_GeneratedSurfaceRecap" + self.psep              # Path for the template to use when generating deck

        # Temporary file
        self.path_ScheduleAnnualInputFile  = self.path_OutputSIM + "CSV_Schedules" + self.psep + "ScheduleInput.csv" # Path for the template to use when generating deck

        # Temporary make directories
        os.makedirs(self.path_SpacetypeJSON_updated, exist_ok=True)
        os.makedirs(self.path_AttributionFile, exist_ok=True)
        os.makedirs(self.path_OutputSIM + "CSV_Schedules" + self.psep , exist_ok=True)
        os.makedirs(self.path_Temporary + "CSV_GeneratedSurfaceRecap" + self.psep , exist_ok=True)


        # ----------------------------------------------------------------------------
        # Template file paths --------------------------------------------------------
        # ----------------------------------------------------------------------------
        
        self.path_TemplateDECK = self.path_Cwd  + "src" + self.psep + "DCK_Template" + self.psep + "template.dck"      # Path for the template to use when generating deck
        self.path_JSONkeyEq    = self.path_Cwd  + "src" + self.psep + "DCK_Template" + self.psep + "dataTemplate.json" # Path for JSON template key equivalence file
        self.path_Meteo        = self.path_OutputSIM  + "meteo.epw"         # Path to meteo file for trnsys simulation
        shutil.copy(self.path_Cwd  + "src" + self.psep + "DCK_Template" + self.psep + "meteo.epw", self.path_Meteo)
        self.path_TemplateB18_ForSurfaceComposition  = self.path_Cwd  + "src" + self.psep + "DCK_Template" + self.psep + "template.b18" # Path to B18 file where to scrap surface composition

        # -----------------------------
        # Variables -------------------
        # -----------------------------
        

        # Keys dictionnary
        self.keys = {}
    
        # Identification key variables
        self.schedKEY = "horex"               # Used in BuildDeck for identifying if an input is a schedule in the input list (the key must correspond to a part of a schedule name).
        self.targetkey_INPUT = "$INPUT_"   # Used as a in-value identifier to say said value vary with key-following schedule (example: Dhw: {1.4 * $SCHEDULE_ScheduleName})
        self.targetkey_SCHEDULE = "$SCHEDULE_"   # Used as a in-value identifier to say said value vary with key-following schedule (example: Dhw: {1.4 * $SCHEDULE_ScheduleName})
        self.targetkey_ZONE = "$ZONE"         # Used to indicate a zone dependant value. Could be $ZONESURF, $ZONESURFEXT, $ZONEVOLUME...
        
        # Output dictionnary to save (Keys and names are defined using TRNBUILD output convention)
        self.DictOutput = {"29": "ABSHUM", 
                          "30":"QHEAT",
                          "31": "QCOOL",
                          "98": "QDEHUM",
                          "99": "QHUM",
                          "155": "QELLIGHT",
                          "156": "QELEQUIP",
                          "1"  :"TAIR",}
        
        # Probability of occurence of each spacetype depending of the zone type.
        var = {"Habitation":1}
        self.InputFamily = ["horexA", "horexB", "horexC", "horexG", "horexD", "horexK"]

        if Precision_EXP != "determinist":
            var = {"HabitationMoyen":0.35, "HabitationEtudiant":0.15, "HabitationRetraite":0.2, "HabitationTeletravail":0.1, "HabitationFamille":0.2}
            self.InputFamily = ["horexA", "horexB", "horexC", "horexD", "horexK", "horexG", "horexGMoyen", "horexGFami", "horexGEtud", "horexGRetr", "horexGTele"]

        self.DictSpacetype = {
                "P":{"Parking":1},
                "C":{"Restauration":0.4, "Commerce":0.4, "Gym":0.1, "Theatre":0.1}, 
                "CB":{"Restauration":1}, 
                "CC":{"Commerce":1}, 
                "CG":{"Gym":1}, 
                "CT":{"Theatre":1}, 
                "I":{"Atelier":0.1, "Ecole":0.5, "Bibliotheque":0.4}, 
                "IA":{"Atelier":1}, 
                "IE":{"Ecole":1}, 
                "IB":{"Bibliotheque":1},
                "R":var, 
                "RC": {"HabitationCouloir":1}, 
                "B":{"Bureaux":1}, 
                "BC": {"BureauxCouloir":1}, }

        # ============================================================================
        # ADD-ON: THN GENERATION =====================================================
        # ============================================================================

        self.Precision_THN = Precision_THN + self.psep

        # -----------------------------
        # RTh file paths --------------
        # -----------------------------

        # Template THN file
        if Precision_THN == "TopologyReduced":
            self.path_Rth            = self.path_Cwd  + "src" + self.psep + "RTh_Template" + self.psep + "RThReduced.dck"
        else:
            self.path_Rth            = self.path_Cwd  + "src" + self.psep + "RTh_Template" + self.psep + "RTh.dck"

        # Pipe sinzing file
        self.path_Pipefile       = self.path_Scenario + "6_RTh" + self.psep+self.Precision_THN+"input" + self.psep + "pipe.csv"
        
        # Output paths
        self.path_Rth_out        = self.path_Scenario +"6_RTh" + self.psep+self.Precision_THN + self.psep + "RTh_sized.dck"

        # Make paths
        os.makedirs(self.path_Scenario + "6_RTh" + self.psep, exist_ok=True)
        os.makedirs(self.path_Scenario + "6_RTh" + self.psep+self.Precision_THN+"" + self.psep, exist_ok=True)
        os.makedirs(self.path_Scenario + "6_RTh" + self.psep+self.Precision_THN+"input" + self.psep, exist_ok=True)
        shutil.copy(self.path_Cwd  + "src" + self.psep + "RTh_Template" + self.psep + "PerfMap.dat", self.path_Scenario + "6_RTh" + self.psep+self.Precision_THN+"input" + self.psep+"PerfMap.dat")
        shutil.copy(self.path_Cwd  + "src" + self.psep + "RTh_Template" + self.psep + "Typical666ChillerPerformance.dat", self.path_Scenario + "6_RTh" + self.psep+self.Precision_THN+"input" + self.psep+ "Typical666ChillerPerformance.dat")

        # -----------------------------
        # Variables -------------------
        # -----------------------------

        # Rated COP for equipment
        self.PAC_COP_Rated     = 2 
        self.chiller_COP_Rated = 8 

        # Correction ratio from performance map (if wanted operative temperature is different than the operative temperature of performance data)
        # Should be updated if network temperature changes (Heating: Tsupply=75°C and Treturn=45°C \\ Cooling: Tsupply=12°C and Treturn=4°C)
        self.chiller_Capacity_CorrectionRatio = 1.014
        self.chiller_COP_CorrectionRatio = 1.3218
        self.PAC_Cond_CorrectionRatio = 1.52
        self.PAC_Evap_CorrectionRatio = 2.06


    def _load_keys(self):
        """
        This method loads the key equivalence JSON file as a dictionary stored as an attribute.
        """
        with open(self.path_JSONkeyEq) as file:
            self.keys = json.load(file)
