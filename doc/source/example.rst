Example of use
==============

For this example, we assume you just created a new file example.py at the root of the project. Then create the foldes in data/ as shown below. The folder structure should look like this:

.. code-block::
    data/
        example/                         # << New folder for file data
            1_BuildingDescription_CSV/      # Where you store your CSV description of buildings
            2_StructuralModels_B18/         # Where you store your b18 geometric models (built from Sketchup3D or other)
            3_Spacetype_JSON/               # Where you store the spacetype in .json format.
    doc/
    src/
    example.py   # << New file
    README.md
    LICENCE.md
    requirements.txt

We also assume you have installed all dependencies in requirements.txt using the following command:

.. code-block::
    pip install -r requirements.txt

1. Create project data
----------------------

First things first, let's take a look at the data files needed to use TRNBpy:

- Data for building surfaces (.CSV) 
- TRNSYS model files (.B18).
- Set of occupancy hypothesis for models (.JSON)

1.1 Building CSV description
----------------------------

Building CSV files use a format close to the following. 

- **Name** is an unique ID for each cluster. 
- **SubBuilding** is the name of the Subbuilding.
- **Building** is the name of the Building.
- **Floor** is the name of the floor. We use F1 for ground floor. Fs for central floors. Ftop for last floor. F0 for underground floor.
- **Weight** is the time the cluster need to be taken into account. For instance, if a building have 25 floors, with 23 being central floor, we can decide to model only ground floor, top floor and one central floor (because all of them have the same boundaries conditions). Then the weight of the central floor should be 23 (25-1-1).

Then, the following columns represent each of your category of occupation as defined in the configuration file (see below configuration file).

- **R** stands for Residential surface.
- **C** stands for Commercial surface.
- **B** stands for Office surface.
- **I** stands for Institutionnal surface.
- **P** stands for Parking surface.

==========  ===========  ======== =====  ======  =====  =====  =====  =====  =====
Name        SubBuilding  Building Floor  Weight	 R	    C	   O	  I	     P
==========  ===========  ======== =====  ======  =====  =====  =====  =====  =====
B_SB1_F1	SB1          B	      F1	 1	     168.0	192.0			
B_SB1_Fs	SB1	         B	      Fs	 7	     360.0				
B_SB1_Ftop  SB1	         B	      Ftop	 1	     360.0				
B_SB2_F1    SB2	         B	      F1	 1	     630.0	196.0			
B_SB2_Fs    SB2	         B	      Fs	 5	     826.0				
B_SB2_Ftop  SB2	         B	      Ftop	 1	     826.0				
B_SB3_F1    SB3	         B	      F1	 1	     360.0				
B_SB3_Fs    SB3	         B	      Fs	 9	     826.0				
B_SB3_Ftop  SB3	         B	      Ftop	 1	     826.0				
B_SB3_F0    SB3	         B	      F0	 1	                                 826.0
==========  ===========  ======== =====  ======  =====  =====  =====  =====  =====


If you have detailed models of your buildings, you can also use the prebuilt function of TRNBpy for genereting CSV buildings files:

.. code-block::
    print("Step 0.1 - Make buildings csv files")
    sitedatabuilder._make_Buildings(c)

Then, check those files, and edit the weight of each cluster ("Building-Subbuilding-floor") if you have modelled your detailed building with 
central floor simplification (1 centrale floor instead of modelling all of them).

1.2 Model structural b18 files
------------------------------

You can use Sketchup and its TRNSYS3D extension to build models for your project.

Given the number of modeled thermal zones, a clear naming convention is necessary. This convention is also chosen to characterize the space in question using relevant data (building, floor, etc.). The zone naming convention follows this format:

> R-SubBuilding-Floor-id

Where:

- R: the occupancy type category (R for residential, C for commercial, I for institutional, B for Office (Bureau in french), P for Parking).
- SubBuilding: the name of the subbuilding to which the zone belongs.
- Fi: the floor identifier (for *Floor i*). For example: Fcave for basements, Ftop for the top floor, Fstack for the middle floors, F0 through FX for the rest.
- id: a unique zone identifier for that floor of the subbuilding.

Floor definition should match the building CSV files.

1.3 Spacetype json files
------------------------

Here is an example of a spacetype json file. Note that all entry are string, even when they represent float or integers.
A few things:

First, TRNBUILD use three type of data ("CONSTANT", "INPUT" and "SCHEDULE") so that variable can be defined as constant, as an input to the b18 model (so taken from TRNSYS deck) or as an internal variable following a schedule defined in schedule objects.
For TRNBpy, we use those three type using the following recommandation. In conf.py, prefix are defined for input type and schedule type. If those prefix are seen in the value expression, then TRNBpy know what to do, if no prefix is found, TRNBpy assume the value is constant.
For instance, i define in my spacetype the value of heating setpoint as "$INPUT_HeatingSetpoint1". Here I also write the type "INPUT" in my heating definition. Because of prefix "$INPUT_", TRNBpy will know that it should look for an entry named "HeatingSetpoint1", and use its value for heating setpoint.

Second, sometimes, some variables are floor-area dependant, or volume dependzant or whatever. To do so, TRNBpy can also do some math.  TRNBpy can detect and modifiy item values with real values of $ZONEVOLUME, $ZONESURFACE, $ZONEEXTSURFACE or $ZONERATIOEXT. 
Assuming the variable is in a f(x)= A*x equation, it will return item with f(x) instead of A*x.
So for instance, I write my infiltration as follow: { $ZONEEXTSURFACE * 0.07 }. {} define where TRNBpy should look for equation A*x. A is zone dependant item, x is a constant value.

.. code-block::
    {
        "Coolings":{
            "0":{
                "Name": "Name",                # Name of cooling.
                "Source": "Source",            # Sources of hypothesis for this cooling.
                "Description":"Description",   # Description of cooling.
                "Type":"Type",                 # "INPUT", "SCHEDULE" or "CONSTANT". Define type of TdbConsigne.
                "Power":"Power",               # Nominal sensible power of cooling per floor area (kJ/hr/m2)
                "TdbConsigne":"TdbConsigne",   # Temperature setpoint. Could be a constant value, an input (using "$INPUT_" prefix before input name) or an shcedule (using "$SCHEDULE_" prefix before input name)
                "AreaRelPower":"1",            # 1 if nominal power is per floor area. Else 0. Default is 1.
                "RadFrac":"0",                 # Radiative fraction of sensible power. Float in [0, 1]. Default is 0.
                "Humidity":"Humidity",         # Absolute humidity gains in kg/kg (String)
                "ElecPowerFrac":"0"            # Fraction of actual sensible power from electricity. Float in [0, 1]
            }
        },
        "Heatings":{
            "0":{
                "Name": "Name",                # Name of heating.
                "Source": "Source",            # Sources of hypothesis for this heating.
                "Description":"Description",   # Description of heating.
                "Type":"Type",                 # "INPUT", "SCHEDULE" or "CONSTANT". Define type of TdbConsigne.
                "Power":"Power",               # Nominal sensible power of heating per floor area (kJ/hr/m2)
                "TdbConsigne":"TdbConsigne",   # Temperature setpoint. Could be a constant value, an input (using "$INPUT_" prefix before input name) or an shcedule (using "$SCHEDULE_" prefix before input name)
                "AreaRelPower":"1",            # 1 if nominal power is per floor area. Else 0. Default is 1.
                "RadFrac":"0",                 # Radiative fraction of sensible power. Float in [0, 1]. Default is 0.
                "Humidity":"Humidity",         # Absolute humidity gains in kg/kg (String)
                "ElecPowerFrac":"0"            # Fraction of actual sensible power from electricity. Float in [0, 1] 
            }
        },
        "Gains":{
            "0":{
                "Name": "Name",                   # Name of gain.
                "Source": "Source",               # Sources of hypothesis for this gain.
                "Description":"Description",      # Description of gain.
                "GainCategory":"GainCategory",    # "LIGHTS", "EQUIPMENT", "PEOPLE". TRNSYS gain category.
                "GainType":"GainType",            # "AREA_RELATED" or "ABSOLUTE". Default is "AREA_RELATED".
                "GainSchedule":"",                # Name of schedule if used. Using prefix "$SCHEDULE_".
                "GainInput": "$INPUT_NameInput",  # Name of inpu if used. Using prefix "$INPUT_".
                "Convective":"Convective",        # Value of convective gain in kJ/hr.
                "Radiative":"Radiative",          # Value of radiative gain in kJ/hr.
                "Humidity":"Humidity",            # Value of humidity gain in kJ/hr.
                "ElecPowerFrac":"ElecPowerFrac"   # Fraction of actual sensible gain from electricity. 0 for PEOPLE, 1 for LIGHTS and EQUIPMENT type.
            }
        },


        "Infiltrations":{
            "0":{
                "Name": "Name",              # Name of infiltration.
                "Source": "Source",          # Sources of hypothesis for this infiltration.
                "Description":"Description", # Description of infiltration.
                "InfType":"InfType",         # "CONSTANT", "INPUT", "SCHEDULE". Type of InfRate entry.
                "InfRate":"InfRate"          # Value of infiltration in air replacement per hour (1/hr).
            }
        },
        "Schedules":{
            # Should be left empty. Will be automatically filled with schedule definition.
            # Make sure schedule file and schedule found in spacetype are matching.
        },
        "Ventilations":{
            "0":{
                "Name": "Name",                  # Name of ventilation.
                "Source": "Source",              # Sources of hypothesis for this ventilation.
                "Description":"Description",     # Description of ventilation.
                "Mode":"Mode",                   # "AIRCHANGE" for air change rate. "AIRFLOW" for mass flow rate."AIRFLOWSPEC" for mass flow rate related to reference floor area. "VAIRFLOW" for volume flow rate. "VAIRFLOWSPEC" for volume flow rate related to reference floor area. Default is "VAIRFLOW"
                "FlowValue": "FlowValue",        # Nominal value of flow of ventilation. Unit depends on Mode. Default is a zone dependant esuation { $ZONESURFACE * ValuePerM2 }.
                "FlowInput": "FlowInput",        # Empty or input name. Multiplying factor from an input entry. Using input prefix.
                "FlowSchedule": "FlowSchedule",  # Empty or schedule name. Multiplying factor from a schedule object. Using schedule prefix.
                "Tdb":"OUTSIDE",            # Temperature of airflow. Can be user defined value or OUTSIDE.
                "TdbType":"OUTSIDE",        # "CONSTANT", "INPUT", "SCHEDULE"  or "OUTSIDE". Type of Tdb entry. 
                "Humidity":"OUTSIDE",       # (Relative or absolute) Humidity of airflow. Can be user defined value or OUTSIDE.
                "HumidityType":"OUTSIDE",   # "CONSTANT", "INPUT", "SCHEDULE" or "OUTSIDE". Type of Humidity entry.
                "RelOrAbs":"rel",           # "rel" or "abs". Default is "rel" for relative. Relative or Absolute definition for Humidity.  
                "SpecFanPower":"0",         # Default is 0.
                "SensHr":"0",               # Default is 0.
                "Calcqahu":"1"              # Default is 1.
            }
        },
    },


2. Configure tool
-----------------

Now that we should have all the files, it's time to configure how we want the tool to work. Go to the config.py file.

1. Check the paths. Make sure it fits your project.
2. Check the Identification key variables, make sure it fits your project.
3. Check the InputFamily attribute. Update it with your schedules input family (for instance, all schedules used for restaurant should use the same start name: Resto_ventilation, Resto_occupant...)
4. Check the DictSpacetype attribute. Update it with your spacetype and their probability. For instance, if you have an entry in DictSpacetype that is "I":{"Workshop":0.1, "School":0.5, "Library":0.4}, 
then each zone starting with "I" ("I as their spacetype category identifier") will have 10% probability to be a orkshop, 50% probability to be a school and 40% for a library.

3. Create Configuration object
------------------------------

Now we can start manipulating the ``example.py`` file. First of all, let's import TRNBpy to our new project.

.. code-block::
    # import TRNBpy
    from src.TRNBby import *

Now you can define: 

- The precision you want for model geometry (Precision_BLD) depending on what you have stored in 2_StructuralModels_B18 folder.
- The precision for occupancy. "Determinist", "Variable" (Multiple choice for residential areas), "Stochastic" (variable and use of noise builder code for more stochasticity).
- The precision of thermal network model. By default, choose "TopologySimplified". This precision is used only if you go to the last step for generation of thermal network deck file.

.. code-block::
    Precision_BLD = "Detailed"
    Precision_EXP = "Determinist"
    Precision_THN = "TopologySimplified"

Now that you've defined your choice of precision for the three dimensions, just create a ClassConfiguration object to initiate all parameters.
Make sure your os can read the path defined in ClassConfiguration object. Change c.psep to match your os path definition.
Finally, call the ClassConfiguration method ``_load_keys()`` so that template JSON strutcure is read and its keys copied.

.. code-block::
    c = ClassConfiguration(scenarioName=scenario,         # Folder name (Windows my\\path but Linux my/path)
                           psep = "\\"                    # Must be "\\" on Windows and "/" on linux.
                           Precision_BLD=Precision_BLD,   # "detailed" - "tailored" - "prototype"
                           Precision_EXP=Precision_EXP,   # "determinist" - "variable" - "stochastic"
                           Precision_THN=Precision_THN)   # "TopologyDetailed" - "TopologyReduced" - "TopologySimplified" 
    c._load_keys()

4. Call the functions
---------------------

Now, copy paste the following lines to start the different steps necessary for generating deck files for all models.

.. code-block::
    print("Step 2 - Generate JSON Building file")
    jsonbuilder._BuildJSONFile(c)

    print("Step 3 - Noise generation: For non-deterministic approaches, add noise & variability to some values")
    noisebuilder.noise(c)

    print("Step 4.1 - Convert JSON Building file to B18")
    convert.convert_FromJSON_ToB18(c)

    print("Step 4.2 - Deck generation")
    deckbuilder.generate_AllDeckForSimulations(c)

As automatic simulation is not yet supported, you should manually run all deck simulation before proceding to the next step. When it's done, do step 6 and check debug.log for warning or critical error to see if you have not forgotten to simulate a deck.

.. code-block::
    print("Step 6 - Load builder: Start scaling from model to building loads")
    loadbuilder.Scaling(c)

Here you go ! You now have built the loads for all of your buildings !
If you want to go further and simulate a thermal network, you should check PipingTool tool before proceding to the next step.

For now, let's assume you are coming back from Piping tool with the following files:

.. code-block::
    input/
        cluster1.csv
        cluster2.csv
        ...
        clusterN.csv
    pipe.csv
    totalloads.csv

Then, copy all those files to ``data/6_RTh/YourPrecisionOfTHN/`` (of course, replace YourPrecisionOfTHN by your precision of THN).
Then, run the following lines to generate an re-sized THN adapted to your pipes and loads: 

.. code-block::
    print("Step 8 - THN Builder: Update THN deck file with equipment and pipe sizing.")
    thnbuilder.update_RTh(c)