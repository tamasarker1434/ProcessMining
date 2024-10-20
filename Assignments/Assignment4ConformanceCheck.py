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
        self.m = self.c = self.r = 0.0
        self.p = 1.0
    def reset(self):
        self.places = {}
        self.transitions = {}
        self.edges = {}
        self.m = self.c = self.r = 0.0
        self.p = 1.0
    def reset_para(self):
        self.m = self.c = self.r = 0.0
        self.p = 1.0
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
                return False

        return True
    def fire_transition(self, transition):

        if transition not in self.transitions.values() or not self.is_enabled(transition):
            for source in self.edges:
                if source == transition:
                    for target in self.edges[source]:
                        self.places[target] += 1
                        self.p += 1
                        self.c += 1

                else:
                    for target in self.edges[source]:
                        if target == transition:
                            self.m += 1
        else:
            for source in self.edges:
                if source == transition:
                    for target in self.edges[source]:
                        self.places[target] += 1
                        self.p += 1

                else:
                    for target in self.edges[source]:
                        if target == transition:
                            self.places[source] -= 1
                            self.c += 1
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
pn = PetriNet()
def alpha(log):
    variable = 1
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

    # Xw set
    Xw = set()
    subsets = set() # all possible combinations of activities

    for activities_amount in range(1, len(activities)): # this will ensure we get sets with all combinations from length of activities to 1 on each side
        for combination in list(itertools.combinations(activities, activities_amount)):
            subsets.add(combination)

    for combination in subsets:
        valid_a = check_sets(combination, combination, choice_relations) # all activities in a are in choice
        if valid_a:
            for combination2 in subsets:
                valid_b = check_sets(combination2, combination2, choice_relations) # all activities in b are in choice
                if valid_b:
                    valid_a_b = check_sets(combination, combination2, causal_relations) # the is a causal relation between each activity from a and from b
                    if valid_a_b:
                        Xw.add((combination, combination2))

    # Yw set
    Yw = copy.deepcopy(Xw) # copy the set Xw so that they are different objects

    for set_pair in Xw:
        A = set(set_pair[0]) # set A
        B = set(set_pair[1]) # set B
        for set_pair2 in Xw:
            if set_pair != set_pair2:
                if A.issubset(set_pair2[0]) and B.issubset(set_pair2[1]):
                    Yw.discard(set_pair)

    # construct Petri Net
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

def check_sets(A, B, set_to_check):
    for activity in A:
        for activity2 in B:
            if (activity, activity2) not in set_to_check:
                return False

    return True


def get_value_k(log):
    traces = set()
    trac_with_n = {}
    for case_id, events in log.items():
        trace = []
        for event in events:
            if 'concept:name' in event:
                trace.append(event['concept:name'])
        traces.add(tuple(trace))
    for i in traces:
        n =0
        for case_id, events in log.items():
            trace = []
            for event in events:
                if 'concept:name' in event:
                    trace.append(event['concept:name'])
            if tuple(trace) == i:
                n += 1
        trac_with_n[i] = n
    return trac_with_n,traces

def fitness_token_replay(log, mined_model):
    n =[]
    m =[]
    c =[]
    r =[]
    p =[]
    trac_with_n, traces = get_value_k(log)
    k = len(traces)
    for trace in traces:
        pn.n = trac_with_n[trace]
        pn.reset_para()
        m_places = copy.deepcopy(pn.places)
        for a in trace:
            mined_model.fire_transition(mined_model.transition_name_to_id(a))
        for i in pn.places.keys():
            pn.r += pn.places[i]
        pn.c += 1
        pn.r -= 1
        n.append(pn.n)
        m.append(pn.m)
        c.append(pn.c)
        r.append(pn.r)
        p.append(pn.p)
        pn.places = copy.deepcopy(m_places)
    conformance = calculate_f(n,m,c,r,p)
    return conformance
def calculate_f(ni, mi, ci, ri, pi):
    # Calculate the numerator and denominator for the first term
    numerator1 = sum(ni[i] * mi[i] for i in range(len(ni)))
    denominator1 = sum(ni[i] * ci[i] for i in range(len(ni)))

    # Calculate the numerator and denominator for the second term
    numerator2 = sum(ni[i] * ri[i] for i in range(len(ni)))
    denominator2 = sum(ni[i] * pi[i] for i in range(len(ni)))

    # Calculate the f value
    f = 0.5 * (1 - numerator1 / denominator1) + 0.5 * (1 - numerator2 / denominator2)

    return f


if __name__ == "__main__":
    log = read_from_file("extension-log-4.xes")
    log_noisy = read_from_file("extension-log-noisy-4.xes")
    mined_model = alpha(log)
    print(round(fitness_token_replay(log, mined_model), 5))
    print(round(fitness_token_replay(log_noisy, mined_model), 5))