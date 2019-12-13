# -*- coding: utf-8 -*-
#    See the file LICENSE.txt for your rights.
#    Author: Michael Kainzbauer (github: mkainzbauer)

"""How to read data from your Fronius device and store it as radiation in weewx archive data

*******************************************************************************

To use this extension, add the following somewhere in your configuration file
weewx.conf:

[Fronius]
    api_url = http://IP_ADRESS.OF_YOUR.DEVICE.HERE/solar_api/v1/GetArchiveData.cgi?
    timeZone = Z # use the timeZone of your device 
    installedWP = 3000 # installed Watts peak
    

*******************************************************************************

To enable this service:

1) copy this file to the user directory

2) modify the weewx configuration file by adding this service to the option
"report_services", located in section [Engine][[Services]].

[Engine]
  [[Services]]
    ...
    data_services = user.fronius.AddRadiation # other services can be appended separated with a comma

*******************************************************************************
"""

import weewx, json, urllib2, syslog, weeutil.weeutil
from weeutil.weeutil import timestamp_to_string
from weewx.engine import StdService
from datetime import datetime

class AddRadiation(StdService):
      
    def __init__(self, engine, config_dict):

      # Initialize my superclass first:
      super(AddRadiation, self).__init__(engine, config_dict)

      # Bind to any new archive record events:
      self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)

    def new_archive_record(self, event):
      radiation = self.getRadiation(event)
      syslog.syslog(syslog.LOG_DEBUG, "Radiation: %s at %s" % (radiation, (weeutil.weeutil.timestamp_to_string(event.record['dateTime']))))
      event.record['radiation'] = radiation

    def getRadiation(self, event):
      timeZone = "Z"
      if 'timeZone' in self.config_dict['Fronius']:
        timeZone = self.config_dict['Fronius']['timeZone']
        syslog.syslog(syslog.LOG_DEBUG, "Fronius timeZone: %s"  % timeZone)
      installedWP = float(self.config_dict['Fronius']['installedWP'])
      syslog.syslog(syslog.LOG_DEBUG, "Installed Watt peak: %s"  % installedWP)
      startDateTime = int(event.record['dateTime'])
      endDateTime = startDateTime + int(self.config_dict['StdArchive']['archive_interval'])
      endDate = datetime.utcfromtimestamp(endDateTime).isoformat() + timeZone
      startDate = datetime.utcfromtimestamp(startDateTime).isoformat() + timeZone
      url = self.config_dict['Fronius']['api_url'] + 'Scope=System&StartDate=' + startDate + '&EndDate=' + endDate + '&Channel=EnergyReal_WAC_Sum_Produced&Channel=TimeSpanInSec'
      syslog.syslog(syslog.LOG_INFO, url)
      try:
        response = urllib2.urlopen(url)
        data = json.loads(response.read())
        work = data["Body"]["Data"]["inverter/1"]["Data"]["EnergyReal_WAC_Sum_Produced"]["Values"]["0"]
        timeSpan = data["Body"]["Data"]["inverter/1"]["Data"]["TimeSpanInSec"]["Values"]["0"]
        averagePower = work / (timeSpan / float(3600))
        syslog.syslog(syslog.LOG_INFO, "Avg Power: %s at %s" % (averagePower, (weeutil.weeutil.timestamp_to_string(event.record['dateTime']))))
        normalizedOutput = averagePower / installedWP
        syslog.syslog(syslog.LOG_DEBUG, "Normalized Output: %s at %s" % (normalizedOutput, (weeutil.weeutil.timestamp_to_string(event.record['dateTime']))))
        return normalizedOutput
      except urllib2.URLError, e:
        syslog.syslog(syslog.LOG_ERR, "Error getting inverter data: %r" % e)
      except:
        syslog.syslog(syslog.LOG_ERR, "Unexpected error:")
