# shapefile reading, writing
import fiona
from fiona import collection

# frienly OGR and GDAL utils
from shapely.geometry import shape, mapping, Point
from shapely.geometry import Polygon, LineString
from shapely.ops import polygonize_full
#https://github.com/Toblerity/Shapely/blob/master/docs/manual.rst#prepared-geometry-operations
from shapely.prepared import prep
from shapely.ops import snap
from shapely.strtree import STRtree

# Basic math functions
from math import cos, sin, pi

# Speed up spatial join with a spatial index
from rtree import index
# assumes you've also installed: spatialindex
# eg on a Mac using Homebrew: brew install spatialindex

# pyshp packages for reading/writing ESRI format shapefiles
import shapefile

import time

# Init the export properties schema
#schema = {}
source_crs = {}
source_driver = {}

# Store all lines from all input sources
lines = []            
            
if __name__ == '__main__':
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
    # Admin 0 Boundary Lines for Disputed Areas
    with fiona.open(
            "../../10m_cultural/ne_10m_admin_0_boundary_lines_disputed_areas.shp", 
            "r") as input:
        for line in input:
            lines.append(shape(line['geometry']))
    # Admin 0 Map Units
    with fiona.open(
            "../../10m_cultural/ne_10m_admin_0_boundary_lines_map_units.shp", 
            "r") as input:
        for line in input:
            lines.append(shape(line['geometry']))
    # Admin 0 Seams
    with fiona.open(
            "../../10m_cultural/ne_10m_admin_0_seams.shp", 
            "r") as input:
        for line in input:
            lines.append(shape(line['geometry']))
    # Admin 0 Boundary Lines Land
    with fiona.open(
            "../../10m_cultural/ne_10m_admin_0_boundary_lines_land.shp", 
            "r") as input:
        for line in input:
            lines.append(shape(line['geometry']))

    # Report stats
    print len(lines),         '\t','input lines'

    line_counter = 0
    single_lines = []
    
    print "splitting multipart lines into single part lines"
    for line in lines:
        line_counter += 1
        #print "\t", line_counter, "of", total_lines
        
        # Gather the terminal nodes of each line
        if line.type == "MultiLineString":
            for line_part in line.geoms:
                single_lines.append(line_part)
        else:
            single_lines.append(line)

    # Report stats
    print len(single_lines),         '\t','split lines'

    # assumes decimal degrees
    snaping_dist = 0.000001

    # How many of those lines touch another line?
    print "Snapping lines within", snaping_dist
    
    verbose = True
    line_counter = 0
    total_lines = len(single_lines)
    line_start_and_end_nodes = []

    # enable faster spatial lookups
    tree = STRtree(single_lines)

    # init the time counter
    start_time = time.time()
    
    for line in single_lines:
        line_counter += 1
        elapsed_time = time.time() - start_time
        if line_counter % 100 == 0 or line_counter == 1 or elapsed_time > 2000:
            print line_counter, "of", total_lines
            
        #rest time counter
        start_time = time.time()
        
        # Gather the terminal nodes of each line
        if line.type == "MultiLineString":
            for line_part in line.geoms:
                terminal_node = len(line_part.coords) - 1
                line_start_and_end_nodes.append(Point( line_part.coords[0] ))
                line_start_and_end_nodes.append(Point( line_part.coords[terminal_node] ))
        else:
            terminal_node = len(line.coords) - 1
            line_start_and_end_nodes.append(Point( line.coords[0] ))
            line_start_and_end_nodes.append(Point( line.coords[terminal_node] ))

        for this_pt in line_start_and_end_nodes:
            #i = 0
            #found_intersection = False
            
            nearby = tree.query(this_pt.buffer(snaping_dist))
            
            #print "\t", len(nearby), "lines nearby"
            
            j = 0
            for near in nearby:
                if near.equals(line) is False:
                    result = snap(line, near, snaping_dist)
                    line.coords = result.coords
                    j += 1
                    #print "\t\tsnapping to", j
                    #one and done?
                    break
        
#             
#             for other_line in lines:
#                 #print i
#                 i += 1
# 
#                 if line.equals(other_line) is False:    
#                     #speedup
#                     prepared_pt = prep(this_pt)
#                     if prepared_pt.intersects(other_line): 
#                         found_intersection = True
#                         if verbose: print "\tHit! ", i
#                         break
#             
#             if found_intersection is False:
#                 j = 0
#                 for other_line in lines:
#                     #print '\t', j
#                     j += 1
# 
#                     if line.equals(other_line) is False:
#                         buffered = this_pt.buffer(snaping_dist)
#                         prepared_buffer = prep(buffered)
#                         
#                         if prepared_buffer.intersects(other_line): 
#                             found_intersection = True
# 
#                             # http://stackoverflow.com/questions/24415806/coordinate-of-the-closest-point-on-a-line
#                             # Now combine with interpolated point on line
#                             projected_terminal_point = other_line.interpolate(other_line.project(this_pt))
#                             print(projected_terminal_point)  # POINT (5 7)
#                             
#                             line.extend(projected_terminal_point)
# 
#                             if verbose: print "\tNearby hit! at ", i, ":", j
# 
#                             break

    # Load the shapefile of points and convert it to shapely point objects
    points = []
    point_attr = []
    #point_coords = []
    with fiona.open(
            "../../10m_cultural/ne_10m_admin_0_label_points.shp", 
            "r") as input_label_points:
        source_crs = input_label_points.crs
        source_driver = input_label_points.driver
        out_schema = input_label_points.schema # doesn't work because point > polygon
    
        for point in input_label_points:
            points.append(shape(point['geometry']))
            point_attr.append(point['properties'])
        
    # Report
    print str( len( points ) ) +     '\t' + 'input label points'
    #print str( len( point_attr ) ) + '\t' + 'label point attributes'

    # Build polygons from all input lines
    polygon_geoms, dangles, cuts, invalids = polygonize_full(single_lines)

    # Report stats
    print len(polygon_geoms), '\t','output polygons'
    print '\terrors:'
    print '\t',len(dangles),  '\t','dangles'
    print '\t',len(cuts ),    '\t','cuts'
    print '\t',len(invalids), '\t','invalids'

    # TODO: This is redundant and should be rewriten
    # Load the shapefile of points and convert it to shapely point objects
    points_sf = shapefile.Reader("../../10m_cultural/ne_10m_admin_0_label_points.shp")
    point_shapes = points_sf.shapes()
    point_coords= [q.points[0] for q in point_shapes ]

    # http://stackoverflow.com/questions/14697442/faster-way-of-polygon-intersection-with-shapely
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
    total_matches = 0
    for i in range(len(points)): # Iterate through each point
        temp= None
        count = 0
        #print "Point ", i
        # Iterate only through the bounding boxes which contain the point
    #     for j in idx.intersection( point_coords[i] ):
    #         # Verify that point is within the polygon itself not just the bounding box
    #         if points[i].within(polygon_geoms[j]):
    #             #print "Match found! ", j
    #             temp=j
    #             count += 1
    #             #break
        if count > 0:
            total_matches += 1
        matches.append([temp,count]) # Either the first match found, or None for no matches


    # Report stats
    print total_matches, '\t','points have matching polygons'
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
    # out_schema = {  'geometry': 'Polygon', 
    #                 'properties': { 
    #                     'sr_sov_a3': 'str:3', 
    #                     'sr_adm0_a3': 'str:3', 
    #                     'sr_subunit': 'str:100', 
    #                     'sr_su_a3': 'str:3', 
    #                     'sr_brk_a3': 'str:3', 
    #                     'sr_br_name': 'str:100', 
    #                     'scalerank': 'float', 
    #                     'featurecla': 'str:50' } }

    # We want to use the same schema as the output, and record the number of matches
    out_schema['geometry'] = 'Polygon'
    out_schema['properties'][u'matches'] = 'int'

    # Export polygons to ESRI Shapefile format
    with fiona.open(
            "ne_10m_admin_0_scale_rank_minor_islands.shp", 
            "w", 
            driver=source_driver,
            crs=source_crs,
            schema=out_schema) as output:
        counter = 0
        for poly in polygon_geoms:
            attr = None
            point_counter = 0
            matched = 0
            total_matched = 0
            for point in matches:
                if point[0] == counter:
                    attr = point_counter
                    matched = point[1]
                    total_matched += 1
                    #break
                point_counter += 1
            
            try:
                #print point_attr[matches[attr][0]]['sr_br_name']
                output.write({
                    'geometry': mapping(poly),
                    'properties': { 
                        u'sr_sov_a3':  point_attr[attr]['sr_sov_a3'],
                        u'sr_adm0_a3': point_attr[attr]['sr_adm0_a3'],
                        u'sr_subunit': point_attr[attr]['sr_subunit'],
                        u'sr_gu_a3':   point_attr[attr]['sr_gu_a3'],
                        u'sr_su_a3':   point_attr[attr]['sr_su_a3'],
                        u'sr_brk_a3':  point_attr[attr]['sr_brk_a3'],
                        u'sr_br_name': point_attr[attr]['sr_br_name'],
                        u'scalerank':  point_attr[attr]['scalerank'],
                        u'featurecla': point_attr[attr]['featurecla'],
                        u'matches':    total_matched
                    }
                })
            except:
                output.write({
                    'geometry': mapping(poly),
                    'properties': { 
                        u'sr_sov_a3':  "err",
                        u'sr_adm0_a3': "err",
                        u'sr_subunit': "Topology / Attribute Error",
                        u'sr_gu_a3':   "err",
                        u'sr_su_a3':   "err",
                        u'sr_brk_a3':  "err",
                        u'sr_br_name': "Topology / Attribute Error",
                        u'scalerank' : 100,
                        u'featurecla': "Topology / Attribute Error",
                        u'matches':    0
                    }
                })
            counter += 1

    out_schema_error = {  'geometry': 'LineString', 'properties': { 'name': 'str' } }
    # Dangles
    if len(dangles) > 0:
        with fiona.open(
                "ne_10m_admin_0_scale_rank_minor_islands_dangles.shp", 
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
                "ne_10m_admin_0_scale_rank_minor_islands_cuts.shp", 
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
                "ne_10m_admin_0_scale_rank_minor_islands_invalids.shp", 
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
                
    if len(single_lines) > 0:
        with fiona.open(
                "ne_10m_admin_0_scale_rank_minor_islands_single_lines.shp", 
                "w", 
                driver=source_driver,
                crs=source_crs,
                schema=out_schema_error) as output:
            for f in single_lines:
                output.write({
                    'geometry': mapping(f),
                    'properties': { 
                        'name':  'Single line'
                    }
                })
