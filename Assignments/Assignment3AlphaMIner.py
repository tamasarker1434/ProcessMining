import xml.etree.ElementTree as ET
from datetime import datetime
from pprint import pprint


class PetriNet:
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.edges = {}
    def add_place(self, name):
        self.places[name] = 0
        return self

    def add_transition(self, name, t_id):
        self.transitions[t_id] = {
            'name': name,
            'inputs': set(),
            'outputs': set()
        }
        return self
    def add_edge(self, source, target):
        if source > 0 > target:
            self.transitions[target]['inputs'].add(source)
        elif source < 0 < target:
            self.transitions[source]['outputs'].add(target)
        return self
    def get_tokens(self, place):
        return self.places[place]
    def is_enabled(self, transition):
        for place in self.transitions[transition]['inputs']:
            if self.places[place] == 0:
                return False
        return True
    def add_marking(self, place):
        self.places[place] += 1
        return self
    def fire_transition(self, transition):
        if self.is_enabled(transition):
            for place in self.transitions[transition]['inputs']:
                self.places[place] -= 1
            for place in self.transitions[transition]['outputs']:
                self.places[place] += 1
        return self
    def transition_name_to_id(self, name):
        for transition_id, transition_data in self.transitions.items():
            if transition_data['name'] == name:
                return transition_id
        return None
def read_from_file(filename):
    log_dict = {}
    tree = ET.parse(filename)
    root = tree.getroot()
    namespace = "{http://www.xes-standard.org/}"
    for trace in root.findall(f"{namespace}trace"):
        case_id = None
        events = []
        for string in trace.findall(f"{namespace}string"):
            if string.attrib.get("key") == "concept:name":
                case_id = string.attrib.get("value")
                break
        if case_id is None:
            continue
        for event in trace.findall(f"{namespace}event"):
            event_data = {}
            for string in event.findall(f"{namespace}string"):
                key = string.attrib.get("key")
                value = string.attrib.get("value")
                if key and value is not None:
                    event_data[key] = value

            for date in event.findall(f"{namespace}date"):
                key = date.attrib.get("key")
                date_value = date.attrib.get("value")
                if key and date_value is not None:
                    try:
                        dt = datetime.strptime(date_value, "%Y-%m-%dT%H:%M:%S.%f")
                    except ValueError:
                        try:
                            dt = datetime.strptime(date_value, "%Y-%m-%dT%H:%M:%S%z")
                        except ValueError:
                            dt = date_value
                    if isinstance(dt, datetime):
                       event_data[key] = dt.replace(tzinfo=None)
                    else:
                        event_data[key] = dt
            for int_val in event.findall(f"{namespace}int"):
                key = int_val.attrib.get("key")
                value = int_val.attrib.get("value")
                if key and value is not None:
                    try:
                        event_data[key] = int(value)
                    except ValueError:
                        event_data[key] = value
            for float_val in event.findall(f"{namespace}float"):
                key = float_val.attrib.get("key")
                value = float_val.attrib.get("value")
                if key and value is not None:
                    try:
                        event_data[key] = float(value)
                    except ValueError:
                        event_data[key] = value
            events.append(event_data)
        log_dict[case_id] = events
    return log_dict
def alpha(log_dict):
    follows = {}
    transitions_unique = set()
    for case_id, events in log_dict.items():
        tasks = [event['concept:name'] for event in events]
        for i in range(len(tasks) - 1):
            source = tasks[i]
            target = tasks[i + 1]
            transitions_unique.add(source)
            transitions_unique.add(target)
            if source not in follows:
                follows[source] = {}
            if target not in follows[source]:
                follows[source][target] = 0
            follows[source][target] += 1

    print("Follow:")
    pprint(follows)
    print("Transitions U:",transitions_unique)
    p = PetriNet()
    p.add_place(1)
    p.add_marking(1)
    transition_with_id = {}
    for i, transition in enumerate(transitions_unique, start=1):
        t_id = i * -1
        transition_with_id[transition] = t_id
        print("Transition:T_id=>",transition,t_id)
        p.add_transition(transition,t_id)
    p_id=2
    for source, inter_items in follows.items():
        place = -1
        for target, _ in inter_items.items():
            if p.transitions[transition_with_id[target]]['inputs']:
                for i in p.transitions[transition_with_id[target]]['inputs']:
                    place = i
                    continue
            if place <0 :
                place = p_id
                p.add_place(place)
                p_id += 1
                continue
        for target, _ in inter_items.items():
            p.add_edge(place, transition_with_id[target])
        p.add_edge(transition_with_id[source], place)
    for id, details in p.transitions.items():
        if not details['inputs'] and details['outputs']:
            p.add_edge(1,id)
        if details['inputs'] and not details['outputs']:
            p.add_place(p_id)
            p.add_edge(id,p_id)
            p_id+= 1
    print("Places",p.places)
    print("Transitions:",)
    for t_id, transition in p.transitions.items():
        print(f"Transition ID: {t_id}")
        print(f"Name: {transition['name']}")
        print(f"Inputs: {transition['inputs']}")
        print(f"Outputs: {transition['outputs']}")
        print("-" * 30)  # Separator for be
    return p

def check_enabled(pn):
  ts = ["record issue", "inspection", "intervention authorization", "action not required", "work mandate", "no concession", "work completion", "issue completion"]
  for t in ts:
    print (pn.is_enabled(pn.transition_name_to_id(t)))
  print("")

if __name__ == "__main__":
    mined_model = alpha(read_from_file("loan-process.xes"))
    trace = ["record issue", "inspection", "intervention authorization", "work mandate", "work completion",
             "issue completion"]
    for a in trace:
        check_enabled(mined_model)
        mined_model.fire_transition(mined_model.transition_name_to_id(a))
