import logutils
logger = logutils.getLogger( __name__ )

import project_paths
import shuntfile

import pathlib
import os
import os.path
import subprocess

import jinja2

##============================================================================

##
# Processes a Shuntfile and creates materializes all the views
def materialize_views( shuntfile_path, parents = None ):

    logger.info( "Materializing Shuntfile '{0}'".format(
        shuntfile_path ) )

    # ok, load the shuntfile
    sf = shuntfile.load_shuntfile( shuntfile_path )

    # validate that the shuntfile has the needed structure
    validate_shuntfile( sf )
    logger.info( "Shuntfile at '{0}' valid!".format( shuntfile_path ) )

    # now, grab all of the wanted views
    logger.info( "Materializing views" )
    for view in shuntfile.shuntfile_get( sf, ['project','views'], [] ):

        # materialize the view
        logger.info( "Materialize view '{0}'".format( view ) )
        res = _materialize_view(
            project_paths.find_all_template_paths(shuntfile_path),
            project_paths.materialize_path( sf, parents ),
            view )
        logger.info( "Materialized '{0}' to '{1}'".format(
            view, res ) )

    # ok, now grab all of hte subprojects and recurse
    logger.info( "Processing subprojects" )
    for proj in shuntfile.shuntfile_get( sf, ['project','subprojects'],[]):
        new_parents = parents
        if new_parents is None:
            new_parents = []
        new_parents = [ sf ] + new_parents
        proj_path = ( pathlib.Path( shuntfile_path ) / ".." / proj / shuntfile.SHUNT_FILENAME ).resolve().as_posix()
        logger.info( "Processing Subproject '{0}'".format( proj ) )
        materialize_views( proj_path, parents = new_parents )

    # done message log
    logger.info( "Done Materializing Shutnfile '{0}'".format( shuntfile_path ) )

##============================================================================

##
# Actually materialize a single view.
# This will run the jinja2 template defined by hte view and
# output hte result into the materialzation path directory, creating
# it if need be
def _materialize_view( template_paths,
                       materialize_path,
                       view_name ):

    # ok, we want to take the template paths and process any which
    # need processing.
    # This is because we allow git,s3 and other URL type paths.
    template_paths = [ _materialize_path( p,
                                          materialize_path )
                       for p in template_paths ]

    # ok, create a jinja2 environment with the given template paths
    env = jinja2.Environment(
        loader = jinja2.FileSystemLoader( template_paths,
                                          followlinks=True ) )
    logger.info( "_materialize_view: jinja2 template paths set to '{0}'".format(
        template_paths ) )

    # grab the template file using hte view name
    template = env.get_template( view_name )

    # create directory if need be
    materialize_path = pathlib.Path( materialize_path ).resolve()
    if not materialize_path.exists():
        materialize_path.mkdir( parents=True )
        materialize_path = materialize_path.as_posix()
        logger.info( "  creating materialziation directiry: '{0}'".format(
            materialize_path ) )

    # ok, render hte template to a file with the name
    mpath = ( pathlib.Path( materialize_path ) / view_name ).resolve().as_posix()
    with open( mpath, 'w' ) as f:
        f.write( template.render() )
    logger.info( "  rendered template for view '{1}' into '{0}'".format(
        mpath,
        view_name ) )

    return mpath

##============================================================================

##
# Given a path and a materialize_path,
# materializes any paths needed and returns the resulting set of path.
#
# This handles URL/URI style paths by downloading them (recursively)
# into the materialize_path if the materialize_path does not exists
def _materialize_path( path,
                        materialize_path,
                        force=False ):

    # string paths are trated as already materialized
    if isinstance( path, str ):
        return path

    # ok, ensure that path is astructure
    if not isinstance( path, dict ):
        msg = "Invalid path object. Expected string or dictionary but got type={0} '{1}'".format(
            type(path),
            path )
        raise ValueError( msg )

    # makre sure we at least have a source and destination
    if 'source' not in path or 'destination' not in path:
        msg = "Malformed path object. Paths need to have 'source' and 'destination' keys defined. Path = '{0}'".format( path )
        raise ValueError( msg )

    # ok, lookup the source
    source = path['source']
    if source not in KNOWN_PATH_MATERIALIZATION_SOURCES:
        msg = "Invalid path source '{0}'. We don't know how to materialize such a path".format( source )
        raise ValueError( msg )

    # check if destination already there and not forcing
    if ( pathlib.Path( materialize_path ) / path['destination'] ).exists() and not force:
        logger.info( "Skipping materialization of path '{0}' because destination exists and not forcing".format( path ) )
        return ( pathlib.Path(materialize_path) / path['destination'] ).resolve().as_posix()

    # ok, grab the materialzer and run it
    return KNOWN_PATH_MATERIALIZATION_SOURCES[ source ]( path,
                                                         materialize_path,
                                                         force = force )

##============================================================================

##
# Materialzie a git path
def _git_materialize_path( path,
                           materialize_path,
                           force=False ):

    logger.info( "Materializing GIT path: '{0}' into '{1}'".format(
        path, materialize_path ) )
    donep = subprocess.run( ['git','clone'] + path['args'],
                            cwd = materialize_path,
                            check = True )
    return (pathlib.Path(materialize_path) / path['destination'] ).resolve().as_posix()
    
##============================================================================

##
# Materialzie an s3 path
def _s3_materialize_path( path,
                          materialize_path,
                          force=False ):

    logger.info( "Materializing S3 path: '{0}' into '{1}'".format(
        path, materialize_path ) )
    donep = subprocess.run( ['aws','s3'] + path['args'],
                            cwd = materialize_path,
                            check = True )
    return (pathlib.Path(materialize_path) / path['destination'] ).resolve().as_posix()

##============================================================================

##
# A mapping from source to path materalizer function for paths
KNOWN_PATH_MATERIALIZATION_SOURCES = {
    'git' : _git_materialize_path,
    's3' : _s3_materialize_path,
}

##============================================================================

##
# Validates that a given shuntfile object has the required structure
# Raises error if not valid
def validate_shuntfile( sf ):
    pass

##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
