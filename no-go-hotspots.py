# Modules/libraries
import os
import arcpy

# Overwrite outputs
arcpy.env.overwriteOutput = True

# Define directories
gdb_dir = r"No_Go_Clusters.gdb"
input_dir = r"Input"
output_dir = r"Output"

# Set workspace
arcpy.env.workspace = gdb_dir

# Set parameters
# "buff_dist" is the buffer distance around SAPAD polygons
# "min_feats" is min number of no-go polygons required to make up a cluster
# "search_dist" is the radius used to look for clusters
buff_dist = "250 Meters"
min_feats = "30"
search_dist = "10 Kilometers"

# Convert SAPAD to feature layer
pa_data = os.path.join(input_dir, "SAPAD_OR_2020_Q3_Ownership selection 1.shp")
arcpy.MakeFeatureLayer_management(pa_data, "SAPAD_layer")

# Buffer SAPAD to take into account no go polygons occurring on the periphery
arcpy.Buffer_analysis(in_features="SAPAD_layer", out_feature_class="SAPAD_buffered",
                      buffer_distance_or_field=buff_dist,
                      line_side="FULL", line_end_type="ROUND",
                      dissolve_option="NONE",
                      dissolve_field=[], method="PLANAR")

# Convert no-go polygon shapefile to feature layer
nogo_data = os.path.join(input_dir, "nogo_PA.shp")
arcpy.MakeFeatureLayer_management(nogo_data, "nogo_polygons")

# Clip no-go polygons by SAPAD buffered layer to isolate the polygons which occur within PAs
arcpy.analysis.Clip(in_features="nogo_polygons",
                    clip_features="SAPAD_buffered",
                    out_feature_class="nogo_polygons_clip", cluster_tolerance="")

# Use symmetrical difference to subtract the no-go polygons which occur within SAPADs from all no-go polygons
arcpy.analysis.SymDiff(in_features="nogo_polygons",
                       update_features="nogo_polygons_clip",
                       out_feature_class="nogo_outside_SAPAD",
                       join_attributes="ALL", cluster_tolerance="")

# Dissolve boundaries of above's output to take into account multipart polygons
arcpy.analysis.PairwiseDissolve("nogo_outside_SAPAD",
                                "nogo_polygons_dissolve",
                                "SENSFEAT",None, "SINGLE_PART")

# Create a point in the centre of each dissolved polygon
arcpy.management.FeatureToPoint(in_features="nogo_polygons_dissolve",
                                out_feature_class="nogo_points", point_location="INSIDE")

# Identify where clusters occur with density-based clustering analysis
arcpy.DensityBasedClustering_stats(in_features="nogo_points",
                                   output_features="nogo_density_clusters",
                                   cluster_method="DBSCAN", min_features_cluster=min_feats,
                                   search_distance=search_dist, cluster_sensitivity=None)

# Remove points with CLUSTER_ID = -1 so only left with actual clusters
arcpy.MakeFeatureLayer_management("nogo_density_clusters", "nogoDC_layer")
arcpy.SelectLayerByAttribute_management("nogoDC_layer", "NEW_SELECTION", '"CLUSTER_ID" > 0')

# Use join function to keep no_go_polygons that intersect with cluster points to extract relevant species IDs
arcpy.SpatialJoin_analysis(target_features="nogo_polygons", join_features="nogoDC_layer",
                           out_feature_class="nogo_join", join_operation="JOIN_ONE_TO_MANY",
                           match_option="INTERSECT")

arcpy.SelectLayerByAttribute_management("nogo_join", "NEW_SELECTION",
                                        '"CLUSTER_ID" IS NOT NULL And "CLUSTER_ID" > 0')

# Convert both layers to shapefile
filename1 = "nogo_dens_clust_" + buff_dist + "_" + search_dist + "_" + min_feats + "feats"
outname1 = os.path.join(output_dir, filename1)

arcpy.CopyFeatures_management("nogoDC_layer",
                              outname1)

filename2 = "nogo_clust_polygons_" + buff_dist + "_" + search_dist + "_" + min_feats + "feats"
outname2 = os.path.join(output_dir, filename2)

arcpy.CopyFeatures_management("nogo_join_Layer2",
                              outname2)

# Working now (use TableToTable instead of TableToExcel [this requires table as an input, not feature class])
filename3 = "Table_" + buff_dist + "_" + search_dist + "_" + min_feats + "feats.csv"
arcpy.TableToTable_conversion(in_rows="nogo_join_Layer2", out_path="Output", out_name=filename3)

## Add more functions for mapping here?
