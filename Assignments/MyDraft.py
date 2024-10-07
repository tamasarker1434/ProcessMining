from pprint import pprint
transitions_unique={"a","b","c"}
d_succession ={("a","b"),("b","a","b","c")}
choice = []
all_element= []
for i in transitions_unique:
    for j in transitions_unique:
        all_element.append((i,j))
for i in all_element:
    a,b = i
    if (a,b) not in d_succession and (b,a) not in d_succession:
        choice.append(i)
pprint(choice)