# Local
import _Utils as utils
from _Logging import logger 
# Lib
import os
import pandas as pd

# ================================================================================
# Updater for template THN TRNSYS file ===========================================
# ================================================================================

def update_RTh(c):
    """
    Function to size a template thermal network deck model (.dck). Depending on c.Precision_RTU, will use appropriate template, then:
    Read pipes.csv file to overwrite pipes properties and pumps sizing in template.
    Read total loads file to overwrite heat pump and chiller sizing in template.
    Then export resize deck so it's ready to be simulated.
    
    Args:
        c (ClassConfiguration): A ClassConfiguration object containing all path and parameters of tool.  
    """
    # Get template ===================================================================================
    with open(c.path_Rth, "r", encoding="iso-8859-1") as b18_file:
                dck_lines = b18_file.readlines()

    # Get pipe file ==================================================================================
    pipeDF = pd.read_csv(c.path_Pipefile, skipinitialspace=True, index_col="name") 
    print(pipeDF.columns)
    
    # LOOP FOR EACH EQUATION BLOCK ===================================================================
    lineNumber_WhereEQ = utils._checkStr(dck_lines, "* EQUATIONS")
    while (lineNumber_WhereEQ != None):
        
        # Get clean line
        line = utils._cleanString(dck_lines[lineNumber_WhereEQ]) 
        
        # Get eq NAME ("assuming line format is: * EQUATIONS "NAME")
        eq_name = str(utils._cleanString(line.strip('* EQUATIONS').strip(" ").strip('"')))
        
        subheat_security = 1.5
        subcool_security = 1.5
        # Update design pump ----------------------------------------------
        if ("Design" in eq_name and "Main" not in eq_name):
            
            # Get corresponding pipe
            design_nb = eq_name.split("-")[1]
            pipename_H = "H-" + design_nb
            pipename_C = "C-" + design_nb 
            cluster_name = design_nb.split("_")[0]

            # Get pipe values 
            QdotHeatRated = (float(pipeDF.loc[pipename_H, "Q"])*subheat_security)      #kJ/hr
            QdotCoolRated = (float(pipeDF.loc[pipename_C, "Q"])*subcool_security)      #kJ/hr
         
            # Get prameters line
            fcount_param = utils._checkStr(dck_lines, "EQUATIONS", begin=lineNumber_WhereEQ+1, raise_error=False) + 1

            # Update parameters
            dck_lines.pop(   fcount_param)
            dck_lines.insert(fcount_param,   "qdotheat"+cluster_name +"Rated = "+str(QdotHeatRated)+" !Design heating load for heat loop [kJ/h] \n")
            dck_lines.pop(   fcount_param+1)
            dck_lines.insert(fcount_param+1, "qdotcool"+cluster_name +"Rated ="+str(QdotCoolRated)+ " ! Design flowrate for cool 2 loop [kg/h], DeltaT=12-4=8K \n")
      
        # Update design Main pump ------------------------------------------
        """
        if ("Design" in eq_name and "Main" in eq_name):
            # Get pipe values 
            mdotHeatRated = str(float(pipeDF.loc["H-All_1", "Q"])/4.19/30*mainheat_security)  #kg/hr
            mdotCoolRated = str(float(pipeDF.loc["C-All_1", "Q"])/4.19/8*maincool_security)  #kg/hr

            # Get prameters line
            fcount_param = utils._checkStr(dck_lines, "EQUATIONS", begin=lineNumber_WhereEQ+1, raise_error=False) + 1

            # Update parameters
            dck_lines.pop(   fcount_param+2)
            dck_lines.insert(fcount_param+2, "mdotHeat"+"Main" +"Rated = "+mdotHeatRated+" ! Design flowrate for heat 2 loop [kg/h], DeltaT=75-45=30 \n")
            dck_lines.pop(   fcount_param+3)
            dck_lines.insert(fcount_param+3, "mdotCold"+"Main" +"Rated ="+mdotCoolRated+ " ! Design flowrate for cool 2 loop [kg/h], DeltaT=12-4=8K \n")
        """
        # Update parameters ------------------------------------------------
        if ("Parameters" in eq_name):
        
            # Get prameters line
            fcount_param = utils._checkStr(dck_lines, "EQUATIONS", begin=lineNumber_WhereEQ+1, raise_error=False) + 9

            # Calcul rated values of systems parameters
            Qcondrated = float(pipeDF.loc["H-All_1", "Q"]) / 1000 /3600  # kJ/hr > MW
            Qevaprated = Qcondrated * (1-1/c.PAC_COP_Rated)   # MW
            r = c.PAC_Evap_CorrectionRatio / c.PAC_Cond_CorrectionRatio

            QChillerrated =float(pipeDF.loc["C-All_1", "Q"]) / c.chiller_Capacity_CorrectionRatio /1000 /3600  # kJ/hr > MW
            COPchiller_op = c.chiller_COP_Rated / c.chiller_COP_CorrectionRatio

            # Update parameters
            for i in range(0,5):            
                dck_lines.pop(fcount_param)
        
            dck_lines.insert(fcount_param, "COPChillerrated ="+str(COPchiller_op)+" \n")
            dck_lines.insert(fcount_param, "QChillerrated ="  + str(QChillerrated) +"* 3600 * 1000 !MW to kj/hr \n")
            dck_lines.insert(fcount_param, "r_in = "     + str(r)+" \n")
            dck_lines.insert(fcount_param, "Qcondrated ="+ str(Qcondrated) +"* 3600 * 1000 ! [kJ/hr] \n")
            dck_lines.insert(fcount_param, "Qevaprated ="+ str(Qevaprated) +"* 3600 * 1000 ! [kJ/hr] \n")

            print("Qcondrated: ", Qcondrated, " MW")
            print("Qevaprated: ", Qevaprated, " MW")

        # Go to next EQ in file
        lineNumber_WhereEQ = utils._checkStr(dck_lines, "* EQUATIONS", begin=lineNumber_WhereEQ+1, raise_error=False)


    # LOOP FOR EACH UNIT =============================================================================
    lineNumber_WhereUNIT = utils._checkStr(dck_lines, "UNIT")
    while (lineNumber_WhereUNIT != None):
        if "TYPE" in dck_lines[lineNumber_WhereUNIT]:
        
            # Get clean line
            line = utils._cleanString(dck_lines[lineNumber_WhereUNIT]) 
            
            # Get unit ID and NAME ("assuming line format is: UNIT XX TYPE XX \t NAME )
            unit_type_id = int(utils._cleanString(line.split(" ")[3].strip("\t")))
            unit_name = str(utils._cleanString(line.split(" ")[4]))
            
          
            # ----- Loop for each TYPE 25 unit (output file) -----
            if unit_type_id == 952:
                print(unit_type_id, ">", unit_name, "<")

                # Assuming name format is: X-PipeID-Y
                X = unit_name.split("-")[0]
                PipeID = unit_name.split("-")[1]
                unit_name = X + "-" + PipeID

                # Get prameters line
                fcount_param = utils._checkStr(dck_lines, "PARAMETERS", begin=lineNumber_WhereUNIT, raise_error=False) + 1


                # Remove parameters
                for i in range(0,12):            
                    dck_lines.pop(fcount_param)
                
                # Write parameters
                dck_lines.insert(fcount_param, "15		! 12 Initial Fluid Temperature \n")
                dck_lines.insert(fcount_param, "3.0		! 11 Viscosity of Fluid \n")
                dck_lines.insert(fcount_param, "4.19		! 10 Specific Heat of Fluid \n")
                dck_lines.insert(fcount_param, "2.0		! 9 Thermal Conductivity of Fluid \n")
                dck_lines.insert(fcount_param, "1000.0		! 8 Density of Fluid \n")
                dck_lines.insert(fcount_param, str(float(0.027/3.6))+"    ! 7 Thermal Conductivity of Insulation \n")
                dck_lines.insert(fcount_param, str(pipeDF.loc[unit_name, "e"])+"    ! 6 Thickness of Insulation \n")
                dck_lines.insert(fcount_param, "1.5		! 5 Buried Pipe Depth \n")
                dck_lines.insert(fcount_param, "54 	    ! 4 Thermal Conductivity of Pipe Material \n")
                dck_lines.insert(fcount_param, str(pipeDF.loc[unit_name, "Do"])+"    ! 3 Outer Diameter of Pipe \n")
                dck_lines.insert(fcount_param, str(pipeDF.loc[unit_name, "Di"])+"    ! 2 Inner Diameter of Pipe \n")
                dck_lines.insert(fcount_param, str(pipeDF.loc[unit_name, "L"])+"    ! 1 Length of Buried Pipe \n")

      
        # Go to next UNIT in file
        lineNumber_WhereUNIT = utils._checkStr(dck_lines, "UNIT", begin=lineNumber_WhereUNIT+1, raise_error=False)

    
    # Save deck ======================================================================================
    with open(c.path_Rth_out, "w", encoding="iso-8859-1") as converted_file:
                for line in dck_lines:
                    converted_file.writelines(str(line))
    logger.info("Saving RTh ")

# ================================================================================
# ================================================================================
# ================================================================================
