import json
import xmltodict


def init():
    with open("wk1gt.xml") as xml_file:
        data_dict = xmltodict.parse(xml_file.read())

    xml_file.close()

    #
    info = []
    licences = []
    categories = []
    images = []
    annotations = []
    empty_images = []
    person_images = []

    categories.append({
        'id': 1,
        'name': "pedestrain",  # Misspelled on purpose
        'supercategory': "pedestrain"
    })

    for entry in data_dict['dataset']['frame']:
        frame_number = int(entry['@number'])
        image_id = frame_number + 1
        file_name = "Walk" + str(1000 + frame_number) + ".jpg"
        width = 384
        height = 288

        image = {
            'id': image_id,
            'file_name': file_name,
            'width': width,
            'height': height,
            'date_captured': "",
            'licence': 1,
            'coco_url': "",
            'flickr_url': ""
        }

        images.append(image)

        if entry['objectlist'] is None:
            empty_images.append(file_name)
        else:
            person_images.append(file_name)

            objects = entry['objectlist']['object']
            object_list = []
            if isinstance(objects, list):
                object_list = objects
            else:
                object_list.append(objects)

            for obj in object_list:
                bbox = [
                    obj['box']['@h'],
                    obj['box']['@w'],
                    obj['box']['@xc'],
                    obj['box']['@yc']
                ]

                annotation = {
                    'id': len(annotations) + 1,
                    'image_id': image_id,
                    'category_id': 1,
                    'iscrowd': len(objects) > 1,
                    'bbox': bbox,
                    'width': width,
                    'height': height
                }

                annotations.append(annotation)





    json_dict = {
        'info': info,
        'licences': licences,
        'categories': categories,
        'images': images,
        'annotations': annotations,
        'empty_images': empty_images,
        'person_images': person_images
    }



    json_data = json.dumps(json_dict)

    with open("annotations.json", "w") as json_file:
        json_file.write(json_data)

    json_file.close()


init()
