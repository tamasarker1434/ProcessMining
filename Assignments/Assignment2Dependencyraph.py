import xml.etree.ElementTree as ET
from datetime import datetime

def log_as_dictionary(log):
    case_dictionary ={}
    lines = log.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        parts = line.split(';')
        if len(parts) == 4:
            task, case_id, user, timestamp = parts
            event_log = {
                "task": task,
                "user": user,
                "timestamp": timestamp
            }
        case_dictionary.setdefault(case_id,[]).append(event_log)
    return case_dictionary
def dependency_graph_inline(log):
    dg ={}
    for case_id, events in log.items():
        tasks = [event['task'] for event in events]
        for i in range(len(tasks) - 1):
            source = tasks[i]
            target = tasks[i + 1]
            if source not in dg:
                dg[source] = {}

            if target not in dg[source]:
                dg[source][target] = 0

            dg[source][target] += 1
    return dg
import xml.etree.ElementTree as ET
from datetime import datetime

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
def dependency_graph_file(log):
    return dependency_graph_inline(log)

if __name__ == "__main__":
    f = """Task_A;case_1;user_1;2019-09-09 17:36:47
    Task_B;case_1;user_3;2019-09-11 09:11:13
    Task_D;case_1;user_6;2019-09-12 10:00:12
    Task_E;case_1;user_7;2019-09-12 18:21:32
    Task_F;case_1;user_8;2019-09-13 13:27:41
    
    Task_A;case_2;user_2;2019-09-14 08:56:09
    Task_B;case_2;user_3;2019-09-14 09:36:02
    Task_D;case_2;user_5;2019-09-15 10:16:40
    
    Task_G;case_1;user_6;2019-09-18 19:14:14
    Task_G;case_2;user_6;2019-09-19 15:39:15
    Task_H;case_1;user_2;2019-09-19 16:48:16
    Task_E;case_2;user_7;2019-09-20 14:39:45
    Task_F;case_2;user_8;2019-09-22 09:16:16
    
    Task_A;case_3;user_2;2019-09-25 08:39:24
    Task_H;case_2;user_1;2019-09-26 12:19:46
    Task_B;case_3;user_4;2019-09-29 10:56:14
    Task_C;case_3;user_1;2019-09-30 15:41:22"""
    log = log_as_dictionary(f)
    dg = dependency_graph_inline(log)
    for ai in sorted(dg.keys()):
        for aj in sorted(dg[ai].keys()):
            print(ai, '->', aj, ':', dg[ai][aj])
    log = read_from_file("extension-log.xes")
    for case_id in sorted(log):
        print((case_id, len(log[case_id])))
    case_id = "case_123"
    event_no = 0
    print((log[case_id][event_no]["concept:name"], log[case_id][event_no]["org:resource"],
           log[case_id][event_no]["time:timestamp"], log[case_id][event_no]["cost"]))
