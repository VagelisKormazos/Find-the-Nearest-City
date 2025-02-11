# shapefile reading, writing
import fiona
from fiona import collection

# frienly OGR and GDAL utils
from shapely.geometry import shape, mapping, Point
from shapely.ops import polygonize_full

# Speed up spatial join with a spatial index
from rtree import index
# assumes you've also installed: spatialindex
# eg on a Mac using Homebrew: brew install spatialindex

# pyshp packages for reading/writing ESRI format shapefiles
import shapefile

# Init the export properties schema
#schema = {}
source_crs = {}
source_driver = {}

# Store all lines from all input sources
lines = []

# Coastline
with fiona.open(
        "../../10m_physical/ne_10m_coastline.shp", 
        "r") as input:
    for line in input:
        lines.append(shape(line['geometry']))
# Minor Coastline
with fiona.open(
        "../../10m_physical/ne_10m_minor_islands_coastline.shp", 
        "r") as input:
    for line in input:
        lines.append(shape(line['geometry']))
# Admin 0 Boundary Lines Land
with fiona.open(
        "../../10m_cultural/ne_10m_admin_0_boundary_lines_land.shp", 
        "r") as input:
    for line in input:
        lines.append(shape(line['geometry']))
# Admin 0 Boundary Lines Map Units
with fiona.open(
        "../../10m_cultural/ne_10m_admin_0_boundary_lines_map_units.shp", 
        "r") as input:
    for line in input:
        lines.append(shape(line['geometry']))
# Admin 1 Boundary Lines
with fiona.open(
        "../../10m_cultural/ne_10m_admin_1_states_provinces_lines.shp", 
        "r") as input:
    for line in input:
        lines.append(shape(line['geometry']))
# Admin 1 Seams
with fiona.open(
        "../../10m_cultural/ne_10m_admin_1_seams.shp", 
        "r") as input:
    for line in input:
        lines.append(shape(line['geometry']))

# Report stats
print len(lines),         '\t','input lines'

# Load the shapefile of points and convert it to shapely point objects
points = []
point_attr = []
#point_coords = []
with fiona.open(
        "../../10m_cultural/ne_10m_admin_1_label_points.shp", 
        "r") as input_label_points:
    source_crs = input_label_points.crs
    source_driver = input_label_points.driver
    #out_schema = input_label_points.schema # doesn't work because point > polygon
    
    for point in input_label_points:
        points.append(shape(point['geometry']))
        point_attr.append(point['properties'])
        
# Report
print str( len( points ) ) +     '\t' + 'input label points'
#print str( len( point_attr ) ) + '\t' + 'label point attributes'

# Build polygons from all input lines
polygon_geoms, dangles, cuts, invalids = polygonize_full(lines)

# Report stats
print len(polygon_geoms), '\t','output polygons'
print '\terrors:'
print '\t',len(dangles),  '\t','dangles'
print '\t',len(cuts ),    '\t','cuts'
print '\t',len(invalids), '\t','invalids'

# TODO: This is redundant and should be rewriten
# Load the shapefile of points and convert it to shapely point objects
points_sf = shapefile.Reader("../../10m_cultural/ne_10m_admin_1_label_points.shp")
point_shapes = points_sf.shapes()
point_coords= [q.points[0] for q in point_shapes ]

# Build a spatial index based on the bounding boxes of the polygons
idx = index.Index()
count = -1
#for q in polygon_shapes:
for polygon in polygon_geoms:
    count += 1
    idx.insert( count, shape(polygon).bounds )
    #idx.insert(count, q.bbox)

# Assign one or more matching polygons to each point
matches = []
for i in range(len(points)): # Iterate through each point
    temp= None
    #print "Point ", i
    # Iterate only through the bounding boxes which contain the point
    for j in idx.intersection( point_coords[i] ):
        # Verify that point is within the polygon itself not just the bounding box
        if points[i].within(polygon_geoms[j]):
            #print "Match found! ", j
            temp=j
            break
    matches.append(temp) # Either the first match found, or None for no matches

# Report stats
print len(matches), '\t','polygons have point matches'
#print matches

# Report debug information
oops = len(polygon_geoms) - len(matches)
if oops > 0:
    print '\terrors:'
    print '\t',oops,'\t','polygons missing attributes'
if oops < 0:
    print '\terrors:'
    print '\t',oops,'\t','more attributes than polygons (ambiguous matches)'

# Setup export schema
out_schema = {  'geometry': 'Polygon',
                'properties': {
                    'diss_me': 'int:9',
                    'adm1_code': 'str:10',
                    'sr_sov_a3': 'str:3',
                    'sr_adm0_a3': 'str:3',
                    'sr_gu_a3': 'str:3',
                    'iso_a2': 'str:2',
                    'adm0_sr': 'float:4',
                    'name': 'str:100',
                    'admin': 'str:100',
                    'scalerank': 'float:4',
                    'datarank': 'float:4',
                    'featurecla': 'str:50' } }

# Export polygons to ESRI Shapefile format
with fiona.open(
        "ne_10m_admin_1_states_provinces_scale_rank_minor_islands.shp", 
        "w", 
        driver=source_driver,
        crs=source_crs,
        schema=out_schema) as output:
    counter = 0
    for poly in polygon_geoms:
        try:
            output.write({
                'geometry': mapping(poly),
                'properties': { 
                    'diss_me':  point_attr[matches[counter]]['diss_me'],
                    'adm1_code': point_attr[matches[counter]]['adm1_code'],
                    'sr_sov_a3': point_attr[matches[counter]]['sr_sov_a3'],
                    'sr_adm0_a3':   point_attr[matches[counter]]['sr_adm0_a3'],
                    'sr_gu_a3':  point_attr[matches[counter]]['sr_gu_a3'],
                    'iso_a2': point_attr[matches[counter]]['iso_a2'],
                    'adm0_sr':  point_attr[matches[counter]]['adm0_sr'],
                    'name':  point_attr[matches[counter]]['name'],
                    'admin':  point_attr[matches[counter]]['admin'],
                    'scalerank':  point_attr[matches[counter]]['scalerank'],
                    'datarank':  point_attr[matches[counter]]['datarank'],
                    'featurecla': point_attr[matches[counter]]['featurecla']
                }
            })
        except:
            output.write({
                'geometry': mapping(poly),
                'properties': { 
                    'diss_me':  -9999,
                    'adm1_code': 'ER-ERR',
                    'sr_sov_a3': 'ERR',
                    'sr_adm0_a3':  'ERR',
                    'sr_gu_a3':  'ERR',
                    'iso_a2': 'ER',
                    'adm0_sr':  100,
                    'name':  "Topology / Attribute Error",
                    'admin':  "Topology / Attribute Error",
                    'scalerank':  100,
                    'datarank':  100,
                    'featurecla': "Topology / Attribute Error"
                }
            })
        counter += 1

out_schema_error = {  'geometry': 'LineString', 'properties': { 'name': 'str' } }
# Dangles
if len(dangles) > 0:
    with fiona.open(
            "ne_10m_admin_1_states_provinces_scale_rank_minor_islands_dangles.shp", 
            "w", 
            driver=source_driver,
            crs=source_crs,
            schema=out_schema_error) as output:
        for f in dangles:
            output.write({
                'geometry': mapping(f),
                'properties': { 
                    'name':  'Dangle Error'
                }
            })

# Cuts
if len(cuts) > 0:
    with fiona.open(
            "ne_10m_admin_1_states_provinces_scale_rank_minor_islands_cuts.shp", 
            "w", 
            driver=source_driver,
            crs=source_crs,
            schema=out_schema_error) as output:
        for f in cuts:
            output.write({
                'geometry': mapping(f),
                'properties': { 
                    'name':  'Cut Error'
                }
            })

# Invalids
#out_schema_error2 = {  'geometry': 'Polygon', 'properties': { 'name': 'str' } }
if len(invalids) > 0:
    with fiona.open(
            "ne_10m_admin_1_states_provinces_scale_rank_minor_islands_invalids.shp", 
            "w", 
            driver=source_driver,
            crs=source_crs,
            schema=out_schema_error) as output:
        for f in invalids:
            output.write({
                'geometry': mapping(f),
                'properties': { 
                    'name':  'Invalid Error'
                }
            })