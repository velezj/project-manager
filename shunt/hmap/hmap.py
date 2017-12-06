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

DIRECTIVE_PREFIX = '@'
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
# Returns true iff the given object denotes a directive
def is_directive( x ):
    return isinstance( x, str ) and x.startswith( DIRECTIVE_PREFIX )

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

##
# Parses out the directives in an hmap which themselves do not have
# any free variables
def extract_directives_without_free_variables( parse_state ):

    # ok, we will go over all the possible values of
    # the hmap and parse any directives
    directives = []
    for path, value in hmap_paths( parse_state.hmap ):
        if is_directive( value ) and not has_free_variables( value ):
            directives.append( parse_directive( path, value, parse_state ) )

    return directives

##============================================================================
##============================================================================

##
# Parse a directive
def parse_directive( path, value, parse_state ):

    # ok, parse by grabbing single directive token
    # and looking up parser in parse_state
    tokens = value.split(' ',1)
    directive = tokens[0][1:].lower()

    parser = parse_state.get_directive_parser( directive, parser_state.DEFAULT_DIRECTIVE_PARSER )
    if parser is None:
        msg = "Cannot parse directive '{0}' at path '{1}' with value '{2}'"
        msg.format( directive, path, value )
        line_info = parse_state.get_line_info_for_path( path )
        msg += " " + line_info_message( line_info )
        logger.error( msg )
        raise RuntimeError( msg )

    # ok, just parse the directive value and return the parsed
    return parser( directive, parse_state, path, tokens[1] )
    

##============================================================================
##============================================================================
##============================================================================
##============================================================================

##
# The default directive parser only knowns of one directive: include
def _default_directive_parser( directive, parse_state, path, argument ):
    if directive != 'include':
        msg = "Unknown directive '{0}' at path '{1}' value '{2}'".format(
            directive,
            path,
            value )
        line_info = parse_state.get_line_info_for_path( path )
        msg += " " + line_info_message( line_info )
        logger.error( msg )
        raise RuntimeError( msg )

    # make sure our argument has no free variables
    if has_free_variables( argument ):
        msg = "Unable to parse 'include' directive with free variables in argument: '{0}'".format( argument ) + line_info_message( parse_state.get_line_info_for_path( path ) )
        logger.error( msg )
        raise RuntimeError( msg )

    # ok, make sure that argumetn is a single path argument
    try:
        include_path = check_and_parse_single_path( argument, parse_state, path )
    except Exception as e:
        msg = "Unable to parse 'include' directive path argument '{0}'".format(
            argument ) + line_info_message( parse_state.get_line_info_for_path( path ) )
        logger.error( msg )
        raise RuntimeError( msg ) from e

    # ok, create the directive
    return IncludeDirective(
        parse_state,
        path,
        include_path )

##============================================================================

##============================================================================
##============================================================================

##
# The parser state is a class that accumulates states for the
# directive parsers (and other parsers maybe)
#
# This includes the hmap as well as line_information and
# any directive parsers eing used
class ParseState( object ):

    ##
    # The default directive parser
    DEFAULT_DIRECTIVE_PARSER = _default_directive_parser

    ##
    # Create a new parse state
    def __init__( self,
                  hmap,
                  line_info = None,
                  parent = None):
        self.hmap = hmap
        self.line_info = line_info
        self.parent = parent

    ##
    # returns hte line information for a path if any or None
    def get_line_info_for_path( self, path ):
        if self.line_info is None:
            return None
        return hmap_get( self.line_info, path, None )
        

    ##
    # returns the parser for a directive
    def get_directive_parser( self, directive, default ):
        return default

##============================================================================

##
# A line information class which contains the line number, column,
# and raw index ranges for a particular section of an hmap
class LineInformation( object ):
    def __init__( self,
                  start_line,
                  stop_line,
                  start_char,
                  stop_char,
                  start_byte,
                  stop_byte ):
        self.start_line = start_line
        self.stop_line = stop_line
        self.start_char = start_char
        self.stop_char = stop_char
        self.start_byte = start_byte
        self.stop_byte = stop_byte

##============================================================================

##
# Returns a human readable message for hte line information given.
# If given a None will return "<no_line_info>" so is safe to
# call with None values
def line_info_message( line_info ):
    if line_info is None:
        return "<no_line_info>"
    s = "At "
    if line_info.start_line is not None:
        s += "lines {0}-{1} ".format(
            line_info.start_line,
            line_info.stop_line )
    if line_info.start_char is not None:
        s += "characters {0}-{1} ".format(
            line_info.start_char,
            line_info.stop_char )
    if line_info.start_byte is not None:
        s += "bytes {0}-{1}".format(
            line_info.start_byte,
            line_info.stop_byte )
    if line_info.start_line is None and line_info.start_char is None and line_info.start_byte is None:
        s += "<empty_line_info>"
    return s

##============================================================================
##============================================================================
##============================================================================

##
# Make sure given string has a single path arugment in it and
# return it
def check_and_parse_single_path( x, parse_state, path ):
    if not isinstance( x, str ):
        msg = "Excepted string, got {0}".format( type(x) )
        logger.error( msg )
        raise RuntimeError( msg )

    return x

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
    with tempfile.NamedTemporaryFile( mode='w', prefix='shunt-pre-resolve_', delete=False ) as f:
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

def parse_yaml( filename, parent=None ):
    with open(filename) as f:
        return ParseState(
            yaml.load(f),
            parent = parent )

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
