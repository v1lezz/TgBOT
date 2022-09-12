from icalendar import Calendar

class Event:
    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end

def getEvents(file):
    events = []
    g = open(file,'rb')
    gcal = Calendar.from_ical(g.read())
    for component in gcal.walk():
        if component.name == "VEVENT":
            events.append(Event(str(component.get('summary')), component.get('dtstart').dt, component.get('dtend').dt))
    g.close()
    return events