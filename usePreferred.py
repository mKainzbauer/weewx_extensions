# -*- coding: utf-8 -*-
#    See the file LICENSE.txt for your rights.
#    Author: Michael Kainzbauer (github: mkainzbauer)

"""Prefers a reading over another, if reading is present

*******************************************************************************

To use this extension, add the following somewhere in your configuration file
weewx.conf:

[UsePreferred]
    value1 = preferredValue1
    value2 = preferredValue2
    ...

*******************************************************************************

To enable this service:

1) copy this file to the user directory

2) modify the weewx configuration file by adding this service to the option
"report_services", located in section [Engine][[Services]].

[Engine]
  [[Services]]
    ...
    data_services = user.usePreferred.UsePreferred # other services can be appended separated with a comma

*******************************************************************************
"""

import weewx, logging
from weewx.engine import StdService

log = logging.getLogger(__name__)

class UsePreferred(StdService):
      
    def __init__(self, engine, config_dict):

      # Initialize my superclass first:
      super(UsePreferred, self).__init__(engine, config_dict)

      # Bind to any new archive record events:
      self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)

    def new_archive_record(self, event):
      for key in self.config_dict['UsePreferred']:
        otherKey = self.config_dict['UsePreferred'][key]
        if key in event.record:
          log.debug("%s: %s"  % (key,event.record[key]))
          if otherKey in event.record:
            log.debug("Replacing %s(%s) with %s(%s)"  % (key, event.record[key], otherKey, event.record[otherKey]))
            event.record[key] = event.record[otherKey]
          