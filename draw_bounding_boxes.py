# Kode fra Søby:
# anns = coco.loadAnns(annIds)
# for i in anns:
# [x,y,w,h] = i['bbox']
# cv2.rectangle(Image, (int(x), int(y)), ((int(x+w), int(y+h)), (255,0,0), 5)
# cv2.imshow(' ',Image)
# plt.show()
#
# 'segmentation': []
# 'area': box_width * box_height
# 'iscrowd': 0

import json
import cv2
# import matplotlib.pyplot as plt

json_file = open("./json_annotations/wk1gt_annotations.json")
coco = json.load(json_file)
json_file.close()

for annotation in coco['annotations']:
    image_id = annotation['image_id']
    file_name = ""

    for image in coco['images']:
        if image['id'] is image_id:
            file_name = image['file_name']

    [x, y, w, h] = annotation['bbox']
    image = cv2.imread("./images/" + file_name)
    cv2.rectangle(image, (int(x), int(y)), (int(x+w), int(y+h)), (255,0,0), 5)

    new_file_name = "./images_with_boxes/" + file_name
    cv2.imwrite(new_file_name, image)