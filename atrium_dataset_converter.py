import json
import os
import sqlite3
import shutil
from sqlite3 import Error


class AtriumDatasetConverter:
    def create_connection(self, db_file):
        """ create a database connection to a SQLite database """
        connection = None
        try:
            connection = sqlite3.connect(db_file)
        except Error as e:
            print(e)

        return connection

    def select_bounding_boxes_by_frame_number(self, connection, frame_number):
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM bounding_boxes WHERE frame_number=?', (frame_number,))

        rows = cursor.fetchall()
        return rows

    def convert_dataset(self, frame_jump):
        info = {
            'description': "Atrium Dataset",
            'url': "http://www.jpjodoin.com/urbantracker/",
            'version': "1.0.0",
            'year': 0,
            'contributor': "",
            'date_created': ""
        }

        licenses = []
        categories = []
        images = []
        annotations = []

        licenses.append({
            'url': "http://creativecommons.org/licenses/by-nc-sa/2.0/",
            'id': 1,
            'name': "Attribution-NonCommercial-ShareAlike License"
        })

        categories.append({
            'id': 0,
            'name': 'person'
        })

        # DO MAGIC HERE
        image_id = 0
        remaining_jumps = frame_jump

        connection = self.create_connection('atrium_annotations/atrium_gt.sqlite')

        atrium_frames_path = 'atrium_frames'
        atrium_frames = [f for f in os.listdir(atrium_frames_path) if os.path.isfile(os.path.join(atrium_frames_path, f))]
        for frame in atrium_frames:
            frame_number = int(frame[:-4])

            if remaining_jumps > 0:
                remaining_jumps = remaining_jumps - 1
                continue
            else:
                print('Processing frame: ' + frame)

                # Increment image_id
                image_id = image_id + 1

                # Reset remaining_jumps (as we are here, we know that we should skip the next frame_jump frames)
                remaining_jumps = frame_jump

                # Copy file to val folder
                shutil.copy(os.path.join(atrium_frames_path, frame), 'val')

                # Find bounding boxes
                bbox_rows = self.select_bounding_boxes_by_frame_number(connection, frame_number)

                width = 800
                height = 600

                image = {
                    'id': image_id,
                    'file_name': frame,
                    'width': width,
                    'height': height,
                    'licence': 1,
                }

                images.append(image)

                for bbox_row in bbox_rows:
                    x_top_left = bbox_row[2]
                    y_top_left = bbox_row[3]
                    x_bottom_right = bbox_row[4]
                    y_bottom_right = bbox_row[5]

                    bbox_width = x_bottom_right - x_top_left
                    bbox_height = y_bottom_right - y_top_left

                    # center_x = (x_top_left + x_bottom_right) / 2
                    # center_y = (y_top_left + y_bottom_right) / 2

                    bbox = [
                        x_top_left,
                        y_top_left,
                        bbox_width,
                        bbox_height
                    ]

                    annotation = {
                        'id': len(annotations) + 1,
                        'image_id': image_id,
                        'category_id': 0,
                        'bbox': bbox,
                        'width': width,
                        'height': height,
                        'area': bbox_width * bbox_height,
                        'iscrowd': 0  # we set this to 0 as this means that no persons are close to each other
                    }

                    annotations.append(annotation)


        json_dict = {
            'info': info,
            'licenses': licenses,
            'categories': categories,
            'images': images,
            'annotations': annotations
        }

        json_data = json.dumps(json_dict)

        with open('val/annotation_coco.json', "w") as json_file:
            json_file.write(json_data)

        json_file.close()