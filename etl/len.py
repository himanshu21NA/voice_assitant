import json

with open("local_dataset.json", "r") as f:
    len_dict = json.load(f)

word_counts = {}
all_word_counts = []
for k, v in len_dict.items():
    id = 0
    word_counts[k] = {}
    if k == "vehicle_inventory":
        for item in v:
            if isinstance(item, dict):
                text = f"{item.get('year','')} {item.get('make','')} {item.get('model','')}, Trim: {item.get('trim','')}, Price: {item.get('price','')}, Fuel Type: {item.get('fuel','')}, Description: {item.get('description','')}"
                wc = len(text.split())
                word_counts[k][id] = wc
                all_word_counts.append(wc)
                id += 1
            elif isinstance(item, str):
                wc = len(item.split())
                word_counts[k][id] = wc
                all_word_counts.append(wc)
                id += 1
    else:
        for item in v:
            if isinstance(item, str):
                wc = len(item.split())
                word_counts[k][id] = wc
                all_word_counts.append(wc)
                id += 1

for k in word_counts:
    total = sum(word_counts[k].values())
    avg = total / len(word_counts[k]) if word_counts[k] else 0
    print(f"{k}: Total words = {total}, Average words per entry = {avg:.2f}")

# Print overall average
if all_word_counts:
    overall_avg = sum(all_word_counts) / len(all_word_counts)
    print(f"Overall average words per entry: {overall_avg:.2f}")
else:
    print("No entries found for overall average.")