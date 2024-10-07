from datetime import datetime
import xml.etree.ElementTree as ET
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

def check_enabled(pn):
  ts = ["record issue", "inspection", "intervention authorization", "action not required", "work mandate", "no concession", "work completion", "issue completion"]
  for t in ts:
    print (pn.is_enabled(pn.transition_name_to_id(t)))
  print("")

def get_direct_succession(log_dict):
    follows = {}
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
    pairs = []

    # Iterate over the dictionary
    for outer_key, inner_dict in follows.items():
        for inner_key in inner_dict.keys():
            # Append the tuple (outer_key, inner_key) to the list
            pairs.append((outer_key, inner_key))
    return pairs
def get_causality_parallel(d_succession):
    causality = set()
    parallel = set()
    for i in d_succession:
        a,b= i
        if (a,b) and (b,a) in d_succession:
            parallel.add((a,b))
            parallel.add((b,a))
        else:
            causality.add((a, b))
    return causality, parallel

def get_choice(d_succession):
    choice = []
    all_element= []
    for i in transitions_unique:
        for j in transitions_unique:
            all_element.append((i,j))
    for i in all_element:
        a,b = i
        if (a,b) not in d_succession and (b,a) not in d_succession:
            choice.append(i)
    return choice
def get_x_w(d_succession,causality,choice):
    x_w = []
    for pair in d_succession:
        a,b = pair
        if (a,b) in causality and (a,a) in choice and (b,b) in choice:
            x_w.append((a,b))
    return x_w
def get_p_w(x_w):
    place_ids = {}
    total_place = len(x_w) + 2
    p.add_place(1)
    p.add_marking(1)
    place_ids["i_w"] = 1
    p_id = 2
    for i in x_w:
        p.add_place(p_id)
        place_ids[i] = p_id
        p_id+= 1
    p.add_place(total_place)
    place_ids["o_w"] = total_place
    return place_ids

transitions_unique = set()
p = PetriNet()


def set_petrinet_flow(x_w, p_w):
    temp_t= 0
    transition_with_id = {}
    for i in transitions_unique:
        temp_t += 1
        t_id = temp_t * -1
        p.add_transition(i,t_id)
        transition_with_id[i] = t_id
    for pair in x_w:
        a,b = pair
        p_id = p_w[pair]
        p.add_edge(transition_with_id[a],p_id)
        p.add_edge(p_id,transition_with_id[b])
    for id, details in p.transitions.items():
        if not details['inputs'] and details['outputs']:
            p.add_edge(p_w["i_w"],id)
        if details['inputs'] and not details['outputs']:
            p.add_edge(id,p_w["o_w"])


def marge_petrinet():
    for t_id, transition in p.transitions.items():
        transition_input = transition['inputs']
        transition_output = transition['outputs']

        # Handle multiple inputs
        if len(transition_input) > 1:
            # Replace inputs with the minimum value
            min_input = min(transition_input)
            p.transitions[t_id]['inputs'] = {min_input}

            for _, t in p.transitions.items():
                inputs = t['inputs']
                outputs = t['outputs']

                # Check for intersection with the original inputs
                if inputs.intersection(transition_input):
                    # Replace old values in inputs
                    for x in list(inputs):  # Use list to avoid modifying the set while iterating
                        if x in transition_input:
                            inputs.remove(x)  # Remove the old value
                            inputs.add(min_input)  # Add the minimum input

                # Check for intersection with the outputs
                if outputs.intersection(transition_input):
                    # Replace old values in outputs
                    for x in list(outputs):  # Use list to avoid modifying the set while iterating
                        if x in transition_input:
                            outputs.remove(x)  # Remove the old value
                            outputs.add(min_input)  # Add the minimum input

        # Handle multiple outputs
        if len(transition_output) > 1:
            # Replace outputs with the minimum value
            min_output = min(transition_output)
            p.transitions[t_id]['outputs'] = {min_output}

            for _, t in p.transitions.items():
                inputs = t['inputs']
                outputs = t['outputs']

                # Check for intersection with the original outputs
                if inputs.intersection(transition_output):
                    # Replace old values in inputs
                    for x in list(inputs):  # Use list to avoid modifying the set while iterating
                        if x in transition_output:
                            inputs.remove(x)  # Remove the old value
                            inputs.add(min_output)  # Add the minimum output

                # Check for intersection with the outputs
                if outputs.intersection(transition_output):
                    # Replace old values in outputs
                    for x in list(outputs):  # Use list to avoid modifying the set while iterating
                        if x in transition_output:
                            outputs.remove(x)  # Remove the old value
                            outputs.add(min_output)  # Add the minimum output
def alpha(log_dict):
    d_succession = get_direct_succession(log_dict)
    t_w = transitions_unique
    causality, parallel = get_causality_parallel(d_succession)
    choice = get_choice(d_succession)
    x_w = get_x_w(d_succession,causality,choice)
    p_w = get_p_w(x_w)
    set_petrinet_flow(x_w,p_w)
    # marge_petrinet()
    return p
if __name__ == "__main__":
    mined_model = alpha(read_from_file("extension-log.xes"))
    trace = ["record issue", "inspection", "intervention authorization", "work mandate", "work completion",
             "issue completion"]
    for a in trace:
        check_enabled(mined_model)
        mined_model.fire_transition(mined_model.transition_name_to_id(a))
