from datetime import datetime

from dateutil.rrule import rrule, DAILY, MONTHLY, YEARLY, WEEKLY, MO, TU, WE, TH, FR, SA, SU, weekday
from django.test import TestCase
from .timeCodeParser import parseDateRange, parseTimeRange, parseFreq, parseBy
from .timeCodeParserTypes import (EventType, DateRangeObject, TimeRangeObject, TimeUnit, TimeRange, FreqObject, ByObject,
                                  TimeCodeLex, TimeCodeSem, TimeCodeParseResult, TimeCodeDao, DateUnit)


# Create your tests here.
class ParseDateTest(TestCase):
    def test_parseDate(self):
        self.assertEqual(parseDateRange('2021/10/1'), DateRangeObject(dtstart=DateUnit(2021, 10, 1)))

    def test_parseDateSugar(self):
        self.assertEqual(parseDateRange('2021/10/1-11/1'), DateRangeObject(dtstart=DateUnit(2021, 10, 1), until=DateUnit(2021, 11, 1)))
        year = datetime.now().year
        if datetime.now().month >= 10 and datetime.now().day >= 1:
            year += 1
        self.assertEqual(parseDateRange('10/1-25'), DateRangeObject(dtstart=DateUnit(year, 10, 1), until=DateUnit(year, 10, 25)))
        self.assertEqual(parseDateRange('10/1'), DateRangeObject(dtstart=DateUnit(year, 10, 1)))


class ParseTimeTest(TestCase):
    def test_parseTime(self):
        self.assertEqual(parseTimeRange('20:30'), TimeRangeObject(end=TimeUnit(20, 30), startMark='11', endMark='11'))

    def test_parseTimeRange(self):
        self.assertEqual(parseTimeRange('20:30-21:30'), TimeRangeObject(start=TimeUnit(20, 30), end=TimeUnit(21, 30), startMark='11', endMark='11'))

    def test_parseTimeRangeStartUnknown(self):
        self.assertEqual(parseTimeRange('?:?-21:30'), TimeRangeObject(start=TimeUnit(0, 0), end=TimeUnit(21, 30), startMark='00', endMark='11'))

    def test_parseTimeRangeStartHourUnknown(self):
        self.assertRaises(ValueError, parseTimeRange, '?:30-21:30')

    def test_parseTimeRangeStartMinUnknown(self):
        self.assertEqual(parseTimeRange('20:?-21:00'), TimeRangeObject(start=TimeUnit(20, 0), end=TimeUnit(21, 0), startMark='10', endMark='11'))

    def test_parseTimeRangeEndUnknown(self):
        self.assertEqual(parseTimeRange('20:30-?:?'), TimeRangeObject(start=TimeUnit(20, 30), end=TimeUnit(0, 0), startMark='11', endMark='00'))

    def test_parseTimeRangeEndHourUnknown(self):
        self.assertRaises(ValueError, parseTimeRange, '20:30-?:30')

    def test_parseTimeRangeEndMinUnknown(self):
        self.assertEqual(parseTimeRange('20:30-21:?'), TimeRangeObject(start=TimeUnit(20, 30), end=TimeUnit(21, 0), startMark='11', endMark='10'))

    def test_parseTimeRangeStartEndHourUnknown(self):
        self.assertRaises(ValueError, parseTimeRange, '?:30-?:30')

    def test_parseTimeRangeStartEndMinUnknown(self):
        self.assertEqual(parseTimeRange('20:?-21:?'), TimeRangeObject(start=TimeUnit(20, 0), end=TimeUnit(21, 0), startMark='10', endMark='10'))

    def test_parseTimeRangeAllUnknown(self):
        self.assertRaises(ValueError, parseTimeRange, '?:?-?:?')


class ParseFreqTest(TestCase):
    def test_parseFreq(self):
        self.assertEqual(parseFreq('daily'), FreqObject(freq=DAILY))

    def test_parseFreqWithInterval(self):
        self.assertEqual(parseFreq('weekly,i2'), FreqObject(freq=WEEKLY, interval=2))

    def test_parseFreqWithCount(self):
        self.assertEqual(parseFreq('monthly,c2'), FreqObject(freq=MONTHLY, count=2))

    def test_parseFreqWithIntervalAndCount(self):
        self.assertEqual(parseFreq('daily,i10,c20'), FreqObject(freq=DAILY, interval=10, count=20))
        self.assertEqual(parseFreq('yearly,c0,i1'), FreqObject(freq=YEARLY, interval=1, count=0))


class ParseByTest(TestCase):
    def test_parseBy(self):
        self.assertEqual(parseBy('by[day[1,2,3]]'), ByObject(byweekday=[MO, TU, WE]))

    def test_parseByDayMonth(self):
        self.assertEqual(parseBy('by[day[1,2,3],month[1,2,3]]'), ByObject(byweekday=[MO, TU, WE], bymonth=[1, 2, 3]))
