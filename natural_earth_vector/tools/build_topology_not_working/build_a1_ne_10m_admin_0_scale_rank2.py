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
from shapely.ops import unary_union

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

verbose = True

# Store all lines from all input sources
lines = []
single_lines = []
no_dangle_single_lines = []
line_start_and_end_nodes = []
line_start_and_end_nodes_buffers = []
gap_fillers = []
            
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

    print "splitting multipart lines into single part lines"
    for line in lines:
        # Gather the terminal nodes of each line
        if line.type == "MultiLineString":
            for line_part in line.geoms:
                if line_part.is_valid:
                    single_lines.append(line_part)
                else:
                    single_lines.append(line_part.buffer(0))
        else:
            if line.is_valid:
                single_lines.append(line)
            else:
                single_lines.append(line.buffer(0))

    # Report stats
    print len(single_lines),         '\t','split lines'

#     for line in single_lines:
#         #round the start and end nodes to 
#         line.coords[0][0] = round(line.coords[0][0], 4)
#         line.coords[0][1] = round(line.coords[0][1], 4)
#         line.coords[len(line.coords)-1][0] = round(line.coords[len(line.coords)-1][0], 4)
#         line.coords[len(line.coords)-1][1] = round(line.coords[len(line.coords)-1][1], 4)

#     
#     print "snapping line (1)..."
#     
#     # enable faster spatial lookups
#     tree = STRtree(single_lines)
# 
#     # Init tracking vars
#     line_counter = 0
#     total_lines = len(single_lines)
#     start_time = time.time()
# 
#     # Deal with overshoots (dangles)
#     # http://wiki.wildsong.biz/index.php/Finding_Intersections_with_Python
#     for line in single_lines:
#         line_counter += 1
#         elapsed_time = time.time() - start_time
# #         if line_counter % 1000 == 0 or line_counter == 1 or elapsed_time > 2000:
#         print "\t", line_counter, "of", total_lines
#         start_time = time.time()
#         
#         # use lines rtree to speed things up
#         nearby = tree.query(line)
#         
#         print len(nearby), "nearby lines"
#     
#         # Go thru all the nearby lines and calculate rays from the point to those lines
#         for near in nearby:
#             print near.type, line.type, near.length, line.length
# 
#             if line.crosses(near):
#                 # find the intersection
#                 print "lines cross"
#                 intersection = line.intersection(near)
#                 print near.type
# 
#                 if len(intersection) == 1 and intersection[0].type == "Point":
#                     # is the start or end node closer to the intersection
#                     start_to_intersection = LineString([(line.coords[0].x,line.coords[0].y), (intersection[0].x,intersection[0].y)])
#                     end_index = len(line.coords) - 1
#                     end_to_intersection = LineString([(line.coords[end_index].x,line.coords[end_index].y), (intersection[0].x,intersection[0].y)])
#                     
#                     print line.length, "line length before"
#                     if start_to_intersection < end_to_intersection:
#                         line.coords[0] = intersection[0]
#                     else:
#                         line.coords[end_index] = intersection[0]
# 
#                     print line.length, "line length after"
#                 else:
#                     print "\t","complex intersection"

    print "Building polygons..."

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
        
    # Build polygons from all input lines
    polygon_geoms, dangles, cuts, invalids = polygonize_full(single_lines)

    # Report stats
    print len(polygon_geoms), '\t','output polygons'
    print '\terrors:'
    print '\t',len(dangles),  '\t','dangles'
    print '\t',len(cuts ),    '\t','cuts'
    print '\t',len(invalids), '\t','invalids'


    print "Filling the gaps..."

    # assumes decimal degrees
    snaping_dist = 0.0001

    # How many of those lines touch another line?
    print "Snapping lines within", snaping_dist
    
    # enable faster spatial lookups
    tree = STRtree(single_lines)

    # Gather the terminal nodes of each cut line
    for this_cut in cuts:
        terminal_node = len(this_cut.coords) - 1
        line_start_and_end_nodes.append( [Point(this_cut.coords[0]), Point(this_cut.coords[terminal_node])] )
        line_start_and_end_nodes.append( [Point(this_cut.coords[terminal_node]), Point(this_cut.coords[0])] )
    
    # Also gather the terminal nodes of each dangle line
    for this_dangle in dangles:
        terminal_node = len(this_dangle.coords) - 1
        line_start_and_end_nodes.append( [Point(this_dangle.coords[0]), Point(this_dangle.coords[terminal_node])] )
        line_start_and_end_nodes.append( [Point(this_dangle.coords[terminal_node]), Point(this_dangle.coords[0])] )

    # Init tracking vars
    point_counter = 0
    total_points = len(line_start_and_end_nodes)
    start_time = time.time()
    
    # For each terminal node, build a "gap line" to it's nearest neighboring line
    for this_pt in line_start_and_end_nodes:
        point_counter += 1
        elapsed_time = time.time() - start_time
        if point_counter % 10 == 0 or point_counter == 1 or elapsed_time > 2000:
            print "\t", point_counter, "of", total_points
        start_time = time.time()
        
        buffer = this_pt[0].buffer(snaping_dist)
        line_start_and_end_nodes_buffers.append(buffer)
        
        # use lines rtree to speed things up
        nearby = tree.query(buffer)
        #print "\t", len(nearby), "lines nearby"
        
        gaps_to_filter = []
        
        for near in nearby:
            found_near_line_node = False
            near_line_node = None
            for coord in near.coords:
                if buffer.contains(Point(coord)):
                    found_near_line_node = True
                    near_line_node = Point(coord)
                    break
                    
            if found_near_line_node:
                #print "found_near_line_node"
                gap = LineString([(this_pt[0].x,this_pt[0].y), (near_line_node.x,near_line_node.y)])
            else:
                #print "projected_terminal_point"
                # http://stackoverflow.com/questions/24415806/coordinate-of-the-closest-point-on-a-line
                # Now combine with interpolated point on line
                terminal_node = len(near.coords) - 1
                projected_terminal_point = near.interpolate(near.project(this_pt[0]))

                gap = LineString([(this_pt[0].x,this_pt[0].y), (projected_terminal_point.x,projected_terminal_point.y)])
            
            if gap.length > 0 and gap.length <= snaping_dist:
                gaps_to_filter.append( gap )
        
        # Find the shorted line from the point to the nearby lines
        if len(gaps_to_filter) > 0:
            min_length = gaps_to_filter[0].length
            min_gap_index = 0
            i = 0
            for gap in gaps_to_filter:
                if gap.length < min_length:
                    min_gap_index = i
                i += 1
            
            # Store the shortest line
            gap_fillers.append( gaps_to_filter[min_gap_index] )

    # Report stats
    print len(gap_fillers),         '\t','gap filler lines'
    
    for gap in gap_fillers: 
        single_lines.append( gap )

    # Report stats
    print len(single_lines),         '\t','single lines (with gap fillers)'

    print "Building polygons, again..."

    # Build polygons from all input lines, again
    polygon_geoms, dangles, cuts, invalids = polygonize_full(single_lines)

    # Report stats
    print len(polygon_geoms), '\t','output polygons'
    print '\terrors:'
    print '\t',len(dangles),  '\t','dangles'
    print '\t',len(cuts ),    '\t','cuts'
    print '\t',len(invalids), '\t','invalids'


    # Report
    print str( len( points ) ) +     '\t' + 'input label points'
    #print str( len( point_attr ) ) + '\t' + 'label point attributes'

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
        for j in idx.intersection( point_coords[i] ):
            try:
                # Verify that point is within the polygon itself not just the bounding box
                if points[i].within(polygon_geoms[j]):
                    #print "Match found! ", j
                    temp=j
                    count += 1
                    #break
            except: 
                #print "\t","funky geom?"
                pass
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
                
    # Gap Lines
    if len(gap_fillers) > 0:
        with fiona.open(
                "ne_10m_admin_0_scale_rank_minor_islands_gap_lines.shp", 
                "w", 
                driver=source_driver,
                crs=source_crs,
                schema=out_schema_error) as output:
            for f in gap_fillers:
                output.write({
                    'geometry': mapping(f),
                    'properties': { 
                        'name':  'Gap line'
                    }
                })

    # Node buffers
    out_schema_error2 = {  'geometry': 'Polygon', 'properties': { 'name': 'str' } }
    if len(line_start_and_end_nodes_buffers) > 0:
        with fiona.open(
                "ne_10m_admin_0_scale_rank_minor_islands_node_buffers.shp", 
                "w", 
                driver=source_driver,
                crs=source_crs,
                schema=out_schema_error2) as output:
            for f in line_start_and_end_nodes_buffers:
                output.write({
                    'geometry': mapping(f),
                    'properties': { 
                        'name':  'Node buffer'
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