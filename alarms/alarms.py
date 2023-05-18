"""
Here are defined the alarms that the system triggers
in the presence of situations out of the normal workflow
"""

from datetime import datetime
from time import sleep

import json


DATE_FORMAT = '%d-%m-%Y-%H-%M-%S'



class Alarm():
    """Base alarm class."""
    def __init__(self,name: str, identifier:str, priority: bool=False, progression_time:int =10):
        """
        Creates an alarm that signals errors in the system

        name : str
            Name of the alarm in the system.

        priority : bool
            Defaults to False signaling the alarm has normal priority. For high priority set to True.
        
        """
        self._name = name
        self._identifier = identifier
        self._priority = priority
        self._progression_time = progression_time
        self._timestamp = datetime.now()

        self._level = 0
    
    @property
    def progression_time(self):
        """Time to progress to alert level in the alarm in the system."""
        return self._progression_time
    
    @property
    def timestamp(self):
        """Instant when the alarm was registered"""
        return self._timestamp
    
    @property
    def name(self):
        """Name of the alarm in the system."""
        return self._name
    
    @property
    def identifier(self):
        """Identifier of the alarm in the system."""
        return self._identifier
    
    @property
    def level(self):
        """Alarm Level corresponding to the severity of the alarm. Values are \'Warning\' and  \'Alarm\'"""
        return self._level
    
    def toggle_level(self, verbosity: int = 0):
        """Change the level of the alarm between \'Warning\' and  \'Alarm\'"""
        
        log =f"{DATE_FORMAT} - {self._name} set to {self._level}"
        self._level = 1 if not self._level else 0
        log = datetime.now().strftime(log)

        if verbosity == 1:
            print(log)
        
        return log
    
    @property
    def priority(self):
        """Alarm priority in the system"""
        return "High Priority" if self._priority else "Normal Priority"
    
    def to_json(self):
        json_dict = {
            'name': self.name,
            'identifier': self.identifier,
            'priority': self.priority,
            'level': self.level,
        }

        return json.dumps(json_dict)
    
    

class TrafficJamAlarm(Alarm):
    """Alarm that signals a traffic jam"""
    def __init__(self,line_id:int, name: str, identifier:str,  priority: bool=False, threshold:int = 30):
        """
        Creates an alarm that signals a traffic jam

        name : str
            Name of the alarm in the system.

        priority : bool
            Defaults to False signaling the alarm has normal priority. For high priority set to True.
        
        threshold : int
           The amount of cars per second for the system to consider a line to be on a traffic jam
        
        """
        super().__init__(name, identifier, priority)
        self._threshold = threshold
        self._line_id = line_id

    @property
    def threshold(self):
        return self._threshold
    @property
    def line_id(self):
        return self._line_id
    
    def to_json(self):
        json_dict:dict = json.loads(super().to_json())

        json_dict['line_id'] = self.line_id
        json_dict['threshold'] = self.threshold

        return json.dumps(json_dict)
    

class CommunicationAlarm(Alarm):
    """Alarm that signals a communication errors with parts of the system"""
    def __init__(self,name: str, identifier:str, priority: bool=False, retries:int = 4):
        """
        Creates an alarm that signals a traffic jam

        name : str
            Name of the alarm in the system.

        priority : bool
            Defaults to False signaling the alarm has normal priority. For high priority set to True.
        
        retries : int
           The amount of retries for the system to switch from \'Warning\' to \'Alert\' 
        
        """
        super().__init__(name, identifier, priority)
        self._retries = retries

    @property
    def retries(self):
        """The amount of retries for the system to transit from \'Warning\' to \'Alert\' """
        return self._retries
    
    def countdown(self, verbosity: int = 0):
        """Makes a countdown to the point of transition from \'Warning\' to \'Alert\'"""
        if self._retries > 0:
            self._retries -= 1

        if verbosity == 1:
            log = f"{DATE_FORMAT} - {self._name} : Retrying {self._retries} more times"
            log = datetime.now().strftime(log)
            print(log)

    def to_json(self):
        json_dict:dict = json.loads(super().to_json())

        json_dict['retries'] = self.retries

        return json.dumps(json_dict)



#########################################################################################################################################      

if __name__ == '__main__':
    def check_behavior(a: Alarm):
        print(a.to_json())
        
    
    simple_comm_alarm = CommunicationAlarm(name='Error de comunicacion con sistema de reconocimiento')
    simple_traff_alarm = TrafficJamAlarm(name ='Embotellamiento en linea 1', priority=True, line_id=0)

    check_behavior(simple_comm_alarm)
    check_behavior(simple_traff_alarm)

    