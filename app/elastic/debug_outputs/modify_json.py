import json

def split_subheader(input_file, output_file):
    with open(input_file, 'r') as infile:
        data = json.load(infile)

    for document in data:
        subheader = document['subheader']
        split_subheaders = [subheader[i:i+50] for i in range(0, len(subheader), 50)]

        # Replace empty strings with placeholder
        split_subheaders = ["N/A" if not s.strip() else s for s in split_subheaders]

        document['subheader'] = split_subheaders

    with open(output_file, 'w') as outfile:
        json.dump(data, outfile, indent=2)

# Example usage
split_subheader('../data/extracted_datas_new.json', 'output.json')
