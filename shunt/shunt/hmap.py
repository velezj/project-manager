import logging
logger = logging.getLogger( __name__ )


##
# Interface functions for Hiearchichal Maps (hmaps)
# which are jsut dictionaries-of-dictionaries :)

##============================================================================

##
# Returns true iff the given object is a structured key with
# given delimiter
def is_structured_key( x, delim='/' ):
    return isinstance( x, str ) and delim in x

##============================================================================

##
# Convert from a structured key to a path.
# A structured key is just a delimited single-string key
# much like a file system path or url :)
def structured_key_to_path( sk, delim='/' ):
    def _numerate(x):
        if isinstance( x , str ) and x.startswith('[') and x.endswith(']'):
            try:
                return int(x[1:-1])
            except:
                return x
        return x            
    return list(map(_numerate, sk.split( delim )))

##============================================================================

##
# Take a path of a structured key and return a path
def ensure_path( sk_or_path, delim='/' ):
    if isinstance( sk_or_path, str ):
        return structured_key_to_path( sk_or_path, delim=delim )
    return sk_or_path

##============================================================================

##
# Traverse a hiearchical map (dict of dict) structure with a path
# (a list of keys).
# This will return the parent dictionary and key for the last
# item in the path or None,None if the path is not valid
#
# This will *change* the given hmap (potentially) since it will
# *create* the hmap structure down the path if it was not
# previously created in the hmap
def hmap_probe( hmap, path ):
    path = ensure_path( path )
    if path is None or hmap is None or len(path) < 1:
        return None, None
    if len(path) == 1:
        return hmap, path[0]
    next_element_type = dict
    if isinstance( path[1], int ):
        next_element_type = list
    if isinstance( path[0], int ) and isinstance( hmap, list ):
        while len( hmap ) < path[0]:
            hmap.append( None )
        if len(hmap) == path[0]:
            hmap.append( next_element_type() )
    else:
        if path[0] not in hmap:
            hmap[ path[0] ] = next_element_type()
    return hmap_probe( hmap[ path[0] ], path[1:] )

##============================================================================

##
# Get the value for a path from an hmap
# Or returns the given default value.
# This may change the given hmap by probing it.
def hmap_get( hmap, path, default ):
    node, key = hmap_probe( hmap, path )
    if node is None or ( isinstance(node,dict) and key not in node ) or ( isinstance( node, list ) and len(node) <= key):
        return default
    return node[ key ]

##============================================================================

##
# Sets the value of the given path in an hmap to the
# given value.
# This will create the path layers if need be
def hmap_set( hmap, path, value ):
    node, key = hmap_probe( hmap, path )
    if node is None:
        raise ValueError( "Could not probe hmap, returned None. This usually means that the hmap itself was None!" )
    if isinstance( node, dict ):
        old = node.get( key, None )
        node[ key ] = value
    elif isinstance( node, list ):
        old = None
        if key < len(node):
            old = node[ key ]
        while len(node) <= key:
            node.append( None )
        node[ key ] = value
    else:
        raise ValueError( "Could not probe hmap, returned neither a dict or list. This usually means that hte hamp itself was malformed" )    
    return old

##============================================================================

##
# returns true if the given path has a set value in the given hmap
def hmap_has_path( hmap, path ):
    node, key = hmap_probe( hmap_probe, path )
    return node is not None and (
           ( isinstance(node,dict) and key in node )
        or ( isinstance(node,list) and key < len(node) ) )


##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
