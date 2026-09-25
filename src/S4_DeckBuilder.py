# Local
import src._Utils as utils
from src._Logging import logger 
import src._TranslateToB18 as reader
# Lib
import os
import pandas as pd

# ================================================================================
# Intermediate function ==========================================================
# ================================================================================

# ----- Build deck for 1 file -----
def _buildDeck_FromB18(B18_InputPath, c, DCK_TemplatePath, DCK_OutputPathDir, PATH_METEO_FILE, PATH_SCHEDULE_FILE, filename, KEY_sched, KEY_input, PRINTER_MAX_INPUT=75):
    """
    This function allows to update a template Deck file with saved configuration and buildings informations.
    It includes update path to meteo file, path to external schedule file, path to building file.
    It also includes linking all of the building's output to different Type25 in deck file. 
    If maximum number of input is reached, then multiples deck are generated until all outputs are linked to one Type25 input.

    Args:
        B18_InputPath (string): Path to .b18 building file.
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
        DCK_TemplatePath (string): Path to .dck template used to write output in.
        DCK_OutputPathDir (string): Path to output directory where to save updated .dck file.
        PATH_METEO_FILE (string): Relative path to meteo file.
        PATH_SCHEDULE_FILE (string): Relative path to schedule file.
        filename (string): A string containing the name of the output file, without it's extension (.dck).
        schedKEY (string): A string of the common identifier found a the begening of every schedule name. Used for importing only specific columns from CSV file.
        schedFILEUNIT (string): A string of an integer corresponding to the fileUNIT of the CSV (defined in the assign line  of CSV import block).
        PRINTER_MAX_INPUT (int): Maximum number of input allowed per Type25c logger.infoer. If total outputs is greater than PRINTER_MAX_INPUT, multiple deck files will be generated.
    """
    # Get Relative paths ----------------------------------------------------------------------
    PATH_METEO_FILE_REL = os.path.relpath(PATH_METEO_FILE, DCK_OutputPathDir+"file.csv") 
    PATH_B18_REL = os.path.relpath(B18_InputPath, DCK_OutputPathDir+"file.csv")
    
    # Get sublist of schedule -----------------------------------------------------------------
    MAX_SCHED_PER_READER = 95
    schedule_Mainfile = pd.read_csv(PATH_SCHEDULE_FILE)
    TOTAL_SCHED = len(schedule_Mainfile.columns)
    subfile_id=0
    OrderedAsCSVOutput = pd.DataFrame(columns=["SchedName","SchedID", "SchedFile", "SchedLog"])

    while TOTAL_SCHED > 0:
        # Get subcolumns
        subcolumns = list(schedule_Mainfile.columns.difference(["TIME"]))[MAX_SCHED_PER_READER*subfile_id: MAX_SCHED_PER_READER*(subfile_id+1)]
        # Save sub schedule file
        schedule_Mainfile[subcolumns].to_csv(PATH_SCHEDULE_FILE[:-4]+"-"+str(subfile_id)+".csv", index=False)
        logger.info("Saved sub-schedule file - "+PATH_SCHEDULE_FILE[:-4]+"-"+str(subfile_id)+".csv")
        # Append input lists with infos of the subschedule
        for schedIndex in range(0, len(subcolumns)): 
            OrderedAsCSVOutput.loc[MAX_SCHED_PER_READER*subfile_id+schedIndex] = [subcolumns[schedIndex], schedIndex+1,  PATH_SCHEDULE_FILE[:-4]+"-"+str(subfile_id)+".csv", ""]

        # Go to next subfile
        subfile_id+=1
        TOTAL_SCHED -= MAX_SCHED_PER_READER

    with open(DCK_TemplatePath, "r", encoding="iso-8859-1") as dck_file:
        dck_lines = dck_file.readlines()     
    lineNumber_WhereUNIT = utils._checkStr(dck_lines, "UNIT")
    schedReader = -1
    while lineNumber_WhereUNIT != None:
        line = utils._cleanString(dck_lines[lineNumber_WhereUNIT])
        if ("TYPE" in line) and int(utils._cleanString(line.split("TYPE")[1][0:3])) == 9:
            unit = utils._cleanString(line.split("TYPE")[0].split("UNIT")[1])
            schedReader += 1
            for index in OrderedAsCSVOutput.index[MAX_SCHED_PER_READER*schedReader: MAX_SCHED_PER_READER*(schedReader+1)]:
                if index<len(OrderedAsCSVOutput.index):
                    OrderedAsCSVOutput.loc[index, "SchedLog"] = unit
                else:
                    pass
        # Go to next UNIT in file
        lineNumber_WhereUNIT = utils._checkStr(dck_lines, "UNIT", begin=lineNumber_WhereUNIT+2, raise_error=False)

    # Get link to B18 characteristics
    OrderedAsB18Input = pd.DataFrame(columns=["SchedName","SchedID", "SchedFile", "SchedLog"])
    list_input = reader._read_listInput_fromB18(path_b18=B18_InputPath)
    
    for name in list_input:
        # Append sublist of input schedules
        found = 0
        if KEY_sched in name and KEY_input in name:
            for schedIndex in OrderedAsCSVOutput.index:
                if name.replace(KEY_input, "") == OrderedAsCSVOutput.loc[schedIndex, "SchedName"]:
                    found +=1
                    schedName = OrderedAsCSVOutput.loc[schedIndex, "SchedName"]
                    schedId   = OrderedAsCSVOutput.loc[schedIndex, "SchedID"]
                    schedFile = OrderedAsCSVOutput.loc[schedIndex, "SchedFile"]
                    schedLog  = OrderedAsCSVOutput.loc[schedIndex, "SchedLog"]
                    OrderedAsB18Input.loc[schedIndex] = [schedName, schedId, schedFile, schedLog]
        if found > 1:
            logger.critical("Error - Multiples schedules identified for "+name)

    OrderedAsCSVOutput.to_csv( c.path_SpacetypeJSON_updated+filename+"_OrderedAsCSVOutput.csv", index=False)
    OrderedAsB18Input.to_csv(c.path_SpacetypeJSON_updated +filename+ "_OrderedAsB18Input.csv" , index=False)

    # MAIN LOOP FOR EACH FILE ================================================================
    # (multiple file if logger.info max input is reached for each logger.infoer ==============
    
    # Get list outputs -----------------------------------------------------------------------
    list_output = reader._read_listOutput_fromB18(path_b18=B18_InputPath)    
    list_output_id = list(range(1, len(list_output)+1))

    deck_file_nb = 0
    while len(list_output) > 0:

        inputWritten = 0
        schedReader = -1
        # Load dck file ----------------------------------------------------------------------
        with open(DCK_TemplatePath, "r", encoding="iso-8859-1") as dck_file:
            dck_lines = dck_file.readlines()
        
        # ====================================================================================        
        # LOOKING FOR type 9 =================================================================
        # ====================================================================================
        lineNumber_WhereUNIT = utils._checkStr(dck_lines, "UNIT")
        while lineNumber_WhereUNIT != None:
            line = utils._cleanString(dck_lines[lineNumber_WhereUNIT])
            if ("TYPE" in line) and int(utils._cleanString(line.split("TYPE")[1][0:3])) == 9:
                
                # 0. Get number of column to read and schedule relative path
                schedReader += 1
                unit = utils._cleanString(line.split("TYPE")[0].split("UNIT")[1])
                try:
                    PATH_SCHEDULE_FILEi = OrderedAsCSVOutput.loc[MAX_SCHED_PER_READER*schedReader+1, "SchedFile"]
                except:
                    PATH_SCHEDULE_FILEi = OrderedAsCSVOutput.loc[OrderedAsCSVOutput.index[-1], "SchedFile"]
                PATH_SCHEDULE_FILE_RELi = os.path.relpath(PATH_SCHEDULE_FILEi, DCK_OutputPathDir+"file.csv")
                schedule_file = pd.read_csv(PATH_SCHEDULE_FILEi)
                nb_col_to_read = len(schedule_file.columns)

                # 1. Remove parameters for columns
                fcount_parameters = utils._checkStr(dck_lines, "PARAMETERS", begin=lineNumber_WhereUNIT+1, end_string="*** External files")
                cleanline = utils._cleanString(dck_lines[fcount_parameters])
                while "*----------" not in cleanline:
                    dck_lines.pop(fcount_parameters)
                    cleanline = dck_lines[fcount_parameters]
                    if "Logical unit for input file" in cleanline:
                        LogicalUnit = cleanline[:3].replace(" ","")
                
             
                # 3. Add parameters for columns
                nb_freeformat = 4 * (1 + nb_col_to_read) + 2 
                nb_logical_unit = 4 * (1 + nb_col_to_read) + 1 
                dck_lines.insert(fcount_parameters, '*|? Input file name |1000 \n')
                dck_lines.insert(fcount_parameters, 'ASSIGN "' + PATH_SCHEDULE_FILE_RELi +'" '+LogicalUnit  +'\n')
                dck_lines.insert(fcount_parameters, '*** External files \n')
                dck_lines.insert(fcount_parameters, '-1		! '+ str(nb_freeformat) +' Free format mode\n')
                dck_lines.insert(fcount_parameters, LogicalUnit+'		! '+ str(nb_logical_unit) +' Logical unit for input file\n')
                for i in range(1, nb_col_to_read+1):
                    e = nb_logical_unit - i*4
                    f = nb_col_to_read +1 - i 
                    dck_lines.insert(fcount_parameters, '1		! '+ str(e+3) +' Average or instantaneous value-'+str(f)+'\n')
                    dck_lines.insert(fcount_parameters, '0		! '+ str(e+2) +' Addition factor-'+str(f)+'\n')
                    dck_lines.insert(fcount_parameters, '1.0		! '+ str(e+1) +' Multiplication factor-'+str(f)+'\n')
                    dck_lines.insert(fcount_parameters, '1		! '+ str(e) +' Interpolate or not-'+str(f)+'\n')
                dck_lines.insert(fcount_parameters, 'STEP		! 4 Time interval of data \n')
                dck_lines.insert(fcount_parameters, str(nb_col_to_read)+'		! 3 No. of values to read \n')
                dck_lines.insert(fcount_parameters, '1		! 2 Header Lines to Skip \n')
                dck_lines.insert(fcount_parameters, '6		! 1 Mode \n')
                dck_lines.insert(fcount_parameters, 'PARAMETERS ' + str(nb_freeformat) + '\n')
            
            # Go to next UNIT in file
            lineNumber_WhereUNIT = utils._checkStr(dck_lines, "UNIT", begin=lineNumber_WhereUNIT+2, raise_error=False)
        
        if schedReader*MAX_SCHED_PER_READER < len(schedule_Mainfile.columns):
            logger.critical("Not enough reader components for file "+filename+" ; "+str(schedReader)+" * "+str(MAX_SCHED_PER_READER)+" < "+str(len(schedule_Mainfile)))
        

        # ====================================================================================
        # LOOP FOR EACH UNIT ==================================================================
        # ====================================================================================
        lineNumber_WhereUNIT = utils._checkStr(dck_lines, "UNIT")
        while lineNumber_WhereUNIT != None:
            line = utils._cleanString(dck_lines[lineNumber_WhereUNIT])
            if "TYPE" in line:

                # Read unit
                unit_type_id = int(utils._cleanString(line.split("TYPE")[1][0:3]))

                # ----- Type15 - Change meteo file to the current meteo file -----
                if unit_type_id == 15:
                    assign_external_file_fcount =  utils._checkStr(dck_lines, "ASSIGN ", begin=lineNumber_WhereUNIT+1, end_string="*----------------", raise_error=False)
                    dck_lines.pop(assign_external_file_fcount)
                    dck_lines.insert(assign_external_file_fcount, 'ASSIGN "' + PATH_METEO_FILE_REL +'" 31 \n')

                # ----- Change Type56 b18 file to the current building file -----
                if unit_type_id == 56:
                    
                    # Link schedules input to building
                    _link_CSVOutput_as_BuildingInput(dck_lines=dck_lines, list_sched_name=list(OrderedAsB18Input["SchedName"]), list_sched_id=list(OrderedAsB18Input["SchedID"]), schedKEY=KEY_sched,fcounti=lineNumber_WhereUNIT, schedFILEUNIT=list(OrderedAsB18Input["SchedLog"]))

                    # Link to b18_ file
                    assign_external_file_fcount =  utils._checkStr(dck_lines, "ASSIGN ", begin=lineNumber_WhereUNIT+1, end_string="*----------------", raise_error=False)
                    dck_lines.pop(assign_external_file_fcount)
                    dck_lines.insert(assign_external_file_fcount, 'ASSIGN "' + PATH_B18_REL +'" 30 \n')

                # ----- Loop for each TYPE 25 unit (output file) -----
                if unit_type_id == 25:
                        
                        # Raise max input error
                        inputWritten += PRINTER_MAX_INPUT  
                        if inputWritten > 750:
                            logger.critical("Too much input description for deck "+ filename + ". Might result in TRNSYS critical error 308. Please reduce your number of printer, reduce the number of input per printer or change limit in TRNSYS" )

                        # Get list of input to add to this TYPE 25 unit
                        sublist_output = list_output[0:PRINTER_MAX_INPUT]
                        sublist_output_id = list_output_id[0:PRINTER_MAX_INPUT]
                        list_output = list_output[PRINTER_MAX_INPUT:]
                        list_output_id = list_output_id[PRINTER_MAX_INPUT:]

                        # Add input to TYPE 25
                        _link_B18Output_as_printerInput(dck_lines=dck_lines, list_output_name=sublist_output, list_output_id=sublist_output_id, fcount=lineNumber_WhereUNIT)

            # Go to next UNIT in file
            lineNumber_WhereUNIT = utils._checkStr(dck_lines, "UNIT", begin=lineNumber_WhereUNIT+1, raise_error=False)
        
        # ====================================================================================
        # SAVE FILE ==========================================================================
        # ====================================================================================
        deck_file_nb += 1
        with open(c.DictSIMpath[filename]+filename+"_"+str(deck_file_nb)+".dck", "w") as dck_file:
            for line in dck_lines:
                dck_file.writelines(str(line))

# ----- Functions to manipulate DECK -----

def _link_B18Output_as_printerInput(dck_lines, list_output_name, list_output_id, fcount):
    """
    This functions allows one to write TRNSYS links between the outputs of Type56 stored in list_output_name and the inputs of the Type25c where fcount is pointing.
    The list_output_name and list_output_id are sublist extracted from Type56 list of output to make sure this Type25c doesn't have too much inputs.

    Args:
        dck_lines (list-like): a list-like object of a .dck file.
        list_output_name (list): A list of output found in the path_b18 file used by Type56 building model.
        list_output_id (list): Unique ID for each output of list_output_name.
        fcount (int): The line from which to start reading the dck_lines file (i.e. the line of the current Type25c where to write the nexts outputs.)
    """
    fcount = utils._checkStr(dck_lines, "INPUTS",begin=fcount, raise_error=False)

    # Input and initial values labels
    nb_inputs_toRmv = int(dck_lines[fcount].split("INPUTS")[1])
    for i in range(0, nb_inputs_toRmv+1):
            dck_lines.pop(fcount)
        
    dck_lines.insert(fcount, "INPUTS "+str(len(list_output_name))+"\n")
    for i in range(0, len(list_output_id)):
            dck_lines.insert( fcount + 1 + i,"2,"+str(list_output_id[i]) + "\n"  )
             #+" \t\t! building.b18: "+str(list_output_id[i])+"- "+list_output_name[i]+" ->Input to be logger.infoed-"+str(i+1)+ "\n")

    # Add initial values for input -------------------------
    fcount_min =  utils._checkStr(dck_lines, "*** INITIAL INPUT VALUES",begin=fcount, raise_error=False)
    fcount_max =  utils._checkStr(dck_lines, "*** External files",begin=fcount_min, raise_error=False)
    nb_line_to_pop = fcount_max - fcount_min
    # Remove existing initial values
    for i in range(1, nb_line_to_pop):
                dck_lines.pop(fcount_min+1)
    # Add initial values
    for i in range(0, len(list_output_id)):
            dck_lines.insert( fcount_min + 1 + i, str(list_output_name[i] + " "))
            if i/5 == int(i/5):
                dck_lines.insert(fcount_min+2+i, "\n")
                fcount_min += 1
    dck_lines.insert( fcount_min + 1 + len(list_output_id), "\n")

def _link_CSVOutput_as_BuildingInput(dck_lines, list_sched_name, list_sched_id, fcounti, schedKEY="SCHED", schedFILEUNIT=["14"]):
    """
    This functions allows one to write TRNSYS links between the outputs of Type56 stored in list_output_name and the inputs of the Type25c where fcount is pointing.
    The list_output_name and list_output_id are sublist extracted from Type56 list of output to make sure this Type25c doesn't have too much inputs.

    Args:
        dck_lines (list-like): a list-like object of a .dck file.
        list_sched_name (list): A list of schedule found in the schedule files columns used by Type9c file reader model.
        list_sched_id (list): Unique ID for each scuedule input of list_sched_name.
        fcount (int): The line from which to start reading the dck_lines file (i.e. the line of the current Type56 where to write the nexts inputs.)
        schedKEY (string): A string of the common identifier found a the begening of every schedule name. Used for importing only specific columns from CSV file.
        schedFILEUNIT (string): A string of an integer corresponding to the fileUNIT of the CSV (defined in the assign line  of CSV import block).
    """

    fcount = utils._checkStr(dck_lines, "INPUTS",begin=fcounti, raise_error=False)

    # Remove existing link to SCHEDULES
    fcountrmv = 0
    nb_sched_toRmv = int(dck_lines[fcount].split("INPUTS")[1])
    for i in range(0, nb_sched_toRmv + 1):
            if schedKEY in dck_lines[fcount + fcountrmv]:
                dck_lines.pop(fcount + fcountrmv)
            else:
                fcountrmv += 1
        
    # Add link to schedules
    dck_lines.pop(fcount)
    dck_lines.insert(fcount, "INPUTS " + str(fcountrmv -1 + len(list_sched_name))+"\n")

    fcount = utils._checkStr(dck_lines, "*** INITIAL INPUT VALUES",begin=fcount, raise_error=False)-1
    for i in range(0, len(list_sched_id)):
        dck_lines.insert( fcount + 1 + i,schedFILEUNIT[i]+","+str(list_sched_id[i])+" \t\t! building.b18: "+str(list_sched_id[i])+"- "+list_sched_name[i]+" ->Input to be logger.infoed-"+str(i+1)+ "\n")

    # Add initial values
    fcount =  utils._checkStr(dck_lines, "*** External files",begin=fcount, raise_error=False)
    i = 0
    while i < len(list_sched_id):
        dck_lines.insert( fcount, "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 \n")
        i += 50
    fcount =  utils._checkStr(dck_lines, "*** External files",begin=fcount, raise_error=False)
    dck_lines.insert(fcount, "\n")

# ================================================================================
# Main function ==================================================================
# ================================================================================

def generate_AllDeckForSimulations(c):
    """
    Main function for deck generation. 
    Iterates on the file found in building file directory and call _buildDeck_FromB18() function for each file.

    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.
    """
    logger.info("STARTING STEP 4 ====================")
    logger.info("GENERATE DECKS FOR TRNSYS SIMULATION")
    logger.info("====================================")

    # Get list of files name in directory ---------------------------------
    logger.info("> Reading building files from directory")
    
    # For each building file in directory (.b18) --------------------------
    logger.info("STARTING DECK GENERATION -----")
    for file in c.models:

        # GENERATE DECK 
        if c.Precision_EXP == "stochastic":
            try: 
                pd.read_csv(c.path_OutputSCH + file + ".csv")
                PATH_SCHEDULE_FILE = c.path_OutputSCH + file + ".csv"
            except:
                PATH_SCHEDULE_FILE = c.path_ScheduleAnnualInputFile     
        else:
            PATH_SCHEDULE_FILE = c.path_ScheduleAnnualInputFile

        logger.info("> Generate deck for "+file)
        _buildDeck_FromB18(B18_InputPath=c.DictSIMpath[file]+file+".b18", 
                                        c=c,
                                        DCK_TemplatePath=c.path_TemplateDECK, 
                                        DCK_OutputPathDir=c.path_OutputSIM, 
                                        PATH_METEO_FILE=c.path_Meteo, 
                                        PATH_SCHEDULE_FILE=PATH_SCHEDULE_FILE,
                                        KEY_sched= c.schedKEY,
                                        KEY_input= c.targetkey_INPUT,
                                        filename=file)

# ================================================================================
# ================================================================================
# ================================================================================
