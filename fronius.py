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
      syslog.syslog(syslog.LOG_INFO, "Radiation: %s at %s" % (radiation, (weeutil.weeutil.timestamp_to_string(event.record['dateTime']))))
      event.record['radiation'] = radiation

    def getRadiation(self, event):
      timeZone = "Z"
      if 'timeZone' in self.config_dict['Fronius']:
        timeZone = self.config_dict['Fronius']['timeZone']
        syslog.syslog(syslog.LOG_INFO, "Fronius timeZone: %s"  % timeZone)
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
        return round(averagePower)
      except urllib2.URLError, e:
        syslog.syslog(syslog.LOG_ERR, "Error getting inverter data: %r" % e)
      except:
        syslog.syslog(syslog.LOG_ERR, "Unexpected error:")