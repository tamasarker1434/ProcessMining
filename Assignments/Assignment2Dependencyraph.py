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

        # Iterate over tasks to build dependencies
        for i in range(len(tasks) - 1):
            source = tasks[i]
            target = tasks[i + 1]
            if source not in dg:
                dg[source] = {}

            if target not in dg[source]:
                dg[source][target] = 0

            dg[source][target] += 1
    return dg

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
