Example of use
==============

For this example, we assume you just created a new file example.py at the root of the project. Then create the foldes in data/ as shown below. The folder structure should look like this:

.. code-block:
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

.. code-block:
    pip install -r requirements.txt



1. Create project data
----------------------


1.1 Building CSV description
----------------------------

.. code-block:
    print("Step 1 - Preparation of spacetype")
    sitedatabuilder._loadAllSchedules_InAllSpacetypes(c)

1.2 Model structural b18 files
------------------------------

1.3 Spacetype json files
------------------------


2. Create Configuration object
------------------------------

Now we can start manipulating the ``example.py`` file.
First of all, let's import TRNBpy to our new project.

.. code-block:
    # import TRNBpy
    from src.TRNBby import *

Now you can define: 
- The precision you want for model geometry (Precision_BLD) depending on what you have stored in 2_StructuralModels_B18 folder.
- The precision for occupancy. "Determinist", "Variable" (Multiple choice for residential areas), "Stochastic" (variable and use of noise builder code for more stochasticity).
- The precision of thermal network model. By default, choose "TopologySimplified". This precision is used only if you go to the last step for generation of thermal network deck file.

.. code-block:
    Precision_BLD = "Detailed"
    Precision_EXP = "Determinist"
    Precision_THN = "TopologySimplified"

Now that you've defined your choice of precision for the three dimensions, just create a ClassConfiguration object to initiate all parameters.
Make sure your os can read the path defined in ClassConfiguration object. Change c.psep to match your os path definition.
Finally, call the ClassConfiguration method ``_load_keys()`` so that template JSON strutcure is read and its keys copied.

.. code-block:
    c = ClassConfiguration(scenarioName=scenario,         # Folder name (Windows my\\path but Linux my/path)
                           psep = "\\"                    # Must be "\\" on Windows and "/" on linux.
                           Precision_BLD=Precision_BLD,   # "detailed" - "tailored" - "prototype"
                           Precision_EXP=Precision_EXP,   # "determinist" - "variable" - "stochastic"
                           Precision_THN=Precision_THN)   # "TopologyDetailed" - "TopologyReduced" - "TopologySimplified" 
    c._load_keys()

3. Call the functions
---------------------

Now, copy paste the following lines to start the different steps necessary for generating deck files for all models.

.. code-block:
    print("Step 2 - Generate JSON Building file")
    jsonbuilder._BuildJSONFile(c)

    print("Step 3 - Noise generation: For non-deterministic approaches, add noise & variability to some values")
    noisebuilder.noise(c)

    print("Step 4.1 - Convert JSON Building file to B18")
    convert.convert_FromJSON_ToB18(c)

    print("Step 4.2 - Deck generation")
    deckbuilder.generate_AllDeckForSimulations(c)

As automatic simulation is not yet supported, you should manually run all deck simulation before proceding to the next step. When it's done, do step 6 and check debug.log for warning or critical error to see if you have not forgotten to simulate a deck.

.. code-block:
    print("Step 6 - Load builder: Start scaling from model to building loads")
    loadbuilder.Scaling(c)

Here you go ! You now have built the loads for all of your buildings !
If you want to go further and simulate a thermal network, you should check PipingTool tool before proceding to the next step.

For now, let's assume you are coming back from Piping tool with the following files:

.. code-block:
    input/
        cluster1.csv
        cluster2.csv
        ...
        clusterN.csv
    pipe.csv
    totalloads.csv

Then, copy all those files to ``data/6_RTh/YourPrecisionOfTHN/`` (of course, replace YourPrecisionOfTHN by your precision of THN).
Then, run the following lines to generate an re-sized THN adapted to your pipes and loads: 

.. code-block:
    print("Step 8 - THN Builder: Update THN deck file with equipment and pipe sizing.")
    thnbuilder.update_RTh(c)