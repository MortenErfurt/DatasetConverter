import os

import numpy as np
import cv2

def rotate_image(image, angle):
  image_center = tuple(np.array(image.shape[1::-1]) / 2)
  rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
  result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
  return result


def run():
    image_dir = "./images/"
    processed_images_dir = "./rotated_images/"

    for file in os.scandir(image_dir):
        print("Processing image " + file.name)
        image = cv2.imread(file.path)
        rotated_image = rotate_image(image, -90)
        cv2.imwrite(processed_images_dir + "/" + file.name, rotated_image)


run()