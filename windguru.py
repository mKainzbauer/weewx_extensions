# -*- coding: utf-8 -*-
import weewx, urllib2, syslog, time
from weewx.engine import StdService

class UploadWindguru(StdService):
    
    inHgmBarFactor = 33.8638
    mphKnotFactor = 0.868976558176657
    inmmFactor = 25.4
    cmmmFactor = 10
    kmhKnotFactor = 0.539957
    mpsKnotFactor = 1.94384
      
    def __init__(self, engine, config_dict):

      # Initialize my superclass first:
      super(UploadWindguru, self).__init__(engine, config_dict)

      # Bind to any new archive record events:
      self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)

    def new_archive_record(self, event):
      try:
        wind_avg = float(event.record['windSpeed'])
        wind_max = float(event.record['windGust'])
        wind_direction = event.record['windDir']
        temperature = float(event.record['outTemp'])
        rh = event.record['outHumidity']
        mslp = float(event.record['pressure'])
        if self.config_dict['Windguru']['barometer'] in event.record:
          mslp = float(event.record[self.config_dict['Windguru']['barometer']])
        precip = float(event.record['rain'])
        
        syslog.syslog(syslog.LOG_DEBUG, "event.record: %s" % event.record)
        #Windguru only takes current values, so only values from close to now are taken (in case of backfilling values)
        if (time.time() - int(event.record['dateTime'])) < int(self.config_dict['StdArchive']['archive_interval']):
          if int(event.record['usUnits']) == weewx.US:
            wind_avg = wind_avg * UploadWindguru.mphKnotFactor
            wind_max = wind_max * UploadWindguru.mphKnotFactor
            precip = precip * UploadWindguru.inmmFactor
            temperature = (temperature - 32) * 5 / float(9)
            mslp = mslp * UploadWindguru.inHgmBarFactor
          elif int(event.record['usUnits']) == weewx.METRIC:
            wind_avg = wind_avg * UploadWindguru.kmhKnotFactor
            wind_max = wind_max * UploadWindguru.kmhKnotFactor
            precip = precip * UploadWindguru.cmmmFactor
          elif int(event.record['usUnits']) == weewx.METRICWX:
            wind_avg = wind_avg * UploadWindguru.mpsKnotFactor
            wind_max = wind_max * UploadWindguru.mpsKnotFactor
          request = self.config_dict['Windguru']['url'] + '?uid=' + self.config_dict['Windguru']['uid'] + '&wind_avg=' + str(wind_avg) + '&wind_max=' + str(wind_max) + '&wind_direction=' + str(wind_direction) + '&temperature=' + str(temperature) + '&rh=' + str(rh) + '&mslp=' + str(mslp) + '&precip=' + str(precip)
          syslog.syslog(syslog.LOG_INFO, "Uploading Windguru data: %s" % request)
          try:
            result = urllib2.urlopen(request, timeout = 1)
            httpStatusCode = result.getcode()
            if int(httpStatusCode) != 200:
              syslog.syslog(syslog.LOG_ERR, "Failed to upload data: Winguru answer: %s"  % httpStatusCode)
            else:
              syslog.syslog(syslog.LOG_DEBUG, "Winguru answer: %s"  % httpStatusCode)
          except urllib2.URLError, e:
            syslog.syslog(syslog.LOG_ERR, "Error uploading data: %r" % e)
          except:
            syslog.syslog(syslog.LOG_ERR, "Unexpected error:")
      except:
        syslog.syslog(syslog.LOG_ERR, "Unexpected error:")
      