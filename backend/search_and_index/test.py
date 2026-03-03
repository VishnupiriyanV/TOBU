import json

f = open("transcript.json","r")
data = json.load(f)
list1 = []
for seg in data:
            
            list1.append(seg["text"])

print(list1[1])

