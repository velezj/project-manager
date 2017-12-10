import logging
logger = logging.getLogger( __name__ )

from hmap import hmap_get, hmap_set, hmap_paths
import from variables import has_free_variables

DIRECTIVE_PREFIX = '@'

##============================================================================

##
# A mapping of known directives and their parsing functions
KNOWN_DIRECTIVES = {}

##============================================================================

##
# Register a new directive and parsing function
def register_directive( name, parser, override=False ):
    if name in KNOWN_DIRECTIVES:
        if not override:
            msg = "Directive '{0}' already registered as a known directive! Set override=True if you want to force set the directive".format( name )
            raise RuntimeError( msg )
        logger.info( "Overriding already registered directive '{0}'".format( name ) )
    KNOWN_DIRECTIVES[ name ] = parser

##============================================================================

##
# Fill the given dicitonary with all the known directives
def fill_known_directive_parsers( target_map, override=False ):
    for name, parser in KNOWN_DIRECTIVES.items():
        if name in target_map:
            if not override:
                msg = "Directive '{0}' already in target map, can not fill because of name clash. Set override=True to force fill the target map".format( name )
                raise RuntimeError( msg )
            logger.info( "Overriding directive '{0}' whiling filling known directive parser".format( name ) )
        target_map[ name ] = parser
        

##============================================================================

##
# Returns true iff the given object denotes a directive
def is_directive( x ):
    return isinstance( x, str ) and x.startswith( DIRECTIVE_PREFIX )

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

##
# Parse a directive
def parse_directive( path, value, parse_state ):

    # ok, parse by grabbing single directive token
    # and looking up parser in parse_state
    tokens = value.split(' ',1)
    directive = tokens[0][1:].lower()

    parser = parse_state.get_directive_parser( directive )
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

##
# Base directive object.
# Each directive has a name and parser along with an object that is
# a callable on Directive( parser.ParseState ) and return the new ParseState.
#
# The directive *may* change hte given parse_state
class Directive( object ):

    ##
    # Subclasses should override this method for performing the
    # action represented by hte directive
    def __call__( self, parse_state ):
        raise NotImplementedError()

##============================================================================

##
# Includes a given file at the path of hte directive.
class IncludeDirective( Directive ):

    ##
    # Creates a new include directive for given path and given inut filename
    def __init__( self, parse_state, path, filename ):
        self.filename = filename
        self.path = path

    ##
    # Includes the file where the directive was
    def __call__( self, parse_state ):
        logger.info( "Including file '{0}' into path '{1}'".format(
            self.filename,
            self.path ) )
        with open( self.filename ) as f:
            hmap_set(
                parse_state.hmap,
                self.path,
                f.read() )
        return parse_state

##============================================================================
##============================================================================
##============================================================================
