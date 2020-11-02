import json

import cv2


def run():
    json_file = open("./json_annotations/wk1gt_annotations.json")
    json_data = json.load(json_file)
    json_file.close()

    image_dir = "./images/"
    processed_images_dir = "./processed_images/"

    # Copy images from images dir to processed_images dir
    copy_images(image_dir, processed_images_dir, json_data)

    # Loop through all images in dataset
    for image in json_data['images']:
        file_name = image['file_name']
        print("Processing image " + file_name)
        image_id = image['id']
        file_path = processed_images_dir + file_name
        image = cv2.imread(file_path)

        # Draw boxes according to annotations for specified image
        draw_boxes(image, image_id, json_data)
        cv2.imwrite(file_path, image)

    print("Done...")


def copy_images(from_dir, to_dir, json_data):
    print("Copying images from " + from_dir + " to " + to_dir + "...")
    for image in json_data['images']:
        file_name = image['file_name']
        image = cv2.imread(from_dir + file_name)
        cv2.imwrite(to_dir + file_name, image)


def draw_boxes(image, image_id, json_data):
    for annotation in json_data['annotations']:
        if annotation['image_id'] is image_id:
            # x,y coordinates are center coordinates of box
            # w,h is width and height of box
            [x, y, w, h] = annotation['bbox']
            cv2.rectangle(image, (int(x - w/2), int(y - h/2)), (int(x + w/2), int(y + h/2)), (255, 0, 0), 1)


run()