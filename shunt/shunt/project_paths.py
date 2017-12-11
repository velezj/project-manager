import logutils
logger = logutils.getLogger( __name__ )

import pathlib
import shuntfile

##============================================================================

TEMPLATE_FOLDER_NAME = "shunts"
MATERIALIZE_FOLDER_NAME = "materialized_views"

##============================================================================

##
# Find all of the possible paths for templates in a project.
#
# This will return:
#   List[ paths ] for all template paths
#   Map[ prefix => path ] for all template paths
def find_all_template_paths( start_path = '.' ):

    # ok, first we will find the "root" directory which is the
    # topmost directory with a shuntfile
    root_path, shuntfile_path = find_shunt_root_path( start_path = start_path )

    # Ok, find all the template paths from the root
    implicit_template_paths = find_all_template_paths_from_root( root_path )

    # read in any template paths explicitly set in hte shuntfile
    explicit_template_paths = extract_template_paths_from_shuntfile( shuntfile_path )

    return explicit_template_paths + implicit_template_paths

##============================================================================

##
# Extract hte explicitly set template paths from the shutnfile
def extract_template_paths_from_shuntfile( shuntfile_path ):
    return shuntfile.shuntfile_get(
        shuntfile.load_shuntfile( shuntfile_path ),
        [ 'project', 'shunt_paths' ],
        [] )

##============================================================================

##
# Finds the root directory for a shunt project given a starting
# path (defaults tp '.' )
def find_shunt_root_path( start_path, original_start_path=None ):

    # set original start path if first given
    if original_start_path is None:
        original_start_path = start_path

    # ok, see if there is a Shuntfile at starting path
    start_path_p = pathlib.Path( start_path ).resolve()
    if ( start_path_p / shuntfile.SHUNT_FILENAME ).exists():
        return start_path_p.as_posix(), ( start_path_p / shuntfile.SHUNT_FILENAME ).as_posix()

    parent = start_path_p.resolve().parent
    if parent is None or parent == start_path_p or parent == pathlib.Path():
        msg = "Unable ti find a '{0}' file in ancestry of starting path '{1}' (real '{2}'). This usually means the file is missing for running the shunt system, or it has been started from hte wrong working idrectory!".format( shuntfile.SHUNT_FILENAME, original_start_path, pathlib.Path( original_start_path ).resolve().as_posix() )
        raise RuntimeError( msg )
    return find_shunt_root_path( parent.as_posix(), original_start_path=original_start_path )
    

##============================================================================

##
# Finds all of the template paths and prefixes given the root node for
# a shunt project
def find_all_template_paths_from_root( root_path, prefix=None ):

    # Now we will look for any template folders
    root_p = pathlib.Path( root_path )
    template_paths = []
    for child in root_p.iterdir():
        if not child.is_dir():
            continue
        if child.name == TEMPLATE_FOLDER_NAME:

            # ok, found a templates folder
            # Add the folder path
            template_paths.append( child.as_posix() )

        else:

            # ok, recurse down to find more templates :)
            child_paths = find_all_template_paths_from_root( child.as_posix(), prefix=None )
            template_paths.extend( child_paths )

    return template_paths

##============================================================================

##
# Returns the materialization path for a shuntfile given the
# shutnfile object and a list of parent shuntfiles (may be None)
def materialize_path( sf, parents ):

    # ok, check if this shuntfile has a setting itself
    mpath = shuntfile.shuntfile_get( sf, ['project','materialize_path'], None )
    if mpath is not None:
        mpath = pathlib.Path( mpath )
        if not mpath.is_absolute():
            return mpath.relative_to( sf.path ).resolve().as_posix()
        return mpath.resolve().as_posix()

    # ok, no explicit path defined, check parents
    if parents is not None and len(parents) > 0:
        return materialize_path( parents[0], parents[1:] )

    # ok, now explicit and now parents, materialize to default
    # locations
    return ( pathlib.Path( sf.path ).parent / MATERIALIZE_FOLDER_NAME ).resolve().as_posix()

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
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
