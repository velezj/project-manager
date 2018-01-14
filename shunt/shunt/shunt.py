import logutils
logger = logutils.getLogger( __name__ )

import project_paths
import shuntfile

import pathlib
import os
import os.path
import subprocess
import shutil

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

    # ensure materiale directory exists and is empty
    materialize_path = project_paths.materialize_path( sf, parents )
    if pathlib.Path( materialize_path ).exists():
        logger.info( "Emptying previous materialization directory '{0}'".format( materialize_path ) )
        shutil.rmtree( materialize_path )
    materialize_path = ensure_path( materialize_path )
    
    # ok, we want to take the template paths and process any which
    # need processing.
    # This is because we allow git,s3 and other URL type paths.
    logger.info( "Materializing template paths" )
    template_paths = project_paths.find_all_template_paths(shuntfile_path)
    template_paths = [ _materialize_path( p,
                                          materialize_path )
                       for p in template_paths ]
    logger.info( "Template paths: {0}".format( template_paths ) )


    # ok, grab all of the resources and copy them
    logger.info( "Copying resources" )
    for res in shuntfile.shuntfile_get( sf, ['project','resources'], [] ):

        # copy the resource
        _copy_resource( template_paths,
                        materialize_path,
                        res )

    # now, grab all of the wanted views
    logger.info( "Materializing views" )
    for view in shuntfile.shuntfile_get( sf, ['project','views'], [] ):

        # materialize the view
        logger.info( "Materialize view '{0}'".format( view ) )
        res = _materialize_view(
            template_paths,
            materialize_path,
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



    # ok, create a jinja2 environment with the given template paths
    env = jinja2.Environment(
        loader = jinja2.FileSystemLoader( template_paths,
                                          followlinks=True ) )
    logger.info( "_materialize_view: jinja2 template paths set to '{0}'".format(
        template_paths ) )

    # grab the template file using hte view name
    template = env.get_template( view_name )

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

##
# Copy a resource into hte materialization path
def _copy_resource( template_paths,
                    materialize_path,
                    res ):

    # get source path
    source_path = None
    if isinstance( res, str ):
        source_path = pathlib.Path( res )
    else:
        source_path = res.get( 'source', None )

    # resolve the source path to an actual path of a resource that exists
    source_path = resolve_path( template_paths,
                                source_path )
    if source_path is None:
        msg = "Unable to copy resource '{0}': path does not exists in any of {1}".format( res, template_paths )
        raise ValueError( msg )

    # get hte target path
    target_path = None
    if isinstance( res, str ):
        target_path = res
    else:
        target_path = res.get( "target", None )
    if target_path is None:
        msg = "Unable to copy resource '{0}', target path is not defined".format(res)
        raise ValueError( msg )

    # resolve the target path
    if pathlib.Path( target_path ).is_absolute():
        target_path = pathlib.Path( materialize_path ).joinpath( pathlib.Path( target_path ).name ).resolve().as_posix()
    else:
        target_path = pathlib.Path( materialize_path ).joinpath( target_path ).resolve().as_posix()

    # ok, copy the file
    if pathlib.Path( source_path ).is_dir():
        shutil.copytree( source_path,
                        target_path )
    else:
        shutil.copyfile( source_path,
                         target_path )
    logger.info( "copied resource '{0}' TO -> '{1}'".format(
        source_path,
        target_path ) )

##============================================================================

##
# Given a set of paths and a relative path,
# searches the paths in order and returns the first which includes
# a file or directory at the given relative path
def resolve_path( paths,
                  relative_path ):

    # check arguments for None which results in None
    if relative_path is None:
        return None
    if paths is None:
        return None

    # if we are given an absoulte path, return it if it exists
    # otherwise return None
    if pathlib.Path( relative_path ).is_absolute():
        if pathlib.Path( relative_path ).exists():
            return pathlib.Path( relative_path ).resolve().as_posix()
        else:
            return None

    # Ok, check the path relative to the set of paths in order
    # If it exists then return it as the path
    for p in paths:
        if pathlib.Path( p ).joinpath( relative_path ).exists():
            return pathlib.Path( p ).joinpath( relative_path ).resolve().as_posix()
    return None

##============================================================================

##
# make sure a given directory exists
def ensure_path( p ):
    materialize_path = pathlib.Path( p ).resolve()
    if not materialize_path.exists():
        materialize_path.mkdir( parents=True )
        materialize_path = materialize_path.as_posix()
        logger.info( "  creating directory: '{0}'".format(
            materialize_path ) )
    return materialize_path

##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================

if __name__ == '__main__':

    import logging
    logging.basicConfig( level=logging.INFO )

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument( 'shuntfile' )

    args = parser.parse_args()

    sf_path = args.shuntfile
    materialize_views( sf_path )
