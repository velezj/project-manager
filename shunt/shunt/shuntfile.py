import logutils
logger = logutils.getLogger( __name__ )

import yaml
import hmap

SHUNT_FILENAME = "Shuntfile"

##============================================================================

##
# A Shuntfile object is just a path and an hmap
class Shuntfile( object ):

    ##
    # Creates new shutnfile with path and hmap (may be None)
    def __init__( self, path, hmap ):
        self.path = path
        self.hmap = hmap

##============================================================================

##
# Reads in a shuntfile into an hmap
def load_shuntfile( path ):
    with open( path ) as f:
        return Shuntfile( path,
                          yaml.load( f ) )

##============================================================================

##
# Gets a particular path from the shuntfile or returns default
def shuntfile_get( shuntfile, path, default ):
    if shuntfile.hmap is None:
        return default
    return hmap.hmap_get( shuntfile.hmap,
                          path,
                          default )

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
##============================================================================
##============================================================================
##============================================================================