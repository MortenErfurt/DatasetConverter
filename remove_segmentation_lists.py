import json


def run():
    json_file = open('../../Datalogi/S9/Deep Learning/Ny mappe/train.json')
    json_data = json.load(json_file)

    for annotation in json_data['annotations']:
        if 'segmentation' in annotation:
            del annotation['segmentation']

    json_file.close()
    resulting_json_data = json.dumps(json_data)

    with open('../../Datalogi/S9/Deep Learning/Ny mappe/train2.json', "w") as resulting_json_file:
        resulting_json_file.write(resulting_json_data)

    resulting_json_file.close()


run()
