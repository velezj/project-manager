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
                  name="",
                  description=None,
                  parent_spec=None,
                  error_on_duplicates = True,
                  allow_extra_options=False,
                  **common_attributes ):
        self.name = name
        self.error_on_duplicates = error_on_duplicates
        self.description = description
        self.allow_extra_options = allow_extra_options
        self.options = {}
        self.subspecs = {}
        self.parent_spec = parent_spec
        for opt in options:
            self.add( *opt, **common_attributes )

    ##
    # Add an option to this specification
    def add_option( self, *args, **attributes ):
        opt = ConfigurationOption( *args, spec=self, **attributes )
        if self.error_on_duplicates and opt.name in self.options:
            raise ValueError( "Configuration option '{0}' already added in this specifications as '{1}'".format( opt.name, self.options[ opt.name ] ) )
        self.options[ opt.name ] = opt
        return self

    ##
    # Add a sub-configuration specification to this specification
    def add_specification( self, spec, **attributes ):

        # merge in the given attributes to the spec
        spec.update_attributes( attributes )

        # check if duplicate and error if wanted
        if self.error_on_duplicates and spec.name in self.specs:
            raise InvalidArgument( "Configuration sub-specification '{0}' already added in this specification as '{1}'".format( spec.name, self.specs[spec.name] ) )

        # add teh spec and return
        self.specs[ spec.name ] = spec
        spec.parent_spec = self
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


    ##
    # Returns the path of this specification from the given
    # specification.
    # If this specification is not a sub-specification of given
    # returns None, else returns the ordered list of the
    # path from hte given specification down to this specification.
    # The list incldues the actual ConfigurationSpecification objects
    def path_from_specification( self, spec ):
        if spec is None:
            return None
        if self is spec:
            return []
        if self.parent_spec is None:
            return None
        parent_path = self.parent_path.path_from_specification( spec )
        if parent_path is None:
            return None
        return parent_path + [self]

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

    TYPES = {
        'string' : unicode,
        'int' : int,
        'float' : float,
        'list' : list,
        'tuple' : tuple,
        'dict' : dict,
    }

    DEFAULT_TYPE_CLASS = TYPES[ 'string' ]

    ##
    # Creates a new configuration option with the
    # given name and attributes
    def __init__( self, name, spec, **attributes ):
        self.name = name
        self.spec = spec
        self.attributes = attributes
        self.required = None
        self.description = None
        self.aggregate_type = None
        self.aggregate_function = None
        self.initial_value = None
        self.type_type = None
        self.type_class = None
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
        self.initial_value = self.attributes.get( 'initial_value', None )
        self.type_type = self.attributes.get( 'type', 'string' )
        self.type_class = TYPES.get( self.type_type, DEFAULT_TYPE_CLASS )

    ##
    # Returns the path from this option to the given specification
    def path_from_specification( self, spec ):
        spec_path = self.spec.path_from_specification( spec )
        if spec_path is None:
            return None
        return spec_path + [ self.name ]

##=========================================================================
##=========================================================================

##
# A Configuration object is a fillable container of configuration.
# It must have a single Configuration Specification which determines
# what is expected in the configuration.
#
# The configuration is filled in by different methods from different
# sources using it's specification to validate
class Configuration( object ):


    ##
    # Initialzie a configuration with a specification
    def __init__( self, specification ):
        self.specification = specification
        self.data = {}
        self._populate_data_levels()

    ##
    # Fill the given specification option with the given value
    def fill_option( self, option, value ):

        # grab any previous value aggragated for hte option
        acum = self.get_option( option,
                                option.initial_value )

        # ok, aggragate the new value
        option_value = option.type_class( value )
        agg = option.aggregate_function( option_value, acum )

        # set the option value
        self._set_option_value( option, agg )

    ##
    # Returns hte option value if set.
    # If not set returns the given default argument.
    # If option is not a part of this specification this is
    # an error and an exception is raised
    def get_option( self, option, default ):
        path = option.path_from_specification( self.specification )
        if path is None or len(path) < 1:
            raise ValueError( "Tried to fetch option value for an option which is not part of a Configuration's Specification. option.name={option.name}".format( option = option ) )
        hmap_get( self.data, map(lambda p: p.name, path), default )

    ##
    # Set the value for an option.
    # This is an internal method.
    #
    # The path to set is computed from the specification and
    # the option, and the value is stored there
    def _set_option_value( self, option, value ):
        path = option.path_from_specification( self.specification )
        if path is None or len(path) < 1:
            raise ValueError( "Tried to internally set option value for an option which is not part of a Configuration's Specification. option.name={option.name}".format( option = option ) )
        hmap_set( self.data, map(lambda p: p.name, path), value )


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
