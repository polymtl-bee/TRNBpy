Code documentation
==================

1. Site data builder
~~~~~~~~~~~~~~~~~~~~

.. automodule:: S1_SiteDataBuilder
.. autofunction:: S1_SiteDataBuilder._make_Site
.. autofunction:: S1_SiteDataBuilder._make_Buildings
.. autofunction:: S1_SiteDataBuilder._schedules_generator
.. autofunction:: S1_SiteDataBuilder._get_scheduleList_FromSpacetype
.. autofunction:: S1_SiteDataBuilder._generate_InputSchedule
.. autofunction:: S1_SiteDataBuilder._update_json_with_trnsys_schedules
.. autofunction:: S1_SiteDataBuilder._update_json_with_input_schedules
.. autofunction:: S1_SiteDataBuilder._loadAllSchedules_InAllSpacetypes

2. JSON builder
~~~~~~~~~~~~~~~

.. automodule:: S2_JsonBuilder
.. autofunction:: S2_JsonBuilder._BuildSpacetypeSurface
.. autofunction:: S2_JsonBuilder._ChooseSpacetype_Probability
.. autofunction:: S2_JsonBuilder._ChooseSpacetype_Manually
.. autofunction:: S2_JsonBuilder._BuildJSONFile

3. Noise builder
~~~~~~~~~~~~~~~~

.. automodule:: S3_NoiseBuilder
.. autofunction:: S3_NoiseBuilder.randomIntervalSelection
.. autofunction:: S3_NoiseBuilder.noiseValues
.. autofunction:: S3_NoiseBuilder.noiseSchedules
.. autofunction:: S3_NoiseBuilder.noiseTsetpoint
.. autofunction:: S3_NoiseBuilder.noise

4. Deck builder
~~~~~~~~~~~~~~~

.. automodule:: S4_DeckBuilder
.. autofunction:: S4_DeckBuilder._buildDeck_FromB18
.. autofunction:: S4_DeckBuilder._link_B18Output_as_printerInput
.. autofunction:: S4_DeckBuilder._link_CSVOutput_as_BuildingInput
.. autofunction:: S4_DeckBuilder.generate_AllDeckForSimulations

5. Load builder
~~~~~~~~~~~~~~~

.. automodule:: S6_LoadBuilder
.. autofunction:: S6_LoadBuilder._get_ModelLoads_FromCSV
.. autofunction:: S6_LoadBuilder._print_stats
.. autofunction:: S6_LoadBuilder._ModelsLoader
.. autofunction:: S6_LoadBuilder._GetClusterLoads
.. autofunction:: S6_LoadBuilder._GetBuildingLoads
.. autofunction:: S6_LoadBuilder._GetSurfacicZoneLoads
.. autofunction:: S6_LoadBuilder._UpdateSiteLoads
.. autofunction:: S6_LoadBuilder._UpdateSpacetypeLoads
.. autofunction:: S6_LoadBuilder.smoothing
.. autofunction:: S6_LoadBuilder.scaling_detailed
.. autofunction:: S6_LoadBuilder.scaling_archetype
.. autofunction:: S6_LoadBuilder.scaling_prototype
.. autofunction:: S6_LoadBuilder.Scaling

6. Thermal network builder
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: S8_ThnBuilder
.. autofunction:: S8_ThnBuilder.update_RTh

7. Log file builder
~~~~~~~~~~~~~~~~~~~

.. automodule:: _Logging
   :members:

8. Translate to B18
~~~~~~~~~~~~~~~~~~~

.. automodule:: _TranslateToB18
   :members:

9. Utilities
~~~~~~~~~~~~

.. automodule:: _Utils
   :members:


