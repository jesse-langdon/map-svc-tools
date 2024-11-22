#   Title:          Map Service Tools
#   Description:    Python Toolbox intended for use with ArcGIS Pro 3.x. This toolbox includes tools for updating,
#                   publishing, and maintaining map services in an ESRI Enterprise Portal environment.
#   Author:         Jesse Langdon, Principal GIS Analyst, Planning and Development Services (PDS)
#   Last Update:    11/22/2024
#   Dependencies:   Python 3, ArcGIS Pro 3.3, arcpy, Windows 11


import arcpy
import os


class Toolbox(object):
    def __init__(self):
        """Define the toolbox."""
        self.label = "Map Service Tools"
        self.alias = "MapServiceTools"
        self.tools = [UpdateAPRXSources]


class UpdateAPRXSources(object):
    def __init__(self):
        """Initialize the tool."""
        self.label = "Update APRX Data Sources"
        self.description = "Updates enterprise geodatabase references in APRX files"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions."""
        # Input folder parameter
        in_folder = arcpy.Parameter(
            displayName="Input folder",
            name="in_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )

        # Output folder parameter
        out_folder = arcpy.Parameter(
            displayName="Output folder",
            name="out_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )

        # Environment selection
        env_type = arcpy.Parameter(
            displayName="Update map service from test to production, or production to test",
            name="env_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        env_type.filter.type = "ValueList"
        env_type.filter.list = ["TEST to PROD", "PROD to TEST"]
        env_type.value = "TEST to PROD"

        # APRX selection parameter
        aprx_selection = arcpy.Parameter(
            displayName="Choose APRX files to process",
            name="aprx_selection",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True
        )

        params = [in_folder, out_folder, env_type, aprx_selection]
        return params

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters."""
        if parameters[0].altered and not parameters[0].hasBeenValidated:
            try:
                # Set workspace to input folder
                arcpy.env.workspace = parameters[0].valueAsText
                # Get list of APRX files using arcpy.ListFiles
                aprx_files = arcpy.ListFiles("*.aprx")

                if aprx_files:
                    parameters[3].filter.type = "ValueList"
                    parameters[3].filter.list = aprx_files
                else:
                    parameters[3].filter.list = []
            except:
                parameters[3].filter.list = []
        return

    def updateMessages(self, parameters):
        """Modify messages created by internal validation."""
        if parameters[0].altered:
            if not os.path.exists(parameters[0].valueAsText):
                parameters[0].setErrorMessage("Input folder does not exist!")

        if parameters[1].altered:
            if not os.path.exists(parameters[1].valueAsText):
                parameters[1].setErrorMessage("Output folder does not exist!")

        if parameters[0].value == parameters[1].value:
            parameters[1].setErrorMessage(
                "Input and output folders must be different!"
            )
        return

    def execute(self, parameters, messages):
        """Execute the tool."""
        # Get parameter values
        input_folder = parameters[0].valueAsText
        output_folder = parameters[1].valueAsText
        env_type = parameters[2].valueAsText
        selected_aprx = parameters[3].valueAsText.split(";")

        # Set source strings based on environment
        if env_type == "TEST to PROD":
            source_sde_conn = r"\\snoco\gis\plng\GDB_connections_PAG\WIN_USER\WIN_USER@SCD_GIS_PUBLISH_TEST.sde"
            dest_sde_conn = r"\\snoco\gis\plng\GDB_connections_PAG\WIN_USER\WIN_USER@SCD_GIS_PUBLISH.sde"
        else:
            source_sde_conn = r"\\snoco\gis\plng\GDB_connections_PAG\WIN_USER\WIN_USER@SCD_GIS_PUBLISH.sde"
            dest_sde_conn = r"\\snoco\gis\plng\GDB_connections_PAG\WIN_USER\WIN_USER@SCD_GIS_PUBLISH_TEST.sde"

        arcpy.AddMessage(f"Processing APRX files from: {input_folder}")
        arcpy.AddMessage(f"Saving updated files to: {output_folder}")
        arcpy.AddMessage(f"Updating sources from {env_type}...")

        # Process each selected APRX file
        for aprx_name in selected_aprx:
            try:
                input_aprx = os.path.join(input_folder, aprx_name)
                output_aprx = os.path.join(output_folder, aprx_name)

                # Open the APRX
                aprx = arcpy.mp.ArcGISProject(input_aprx)

                # Update the connection properties of the APRX
                arcpy.AddMessage(f"Updating connection properties in {aprx_name}...")
                aprx.updateConnectionProperties(source_sde_conn, dest_sde_conn)

                # Save the updated APRX
                aprx.saveACopy(output_aprx)
                arcpy.AddMessage(f"Saved updated APRX to: {output_aprx}")

                # Clean up
                del aprx

            except Exception as e:
                arcpy.AddError(f"Error processing {aprx_name}: {str(e)}")
                continue

        arcpy.AddMessage(f"Processing complete for {len(selected_aprx)} APRX files.")
        return