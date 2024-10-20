import xml.etree.ElementTree as ET
from datetime import datetime
import itertools
import copy
from pprint import pprint

class PetriNet():
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.edges = {}
        self.m = self.c = self.r = 0
        self.p = 1
        self.n = 0

    def reset(self):
        self.places = {}
        self.transitions = {}
        self.edges = {}
        self.m = self.c = self.r = 0
        self.p = 1
        self.n = 0

    def reset_para(self):
        self.m = self.c = self.r = 0
        self.p = 1

    def add_place(self, name):
        self.places[name] = 0

    def add_transition(self, name, id):
        self.transitions[name] = id

    def add_edge(self, source, target):
        if source not in self.edges:
            self.edges[source] = []
        if target not in self.edges[source]:
            self.edges[source].append(target)
        return self

    def is_enabled(self, transition):
        if transition not in self.transitions.values():
            return False
        for source in self.edges:
            if transition in self.edges[source] and self.places.get(source, 0) == 0:
                self.places[source] += 2  # Add 2 tokens to the source
                self.m += 1  # Increment m when adding tokens
        return True

    def fire_transition(self, transition):
        if transition not in self.transitions.values() or not self.is_enabled(transition):
            return
        for source in self.edges:
            if source == transition:
                for target in self.edges[source]:
                    self.places[target] += 1
                    self.p += 1  # Increment p for each fired transition
            else:
                for target in self.edges[source]:
                    if target == transition and self.places[source] > 0:
                        self.places[source] -= 1
                        self.c += 1  # Increment c for each consumed token

    def add_marking(self, place):
        self.places[place] += 1

    def get_tokens(self, place):
        return self.places.get(place, 0)

    def get_edges(self):
        return self.edges

    def transition_name_to_id(self, name):
        for transition_name, transition_id in self.transitions.items():
            if transition_name == name:
                return transition_id
        return None

# Petri Net instantiation
pn = PetriNet()
# Add the check_sets function before using it
def check_sets(set_a, set_b, relations):
    for a in set_a:
        for b in set_b:
            if (a, b) not in relations:
                return False
    return True

# Your alpha function and other code continue here...

# Alpha miner implementation
def alpha(log):
    start_activities = set()
    end_activities = set()
    activities = set()
    directly_follows = set()
    directly_follows_dictionary = {}

    for case_events in log.values():
        prev_activity = None
        for event in case_events:
            activity = event.get('concept:name')
            activities.add(activity)

            if prev_activity and activity:
                pair = (prev_activity, activity)
                directly_follows.add(pair)

                if prev_activity in directly_follows_dictionary:
                    if activity not in directly_follows_dictionary[prev_activity]:
                        directly_follows_dictionary[prev_activity].append(activity)
                else:
                    directly_follows_dictionary[prev_activity] = [activity]

            prev_activity = activity

        if case_events:
            start_activities.add(case_events[0]['concept:name'])
            end_activities.add(case_events[-1]['concept:name'])

    # Causal and parallel relations
    causal_relations = set()
    parallel_relations = set()
    choice_relations = set()

    for activity in activities:
        for activity2 in activities:
            pair = (activity, activity2)
            if pair not in directly_follows and (activity2, activity) not in directly_follows:
                choice_relations.add(pair)

    for pair in directly_follows:
        if (pair[1], pair[0]) not in directly_follows:
            causal_relations.add(pair)
        else:
            parallel_relations.add(pair)

    # Xw and Yw sets
    Xw = set()
    subsets = set()
    for activities_amount in range(1, len(activities)):
        for combination in list(itertools.combinations(activities, activities_amount)):
            subsets.add(combination)

    for combination in subsets:
        valid_a = check_sets(combination, combination, choice_relations)
        if valid_a:
            for combination2 in subsets:
                valid_b = check_sets(combination2, combination2, choice_relations)
                if valid_b:
                    valid_a_b = check_sets(combination, combination2, causal_relations)
                    if valid_a_b:
                        Xw.add((combination, combination2))

    Yw = copy.deepcopy(Xw)
    for set_pair in Xw:
        A = set(set_pair[0])
        B = set(set_pair[1])
        for set_pair2 in Xw:
            if set_pair != set_pair2:
                if A.issubset(set_pair2[0]) and B.issubset(set_pair2[1]):
                    Yw.discard(set_pair)

    # Construct Petri net
    place_name = 1
    activity_id = -1
    for activity in activities:
        pn.add_transition(activity, activity_id)
        activity_id -= 1

    for activity in start_activities:
        pn.add_place(place_name)
        target = pn.transition_name_to_id(activity)
        pn.add_edge(place_name, target)
        pn.add_marking(place_name)
        place_name += 1

    for activity in end_activities:
        pn.add_place(place_name)
        source = pn.transition_name_to_id(activity)
        pn.add_edge(source, place_name)
        place_name += 1

    for (sources, targets) in Yw:
        pn.add_place(place_name)
        for source_activity in sources:
            pn.add_edge(pn.transition_name_to_id(source_activity), place_name)
        for target_activity in targets:
            pn.add_edge(place_name, pn.transition_name_to_id(target_activity))
        place_name += 1

    return pn

# Function to read XES log files
def read_from_file(filename):
    log_dictionary = {}
    try:
        tree = ET.parse(filename)
        root = tree.getroot()

        for trace in root.findall(".//{http://www.xes-standard.org/}trace"):
            case_id = None
            events = []
            for attribute in trace.findall("./{http://www.xes-standard.org/}string"):
                if attribute.get("key") == "concept:name":
                    case_id = attribute.get("value")

            for event in trace.findall(".//{http://www.xes-standard.org/}event"):
                event_attributes = event.findall(".//")
                attributes = {}
                for attr in event_attributes:
                    name = attr.get("key")
                    value = attr.get("value")

                    if name == "time:timestamp":
                        value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
                    elif name == "cost":
                        value = int(value)
                    attributes[name] = value
                events.append(attributes)

                if case_id and events:
                    log_dictionary[case_id] = events

    except ET.ParseError:
        print("Error parsing the file")

    return log_dictionary

# Function to get trace frequency
def get_value_k(log):
    traces = set()
    trace_with_n = {}
    for case_id, events in log.items():
        trace = []
        for event in events:
            if 'concept:name' in event:
                trace.append(event['concept:name'])
        traces.add(tuple(trace))

    for trace in traces:
        n = 0
        for case_id, events in log.items():
            trace_case = [event['concept:name'] for event in events if 'concept:name' in event]
            if tuple(trace_case) == trace:
                n += 1
        trace_with_n[trace] = n

    return trace_with_n, traces

# Fitness calculation using token replay
def fitness_token_replay(log, mined_model):
    trace_with_n, traces = get_value_k(log)
    k = len(traces)
    print("k:", k)
    for trace in traces:
        pn.n = trace_with_n[trace]
        pn.reset_para()
        print("Trace being replayed:")
        pprint(trace)
        m_places = copy.deepcopy(pn.places)
        for a in trace:
            mined_model.fire_transition(mined_model.transition_name_to_id(a))

        # Calculating r
        for i in pn.places.keys():
            pn.r += pn.places[i]
        pn.c += 1
        pn.r -= 1  # Decrement r after replay

        print(f"m: {pn.m}, c: {pn.c}, r: {pn.r}, p: {pn.p}")
        pn.places = copy.deepcopy(m_places)  # Reset places after trace replay

    pn.reset()  # Reset the Petri net after fitness calculation
    conformance = 0
    return conformance

if __name__ == "__main__":
    log = read_from_file("extension-log-4.xes")
    log_noisy = read_from_file("extension-log-noisy-4.xes")
    mined_model = alpha(log)
    # print("Transition :")
    # pprint(pn.transitions)
    print(round(fitness_token_replay(log, mined_model), 5))
    print("-----" * 40)
    print(round(fitness_token_replay(log_noisy, mined_model), 5))