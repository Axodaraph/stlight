"""Management of alarms and functional security"""
from .alarms import Alarm, CommunicationAlarm, TrafficJamAlarm
from datetime import datetime

class AlarmSystem():
    """System in charge of managing alarms"""
    def __init__(self, carril_izq_threshold:int, carril_der_threshold:int, comm_retries:int=4, timeout:int=15):
        """Initializes the AlarmSystem object"""

        self._alarms = {
            "communication" : [],
            "traffic" : []
        }

        self._system_status = {
            'COM-POW': 0,
            'COM-CV0': 0,
            'COM-HT0': 0,
            'TRF-CI': 0,
            'TRF-CD': 0,
        }

        self._carril_izq_thr = carril_izq_threshold
        self._carril_der_thr = carril_der_threshold
        self._comm_retries = comm_retries
        self._timeout = timeout
        self._latest_check = datetime.now()
    
    @property
    def system_status(self):

        alarms = self.active_alarms()
        alarms = {alarm.identifier:alarm.level for alarm in alarms}


        for al, level in alarms.items():
            self._system_status[al] = level+1

        return list(self._system_status.values())

    def deactivate_alarm(self, alarm_identifier:str, alarm_type:str):
        for a in self._alarms[alarm_type]:
                if a.identifier == alarm_identifier:
                    self._alarms[alarm_type].remove(a)
                    print(f'Desactivada la alarma {a.identifier}')
                    self._system_status[a.identifier] = 0
                    break
    
    def detect_traffic_jam(self, counts:tuple):
        thresholds = (self._carril_izq_thr,self._carril_der_thr)
        jammed_lines = [a.line_id for a in self._alarms['traffic']]
        raised_alarms = []
        street_ids = {
            0: 'izq',
            1: 'der'
        }
        
        def check_street_line(id:int, count:int, threshold: int):
            ident = f"TRF-C{street_ids[id][0].capitalize()}"
            if count > threshold and id not in jammed_lines:
                name = f"Embotellamiento en carril {street_ids[id]}"
                jammed_lines.append(id)
                new_alarm = TrafficJamAlarm(
                    line_id= id,
                    name=name,
                    identifier=ident,
                    threshold=threshold
                )
                raised_alarms.append(new_alarm)
                self._alarms['traffic'].append(new_alarm)
            elif count < threshold and id in jammed_lines:
                self.deactivate_alarm(
                    alarm_identifier=ident,
                    alarm_type='traffic'
                )
        
        for id, threshold in enumerate(thresholds):
            check_street_line(id, counts[id], threshold)
        
        return raised_alarms if raised_alarms else []

    def detect_sensor_disconnection(self, ts: str, pattern: str, identifier: str, name: str, priority= True):
        
        if not self._alarms:  # check if the list is empty
            return
        
        latest_timestamp= datetime.strptime(ts, pattern)

        t_delta= datetime.now() - latest_timestamp

        alarm_activated= identifier in [a.identifier for a in self.active_alarms()]
        
        if t_delta.seconds>= self._timeout and not alarm_activated:
            new_alarm = CommunicationAlarm(
                name=f"Error de comunicación con {name}",
                identifier=identifier,
                priority=priority
            )
            self._alarms['communication'].append(new_alarm)
        
            return new_alarm
    def detect_sensor_reconnection(self, ts: str, pattern: str, identifier:str):
        if not self._alarms:  # check if the list is empty
            return
        
        latest_timestamp= datetime.strptime(ts, pattern)

        t_delta= datetime.now() - latest_timestamp

        alarm_activated= identifier in [a.identifier for a in self.active_alarms()]
        if t_delta.seconds < self._timeout and alarm_activated:
            self.deactivate_alarm(
                    alarm_identifier=identifier,
                    alarm_type='communication'
                )
    
    def active_alarms(self, mode:str = 'object'):
        alarms = self._alarms['communication'].copy()
        alarms.extend(self._alarms['traffic'])

        return [a if mode == 'object' else a.to_json() 
                for a in alarms]
    @property
    def level_of_alarms(self):
        return {a.name:a.level for a in self.active_alarms()}
        
    def check_progression(self):
        dt = datetime.now()

        def checker(a:Alarm):
            td = dt - a.timestamp
            if td.seconds == a.progression_time:
                a.toggle_level()
                print(f"{a.identifier} has progressed to {a.level}")
            return a
        
        
        for t in ['communication', 'traffic']:
            self._alarms[t] = [checker(a)
                        for a in self._alarms[t]]