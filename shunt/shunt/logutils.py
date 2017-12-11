import logging
logger = logging.getLogger( __name__ )

import traceback

##============================================================================

class CustomAdapter(logging.LoggerAdapter):
    @staticmethod
    def indent():
        indentation_level = len(traceback.extract_stack())
        return indentation_level-4  # Remove logging infrastructure frames

    def process(self, msg, kwargs):
        return '{i}{m}'.format(i='..'*self.indent(), m=msg), kwargs


##============================================================================

def getLogger( name ):
    return CustomAdapter( logging.getLogger( name ), {} )

##============================================================================
##============================================================================
##============================================================================
##============================================================================
##============================================================================
