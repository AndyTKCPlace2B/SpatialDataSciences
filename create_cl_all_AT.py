# Import arcpy module
import arcpy

# Script arguments
podsDB = arcpy.GetParameterAsText(0)
iliDB = arcpy.GetParameterAsText(1)

# Local variables:
toolRunData_XYZ = str(iliDB) + "\\ToolRunData_XYZ"
toolRunData_Select = str(iliDB) + "\\ToolRunData_Select"
pipeJoin = str(podsDB) + "\\PIPE_JOIN"
calibrationPoint_PreGen = str(iliDB) + "\\CalibrationPoint_PreGen"
clSelect = str(iliDB) + "\\CL_Select"

# Process: Select
arcpy.Select_analysis(toolRunData_XYZ, toolRunData_Select, "Feature = 'WELD'")

# Process: Join Field
arcpy.JoinField_management(toolRunData_Select, "WeldId", pipeJoin, "JOIN_IDENTIFIER", "DerivedMeasure")

# Process: Select (2)
arcpy.Select_analysis(toolRunData_Select, calibrationPoint_PreGen, "\"DerivedMeasure\" IS NOT NULL")

# Process: Select (3)
arcpy.Select_analysis(toolRunData_XYZ, clSelect, "CLGeometry = 'Yes'")

#you need the spatial reference (coordinate system) to load shape
sr = arcpy.Describe(clSelect).spatialReference
arcpy.CreateFeatureclass_management(iliDB, "CL_SELECT_PointToLine", "POLYLINE", has_m="ENABLED", has_z="ENABLED", spatial_reference=sr)
cl = str(iliDB) + "//CL_SELECT_PointToLine"
arcpy.AddField_management(cl, "ET_ID", "TEXT")
#an array is a collection, you insert the points in order
array = arcpy.Array()
#pulls data from point class, note the order by statement
rows = arcpy.da.SearchCursor(clSelect,['Longitude','Latitude','Altitude','WheelCountFt', 'ROUTE_ID'],sql_clause = (None, "ORDER BY ROUTE_ID, WheelCountFt ASC"))
#loop through points and add them to the array, order of entry is important
rid = ''
for row in rows:
    if row[4] == rid:
        array.append(arcpy.Point(row[0],row[1],row[2],row[3]))
    else:                    
        if rid != '':
            #Convert array into polyline, all parameters are needed
            polyline = arcpy.Polyline(array,sr,True,True)
            #tell python you're inserting some rows into a feature class and insert one row
            rows = arcpy.da.InsertCursor(cl,['SHAPE@', 'ET_ID'])
            rows.insertRow([polyline, rid])
            #releases lock on feature class
            del rows
            array = arcpy.Array()
        rid = row[4]
        array.append(arcpy.Point(row[0],row[1],row[2],row[3]))
#Convert array into polyline, all parameters are needed
polyline = arcpy.Polyline(array,sr,True,True)
#tell python you're inserting some rows into a feature class and insert one row
rows = arcpy.da.InsertCursor(cl,['SHAPE@', 'ET_ID'])
rows.insertRow([polyline, rid])
#releases lock on feature class
del rows

# Local variables:
clSelect_pointtoline = cl
#calibrationPoint_PreGen = r'C:\Projects\Koch\20220819\test\ILIData24B.gdb\CalibrationPoint_PreGen'
calibrationPoint_PreGen = str(iliDB) + "\\CalibrationPoint_PreGen"
#clFinal = r'C:\Projects\Koch\20220819\test\ILIData24B.gdb\CL_Final'
clFinal = str(iliDB) + "\\CL_Final"
centerline = str(podsDB) + "\\CENTERLINE"

# Process: Calibrate Routes
arcpy.CalibrateRoutes_lr(clSelect_pointtoline, "ET_ID", calibrationPoint_PreGen, "ROUTE_ID", "DerivedMeasure", clFinal, "DISTANCE", "1 Feet", "BETWEEN", "BEFORE", "AFTER", "IGNORE", "KEEP", "INDEX")

# Process: Generalize
arcpy.Generalize_edit(clFinal, "0.5 Feet")

# Process: Join Field
arcpy.JoinField_management(clFinal, "ET_ID", centerline, "ROUTE_ID", "OBJECTID;LINE_DESIGNATOR;LINE_DESCRIPTION;LINE_TYPE;LINE_SYSTEM_TYPE;ROUTE_DESCRIPTION;ROUTE_SEQUENCE;ROUTE_TYPE;ROUTE_INTERSTATE_LF;BEGIN_MEASURE;END_MEASURE;ROUTE_ID;LINE_ID;ROUTE_OPERATING_STATUS;LINE_OPERATING_STATUS;PRODUCT_SUBTYPE_SCL;LENGTH;DerivedRouteID;GlobalID;SHAPE_Length;TRC_Remarks")

