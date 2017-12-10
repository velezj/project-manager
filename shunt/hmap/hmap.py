import logging
logger = logging.getLogger( __name__ )

import copy
import tempfile
import os

import jinja2
import yaml

##
# Interface functions for Hiearchichal Maps (hmaps)
# which are jsut dictionaries-of-dictionaries :)


TEMPLATE_HANDLEBAR_START = "{{"
TEMPLATE_HANDLEBAR_END = "}}"
JINJA_VARIABLE_KEY = "_"

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
        try:
            return int(x)
        except:
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
    if path[0] not in hmap:
        hmap[ path[0] ] = {}
    return hmap_probe( hmap[ path[0] ], path[1:] )

##============================================================================

##
# Get the value for a path from an hmap
# Or returns the given default value.
# This may change the given hmap by probing it.
def hmap_get( hmap, path, default ):
    node, key = hmap_probe( hmap, path )
    if node is None or key not in node:
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
    old = node.get( key, None )
    node[ key ] = value
    return old

##============================================================================

##
# returns true if the given path has a set value in the given hmap
def hmap_has_path( hmap, path ):
    node, key = hmap_probe( hmap_probe, path )
    return node is not None and key in node


##============================================================================
##============================================================================

##
# Given an hmap that *may* have structured keys as keys,
# returns a new hmap which has the structured keys resolves into
# an actual structure in the hmap (so not more keys are strucutred-keys)
#
# The resulting hmap *may* share structure with the input hmap
def resolve_structured_keys( hmap, delim='/' ):

    # ok, create a new dict as the base
    base = {}

    # now, let's check each key of the given hmap
    # and resolve if it is a strucutred key, otherwise
    # use the value of the input hjmap
    for key, value in hmap.items():

        # recurse to value irregardless of key if it is an hmap node
        if isinstance( value, dict ):
            value = resolve_structured_keys( value, delim=delim )

        # nothing to resolve for this key, jsut use hte value
        if not is_structured_key( key ):
            base[ key ] = value
        else:

            # resolve the key
            path = ensure_path( key )
            temp_map = base
            for p in path[:-1]:
                temp_map[ p ] = {}
                temp_map = temp_map[p]

            # ok, last part of path gets the value
            temp_map[path[-1]] = value

    # return the resolved map
    return base

##============================================================================
##============================================================================
##============================================================================

##
# Returns true iff the given object does not have any free variables
# (which are template {{ }} handlebar slots) in it
def has_free_variables( x ):
    if isinstance( x, (list,tuple) ):
        return not any( has_free_variables, x )
    if isinstance( x, dict ):
        return not any( has_free_variables, x.items() )
    s = str(x)
    return TEMPLATE_HANDLEBAR_START not in s and TEMPLATE_HANDLEBAR_END not in s

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

##
# Resolves the free variables within the hmap.
# This does a global resolve on all the free variables since
# the templates are treated globally
#
# Returns a new parse state with given parse state as parent
def resolve_free_variables( parse_state, template_context ):

    # first, translate any variable blocks into jinja set statements
    # for use within the hmap
    hmap_with_jinja_vars = add_jinja_variable_nodes( parse_state.hmap, template_context )

    # write out the resulting hmap's YAML
    with tempfile.NamedTemporaryFile( mode='w', prefix='shunt-pre-resolve_') as f:
        f.write( yaml.dump( hmap_with_jinja_vars ) )
        f.flush()
        logger.info( "dumping pre-resolve into '{0}'".format( f.name ) )

        # ok, load in the jinja template
        template, render_context = template_context.load_intermediate_template( f.name )

        # now render the template
        template_string = template.render(render_context)
        opened_file = None
        with open( f.name + ".rendered", 'w' ) as wf:
            opened_file = f.name + ".rendered"
            wf.write( template_string )
            
        
        # ok, repase the resulting yaml
        try:
            new_parse_state = parse_yaml( opened_file, parent=parse_state )
        except Exception as e:
            msg = "Unable to re-load rendered template as YAML. Rendering at '{0}'".format( opened_file )
            raise RuntimeError( msg ) from e

        # ok, remove rendered temporary file
        os.remove( opened_file )

        # return the resulting parse
        return new_parse_state

##============================================================================
##============================================================================
##============================================================================

##
# Given a ParseState, returns a new hmap with any 'var' nodes
# having and additional '_' key with jinja template code to
# actually set the variables for jinja templates
def add_jinja_variable_nodes( hmap, template_context ):

    # deal with non-dictionaries
    if not isinstance( hmap, dict ):

        # lists and tuples and just recursed over each element :)
        if isinstance( hmap, (list,tuple) ):
            return type(hmap)( map( lambda x: add_jinja_variable_nodes(x,template_context), hmap ) )

        # everything else is an atom and cannot have vars 
        return hmap

    # new structure to return
    new_hmap = copy.copy( hmap )

    # ok, grab any immediate variables
    if 'vars' in hmap:

        # create jinaj set equivalents
        accum = hmap['vars']
        jinja_sets = []
        for (key,value) in accum.items():
            jinja_sets.append(
                "{{%- set {name} = \"{value}\" -%}}".format(
                    name = discard_handlebars( key ),
                    value = discard_handlebars( value ) ) )

        # assign jinja sets to special key
        new_hmap[ JINJA_VARIABLE_KEY ] = "\n".join( jinja_sets )

    # recurse to children
    for (key, value) in hmap.items():
        if key == 'vars':
            continue
        new_hmap[ key ] = add_jinja_variable_nodes( value, template_context )

    # return new structure
    return new_hmap
        

##============================================================================

##
# Given a string, discards any enclosing handlebars (first order)
def discard_handlebars( x ):
    if not isinstance( x, str ):
        return x

    find_start_idx = x.find( TEMPLATE_HANDLEBAR_START )
    res = x
    if find_start_idx >= 0:
        res = res[0:find_start_idx] + res[find_start_idx+len(TEMPLATE_HANDLEBAR_START):]
    find_end_idx = res.rfind( TEMPLATE_HANDLEBAR_END )
    if find_end_idx >= 0:
        res = res[0:find_end_idx] + res[find_end_idx+len(TEMPLATE_HANDLEBAR_END):]
    return res

##============================================================================
##============================================================================
##============================================================================

##
# A template context allows us to load "intermediate" templates.
# This also includes the jinja Environment and loaders being used
class TemplateContext( object ):

    ##
    #
    def __init__( self,
                  environment = None,
                  context = None):
        if environment is None:
            self.environment = jinja2.Environment(
                loader = jinja2.FileSystemLoader([
                    "templates",
                    ".",
                ] )
            )
        else:
            self.environment = environment
        if context is None:
            self.context = {}
        else:
            self.context = context

    ##
    #
    def load_intermediate_template( self, template_filename ):
        with open( template_filename ) as f:
            template = self.environment.from_string( f.read() )
        context = self.context
        return template, context



DEFAULT_TEMPLATE_CONTEXT = TemplateContext()

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
##============================================================================
##============================================================================
