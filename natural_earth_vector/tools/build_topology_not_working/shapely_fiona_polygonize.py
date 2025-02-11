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

with collection("../../10m_physical/ne_10m_minor_islands_coastline.shp", "r") as input:
    for line in input:
        lines.append(shape(line['geometry']))

# Build polygons from all input lines
polygon_geoms, dangles, cuts, invalids = polygonize_full(lines)

# Report stats
print len(polygon_geoms), '\t','polygons'
print len(dangles),       '\t','dangles'
print len(cuts ),         '\t','cuts'
print len(invalids),      '\t','invalids'


# Load the shapefile of points and convert it to shapely point objects
points = []
point_attr = []
#point_coords = []
with fiona.open(
        "../../10m_physical/ne_10m_minor_islands_label_points.shp", 
        "r") as input_label_points:
    source_crs = input_label_points.crs
    source_driver = input_label_points.driver
    #out_schema = input_label_points.schema # doesn't work because point > polygon
    
    for point in input_label_points:
        points.append(shape(point['geometry']))
        point_attr.append(point['properties'])
        
# Report
print str( len( points ) ) +     '\t' + 'label points'
#print str( len( point_attr ) ) + '\t' + 'label point attributes'

# TODO: This is redundant and should be rewriten
# Load the shapefile of points and convert it to shapely point objects
points_sf = shapefile.Reader("../../10m_physical/ne_10m_minor_islands_label_points.shp")
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
print len(matches), '\t','matches'
#print matches

# Report debug information
oops = len(polygon_geoms) - len(matches)
if oops > 0:
    print oops,'\t','polygons missing attributes'
if oops < 0:
    print oops,'\t','more attributes than polygons (ambiguous matches)'

# Setup export schema
out_schema = { 'geometry': 'Polygon', 'properties': { 'featurecla': 'str', 'scalerank': 'float' } }

# Export polygons to ESRI Shapefile format
with fiona.open(
        "ne_10m_minor_islands.shp", 
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
                    'featurecla': point_attr[matches[counter]]['featurecla'],
                    'scalerank' : point_attr[matches[counter]]['scalerank']
                }
            })
        except:
            output.write({
                'geometry': mapping(poly),
                'properties': { 
                    'featurecla': "Topology / Attribute Error",
                    'scalerank' : 100
                }
            })
        counter += 1