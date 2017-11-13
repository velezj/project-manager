import logging
logger = logging.getLogger( __name__ )

import sys

##=========================================================================

##
# A configuration specification.
# This object defines the expected configuration options as well as
# metadata about the options including documentation, required/optional,
# etc.
#
# A configuration specification is needed before a configuration
# object can be populated with data from various sources
# such as yaml files, the command line, etc.
class ConfigurationSpecification( object ):

    ##
    # Initialize a specification with the given
    # sub-configuration specifications.
    # The given arguments will all be treated as
    # arguments into self.add_option( **arg[i] )
    def __init__( self,
                  *options,
                  root="",
                  description=None,
                  error_on_duplicates = True,
                  allow_extra_options=False,
                  **common_attributes ):
        self.root = root
        self.error_on_duplicates = error_on_duplicates
        self.description = description
        self.allow_extra_options = allow_extra_options
        self.options = {}
        self.subspecs = {}
        for opt in options:
            self.add( *opt, **common_attributes )

    ##
    # Add an option to this specification
    def add_option( self, *args, **attributes ):
        opt = ConfigurationOption( *args, **attributes )
        if self.error_on_duplicates and opt.name in self.options:
            raise InvalidArgument( "Configuration option '{0}' already added in this specifications as '{1}'".format( opt.name, self.options[ opt.name ] ) )
        self.options[ opt.name ] = opt
        return self

    ##
    # Add a sub-configuration specification to this specification
    def add_specification( self, spec, **attributes ):

        # merge in the given attributes to the spec
        spec.update_attributes( attributes )

        # check if duplicate and error if wanted
        if self.error_on_duplicates and spec.root in self.specs:
            raise InvalidArgument( "Configuration sub-specification '{0}' already added in this specification as '{1}'".format( spec.root, self.specs[spec.root] ) )

        # add teh spec and return
        self.specs[ spec.root ] = spec
        return self

    ##
    # Recursively update all of the attributed of all sub-specifications
    # and options.
    def update_attributes( self, attributes, _seen=None ):
        if _seen is None:
            _seen = set([])

        # exit out of looping sub-specifications path
        if self in _seen:
            return self

        # set self as seen
        _seen.add( self )

        # update all specifications
        for spec in self.specs:
            spec.update_attributes( attributes, _seen=_seen )

        # update all options
        for opt in self.options:
            opt.update_attributes( attributes )

        # return self
        return self

##=========================================================================

##
# A configuration option specifies the name and attributes of a particular
# configurable thing in a specification.
# All options have at least a name.
# Options also have a cardinality as well as wehtehr they are required
# or optional.
# Furthermore options can be tagged as advanced (for advanced tuning)
# or normal for day-to-day operation.
class ConfigurationOption( object ):

    AGGREGATE_FUNCTIONS = {
        'last_wins' : lambda new, accum: new,
        'list' : lambda new, accum: accum + [new] if accum is not None else [new],
        'set' : lambda new, accum: set(list(accum) + [new]) if accum is not None else set([new]),
        'first_wins' : lambda new, accum: accum if accum is not None else new,
    }

    DEFAULT_AGGREGATE = AGGREGATE_FUNCTIONS[ 'last_wins' ]

    ##
    # Creates a new configuration option with the
    # given name and attributes
    def __init__( self, name, **attributes ):
        self.name = name
        self.attributes = attributes
        self.required = None
        self.description = None
        self.aggregate_type = None
        self.aggregate_function = None
        self.update_attributes( attributes )

    ##
    # update hte attributes of this option
    def update_attributes( self, attributes ):
        self.attributes.update( attributes )
        self._lift_special_attributes()
        return self

    ##
    # Lift special attributes to self
    def _lift_special_attributes( self ):
        self.required = self.attributes.get( 'required', False )
        self.description = self.attributes.get( 'description' )
        self.aggregate_type = self.attributes.get('aggregate_type', 'last_wins')
        self.aggregate_function = AGGREGATE_FUNCTIONS.get(
            self.aggregate_type,
            DEFAULT_AGGREGATE )
        
        

##=========================================================================
##=========================================================================

##
# A Configuration object is a fillable container of configuration.
# It must have a single Configuration Specification which determines
# what is expected in the configuration.
#
# The configuration is filled in by different methods from different
# sources using it's specification to validate
class Configuration

##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
