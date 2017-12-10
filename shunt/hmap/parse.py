import logging
logger = logging.getLogger( __name__ )

from hmap import hmap_get, hmap_set
import directives

import yaml

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
    DEFAULT_DIRECTIVE_PARSER = directives._default_directive_parser

    ##
    # Create a new parse state
    def __init__( self,
                  hmap,
                  line_info = None,
                  parent = None,
                  directive_parsers = None):
        self.hmap = hmap
        self.line_info = line_info
        self.parent = parent
        self.directive_parsers = directive_parsers
        if self.directive_parsers is None:
            self.directive_parsers = {}
            directives.fill_known_directive_parsers( self.directive_parsers )

    ##
    # returns hte line information for a path if any or None
    def get_line_info_for_path( self, path ):
        if self.line_info is None:
            return None
        return hmap_get( self.line_info, path, None )
        

    ##
    # returns the parser for a directive
    def get_directive_parser( self, directive, default = None ):
        parser = self.directive_parsers.get( directive, default )
        if default is None and parser is None:
            return self.DEFAULT_DIRECTIVE_PARSER


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
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
