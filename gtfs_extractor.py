import heapq
import functools
import time
from gtfs_getter import get_latest

_FOLDER = "corrected_gtfs/"

_CALENDAR_DATES_ONLY = True

_STOP_PENALTY = 2000
_MAX_COUNT = 20


if _CALENDAR_DATES_ONLY:
    calendar = {}
    with open(_FOLDER+"calendar_dates.txt",encoding="utf-8") as f:
        l = f.readlines()
        for i in range(1,len(l)):
            line = l[i].split(",")
            calendar[line[0]] = (line[1],int(line[2]))


def extract_file(filename,obj_type):
    list_obj = set()
    with open(filename,encoding="utf-8") as f:
        l = f.readlines()
        fields = l[0].strip().split(",")
        for i in range(1,len(l)):
            line = l[i].strip().split(",")
            attr = {fields[k]:line[k] for k in range(len(fields))}
            list_obj.add(obj_type(attr))
    return list_obj
        

class Service_Time:
    """
    Class representing a service time
    """
    def __init__(self, kwattrs):
        self.fields = ["service_id","date","exception_type"]
        for f in self.fields:
            self.__setattr__(f, kwattrs[f])


class Route:
    """
    Class representing a route
    """
    def __init__(self, kwattrs):
        self.fields = ["route_id","agency_id","route_short_name","route_long_name","route_desc","route_type"]
        for f in self.fields:
            self.__setattr__(f, kwattrs[f])


class Trip:
    """
    Class representing a trip
    """
    def __init__(self, kwattrs):
        self.fields = ["route_id","service_id","trip_id","trip_headsign","direction_id"]
        for f in self.fields:
            self.__setattr__(f, kwattrs[f])

class NullTrip:
    def __init__(self):
        self.trip_id = -1

class Stop:
    """
    Class representing a trip
    """
    def __init__(self, kwattrs):
        self.fields = ["stop_id","stop_name","stop_desc","stop_lat","stop_lon","location_type","parent_station"]
        for f in self.fields:
            self.__setattr__(f, kwattrs[f])


@functools.total_ordering
class Stop_Time:
    """
    Class representing a trip
    """
    def __init__(self, kwattrs):
        self.fields = ["trip_id","arrival_time","departure_time","stop_id","stop_sequence","pickup_type","drop_off_type"]
        for f in self.fields:
            self.__setattr__(f, kwattrs[f])
        self.stop_sequence = int(self.stop_sequence)

    def __lt__(self, other):
        return ((self.arrival_time, self.stop_id) <
                (other.arrival_time, other.stop_id))
    
    def __hash__(self):
        return hash(tuple([self.__getattribute__(f) for f in self.fields]))


class Agency:
    """
    Class representing a trip
    """
    def __init__(self, kwattrs):
        self.fields = ["trip_id","arrival_time","departure_time","stop_id","stop_sequence","pickup_type","drop_off_type"]
        for f in self.fields:
            self.__setattr__(f, kwattrs[f])


class DijkstraElement:
    def __init__(self,stop,time,status,previous):
        self.stop = stop
        self.time = time
        self.status = status
        self.previous = previous

    def __eq__(self, other):
        return ((self.stop, self.time) ==
                (other.stop, other.time))
    
    def __lt__(self, other):
        return ((self.stop, self.time) <
                (other.stop, other.time))
    
    def __hash__(self):
        return hash((self.stop,self.time))

def compare_times(t1,t2):
    """
    les heures doivent être fournies au format HH:MM:SS
    renvoie t1>=t2
    """
    t1 = [int(i) for i in t1.split(":")]
    t2 = [int(i) for i in t2.split(":")]
    if t1[0]>t2[0]:
        return True
    elif t1[0]<t2[0]:
        return False
    else:
        if t1[1]>t2[1]:
            return True
        elif t1[1]<t2[1]:
            return False
        else:
            if t1[2]>=t2[2]:
                return True
            return False


def get_services_on_dates(dates_list):
    """
    les dates doivent être au format AAAAMMJJ
    """
    service_times = set()
    for service in _SERVICE_TIMES_LIST:
        if service.date in dates_list:
            service_times.add(service)
    return service_times

def get_trips_on_dates(dates_list):
    service_times = get_services_on_dates(dates_list)
    service_id_list = set([i.service_id for i in service_times])
    trips = set()
    for trip in _TRIPS_LIST:
        if trip.service_id in service_id_list:
            trips.add(trip)
    return trips

def get_stops_on_dates(dates_list):
    trips_on_time = get_trips_on_dates(dates_list)
    trip_id_list = set([i.trip_id for i in trips_on_time])
    stop_times = set()
    for stop in _STOP_TIMES_LIST:
        if stop.trip_id in trip_id_list:
            stop_times.add(stop)
    return stop_times


def get_all_stations_from_stop(departure_stop):
    following_trips = _NEXT_STOPS_FROM_TRIP[departure_stop.trip_id][departure_stop]
    return following_trips

def get_all_trips_after_stop(arrival_stop,stops_list,trip_to_avoid):
    """
    The arrival stop,
    the list of the available stops
    the id of the trip to avoid if there is one
    """
    next_departures = []
    for stop in _STOPS_FROM_STOP[arrival_stop.stop_id]:
        if compare_times(stop.departure_time, arrival_stop.arrival_time) and stop.trip_id!=trip_to_avoid and stop in stops_list:
            next_departures.append(stop)
    return next_departures


def time_diff(t1,t2):
    """
    computes t1-t2 in seconds, times are to be given in the form hh:mm:ss

    """
    t1 = [int(i) for i in t1.split(":")]
    t2 = [int(i) for i in t2.split(":")]
    return 3600*(t1[0]-t2[0])+60*(t1[1]-t2[1])+t1[2]-t2[2]

def dijkstra_trip(departure_id,arrival_id,dates,talkative=False):
    stops = get_stops_on_dates(dates)
    dist_heap = []
    current_dist = {}
    seen = set()
    
    for stop in stops:
        if stop.stop_id==departure_id:
            heapq.heappush(dist_heap,(0,DijkstraElement(stop, 0, "onboard", None)))
            current_dist[stop]=0
    
    current = heapq.heappop(dist_heap)
    while len(dist_heap) != 0 and current[1].stop.stop_id != arrival_id:
        if talkative:
            print(len(dist_heap))
            print("time : "+str(current[0])+", station : "+stop_name(current[1].stop)+", status : "+current[1].status)
        
        if current[0]==current_dist[current[1].stop] and current[1].stop not in seen:
            current_stop = current[1]
            if current_stop.status == "onboard":
                next_possible = get_all_stations_from_stop(current_stop.stop)
                for i in next_possible:
                    new_time = current[0]+time_diff(i.arrival_time,current_stop.stop.departure_time)
                    if i in current_dist:
                        if current_dist[i]>new_time:
                            current_dist[i] = new_time
                            to_add = DijkstraElement(i, new_time, "station", current_stop)
                            heapq.heappush(dist_heap,(new_time,to_add))
                    else:
                        current_dist[i] = new_time
                        to_add = DijkstraElement(i, new_time, "station", current_stop)
                        heapq.heappush(dist_heap,(new_time,to_add))
                        
            elif current_stop.status == "station":
                next_possible = get_all_trips_after_stop(current_stop.stop,stops,current_stop.stop.trip_id)
                for i in next_possible:
                    new_time = current[0]+time_diff(i.departure_time,current_stop.stop.arrival_time)
                    if i in current_dist:
                        if current_dist[i]>new_time:
                            current_dist[i] = new_time
                            to_add = DijkstraElement(i, new_time, "onboard", current_stop)
                            heapq.heappush(dist_heap,(new_time,to_add))
                    else:
                        current_dist[i] = new_time
                        to_add = DijkstraElement(i, new_time, "onboard", current_stop)
                        heapq.heappush(dist_heap,(new_time,to_add))
                
        seen.add(current[1].stop)
        current = heapq.heappop(dist_heap)
        
        
    if current[1].stop.stop_id == arrival_id:
        path = [current[1]]
        while isinstance(path[-1].previous,DijkstraElement):
            path.append(path[-1].previous)
        return path
    else:
        print("unable to find path on given dates")
        return []
    

def stop_name(stop):
    return _STOPS_DICT[stop.stop_id].stop_name

def dijkstra_clean_prompt(departure,arrival,dates,Talkative=False):
    start = time.time()
    new_dates = []
    for i in dates:
        d = i.split("/")
        new_dates.append("".join(d[::-1]))
    for i in _STOPS_LIST:
        if departure == i.stop_name and "Train" in i.stop_id:
            departure_id = i.stop_id
            break
    for i in _STOPS_LIST:
        if arrival == i.stop_name and "Train" in i.stop_id:
            arrival_id = i.stop_id
            break
    result = dijkstra_trip(departure_id,arrival_id,new_dates,Talkative)
    print(time.time()-start)
    return result[::-1]

def clean_time(seconds):
    minutes = (seconds//60)
    hours = minutes//60
    minutes = minutes%60
    minutes = str(minutes)
    hours = str(hours)
    if len(minutes)==1:
        minutes = "0"+minutes
    return hours+"h"+minutes+"m"

def clean_hour(t):
    t = time_diff(t,"00:00:00")
    t = clean_time(t)
    if len(t)==5:
        t = "0"+t
    return t

def display_trip(t):
    for i in sorted(t,key = lambda x:x.departure_time):
        print(stop_name(i)+" à "+i.arrival_time)
    
def display_dijkstra(t):
    for i in t:
        print(stop_name(i.stop)+" à "+i.stop.arrival_time+", statut : "+i.status)

def better_dijkstra(l):
    print("departure from "+stop_name(l[0].stop)+" at "+clean_hour(l[0].stop.departure_time))
    for i in range(1,len(l)):
        if l[i].status == "onboard":
            print(clean_time(time_diff(l[i].stop.departure_time,l[i-1].stop.arrival_time))+" connection in "+stop_name(l[i].stop))
        elif l[i].status == "station":
            print(stop_name(l[i-1].stop)+" at "+clean_hour(l[i-1].stop.departure_time)+" -> "+stop_name(l[i].stop)+" at "+clean_hour(l[i].stop.arrival_time))
    print("arrival in "+stop_name(l[-1].stop)+" at "+clean_hour(l[-1].stop.arrival_time))

start = time.time()
get_latest()
print("gtfs requesting time : "+str(round(time.time()-start,2))+" seconds")

start = time.time()

_SERVICE_TIMES_LIST = extract_file(_FOLDER+"/calendar_dates.txt", Service_Time)
_SERVICE_TIMES_DICT = {}
for i in _SERVICE_TIMES_LIST:
    if i.service_id in _SERVICE_TIMES_DICT:
        _SERVICE_TIMES_DICT[i.service_id].append(i)
    else:
        _SERVICE_TIMES_DICT[i.service_id] = [i]
_ROUTES_LIST = extract_file(_FOLDER+"/routes.txt",Route)
_ROUTES_DICT = {i.route_id:i for i in _ROUTES_LIST}
_TRIPS_LIST = extract_file(_FOLDER+"/trips.txt",Trip)
_TRIPS_DICT = {i.trip_id:i for i in _TRIPS_LIST}
_STOP_TIMES_LIST = extract_file(_FOLDER+"/stop_times.txt",Stop_Time)
_STOPS_LIST = extract_file(_FOLDER+"/stops.txt",Stop)
_STOPS_DICT = {i.stop_id:i for i in _STOPS_LIST}
_STOPS_FROM_TRIP = {}

print("basic extraction time : "+str(round(time.time()-start,2))+" seconds (without dicts)")

for i in _STOP_TIMES_LIST:
    if i.trip_id in _STOPS_FROM_TRIP:
        _STOPS_FROM_TRIP[i.trip_id].append(i)
    else:
        _STOPS_FROM_TRIP[i.trip_id] = [i]

_NEXT_STOPS_FROM_TRIP = {i:{j:[] for j in _STOPS_FROM_TRIP[i]} for i in _STOPS_FROM_TRIP}
for i in _STOPS_FROM_TRIP:
    for j in _STOPS_FROM_TRIP[i]:
        for k in _STOPS_FROM_TRIP[i]:
            if k.stop_sequence>j.stop_sequence:
                _NEXT_STOPS_FROM_TRIP[i][j].append(k)

_STOPS_FROM_STOP = {}
for i in _STOP_TIMES_LIST:
    if i.stop_id in _STOPS_FROM_STOP:
        _STOPS_FROM_STOP[i.stop_id].append(i)
    else:
        _STOPS_FROM_STOP[i.stop_id] = [i]
    

print("total extraction time : "+str(round(time.time()-start,2))+" seconds")
