# -*- coding: utf-8 -*-
#    See the file LICENSE.txt for your rights.
#    Author: Michael Kainzbauer (github: mkainzbauer)

"""read data from pvprivate device and store it as as selected value in weewx archive data

*******************************************************************************

To use this extension, add the following somewhere in your configuration file
weewx.conf:

[pvprivate]
    api_url = http://IP_ADRESS.OF_YOUR.DEVICE.HERE:PORT/api/getSumProduced/
    installedWP = 3000 # installed Watts peak
    archive_column = signal1 #optional, "radiation" is default
    

*******************************************************************************

To enable this service:

1) copy this file to the user directory

2) modify the weewx configuration file by adding this service to the option
"report_services", located in section [Engine][[Services]].

[Engine]
  [[Services]]
    ...
    data_services = user.pvprivate.AddPVPower # other services can be appended separated with a comma

*******************************************************************************
"""

import weewx, json, urllib.request, urllib.error, weeutil.weeutil, logging
from weeutil.weeutil import timestamp_to_string
from weewx.engine import StdService
from datetime import datetime

log = logging.getLogger(__name__)

class AddPVPower(StdService):

  def __init__(self, engine, config_dict):

    # Initialize my superclass first:
    super(AddPVPower, self).__init__(engine, config_dict)

    # Bind to any new archive record events:
    self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)

  def new_archive_record(self, event):
    value = self.getValue(event)
    log.debug("pvprivate power value: %s at %s" % (value, (weeutil.weeutil.timestamp_to_string(event.record['dateTime']))))

    archive_column = "radiation"
    if 'archive_column' in self.config_dict['pvprivate']:
      archive_column = self.config_dict['pvprivate']['archive_column']

    event.record[archive_column] = value

  def getValue(self, event):
    try:
      installedWP = float(self.config_dict['pvprivate']['installedWP'])
      log.debug("Installed Watt peak: %s"  % installedWP)
      url = self.config_dict['pvprivate']['api_url'] + str(event.record['dateTime'])
      if 'deviceId' in self.config_dict['pvprivate']:
        url = url + '/' + self.config_dict['pvprivate']['deviceId']
      log.info(url)
      response = urllib.request.urlopen(url)
      raw = response.read()
      log.debug("RAW: %s"  % raw)
      if len(raw) < 1:
        url = self.config_dict['pvprivate']['api_url'] + str(event.record['dateTime'] - int(self.config_dict['StdArchive']['archive_interval']))
        log.info(url)
        response = urllib.request.urlopen(url)
        raw = response.read()
        log.debug("RAW: %s"  % raw)
      data = json.loads(raw)
      averagePower = data["produced"]
      log.info("Avg Power: %s at %s" % (averagePower, (weeutil.weeutil.timestamp_to_string(event.record['dateTime']))))
      normalizedOutput = averagePower / installedWP
      log.debug("Normalized Output: %s at %s" % (normalizedOutput, (weeutil.weeutil.timestamp_to_string(event.record['dateTime']))))

      return normalizedOutput
    except urllib.error.URLError as e:
      log.error("Error getting inverter data: %r" % e)
    except:
      log.error("Unexpected error:")
      return None
