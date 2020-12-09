import os
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import tarfile
import xmltodict
import json
import shutil


class CaviarDatasetConverter:
    def create_test_and_validation_datasets(self, download_files=False, extract_files=False, convert_datasets=False,
                                            frame_jump=19):
        """
        Downloads Caviar datasets, converts them to COCO format, and splits them up into test and validation sets
        """

        annotations_images_pairs = self.__scrape_website()

        download_folder = 'downloads'

        for annotations_images_pair in annotations_images_pairs:
            xml_file_name = annotations_images_pair[0][0]
            xml_file_url = annotations_images_pair[0][1]
            tar_file_name = annotations_images_pair[1][0]
            tar_file_url = annotations_images_pair[1][1]

            if download_files:
                self.__download_file(xml_file_url, xml_file_name, download_folder)
                self.__download_file(tar_file_url, tar_file_name, download_folder)

            # xml file name with out .xml
            xml_file_name_no_ext = xml_file_name[:-4]

            images_destination_folder = download_folder + '/' + xml_file_name_no_ext

            if extract_files:
                self.__extract_compressed_dataset(download_folder, tar_file_name, xml_file_name_no_ext,
                                                  images_destination_folder)

            if convert_datasets:
                self.__covert_dataset(download_folder, xml_file_name_no_ext, frame_jump)

        dataset_names = self.__retrieve_dataset_names(annotations_images_pairs)
        (train_dataset_names, test_dataset_names) = self.__shuffle_and_split_list_of_dataset_names(dataset_names,
                                                                                                   0.7, 0.3)
        self.__concatenate_datasets(download_folder, 'train', train_dataset_names)
        self.__concatenate_datasets(download_folder, 'test', test_dataset_names)

    def __retrieve_dataset_names(self, annotations_images_pairs):
        """
        Retrieves dataset names from list of tuples containing names for xml, tar and url
        Dataset name is the same as the name of the xml file without the .xml extension

        :parameter annotations_images_pairs list of ((xml_file_name, xml_file_url), (tar_file_name, tar_file_url)) tuples
        :returns list of dataset names
        """

        dataset_names = []
        for annotations_images_pair in annotations_images_pairs:
            dataset_names.append((annotations_images_pair[0][0])[:-4])

        return dataset_names

    def __shuffle_and_split_list_of_dataset_names(self, dataset_names, test_set_size, validation_set_size):
        """
        First shuffles the list of annotations in order to randomize the test/validation set split
        Then splits the list of annotations into two lists,
        where 70% of org. list is in first, and the remaining 30% is in the other

        :parameter dataset_names is the list of dataset names
        :returns test_dataset_names, validation_dataset_names lists
        """

        # Test and validation sets must not share data
        if test_set_size + validation_set_size > 1:
            raise Exception('Test size + validation size must not exceed 100% of datasets size')

        shuffled_dataset_names = dataset_names.copy()
        random.shuffle(shuffled_dataset_names)

        number_of_items = len(shuffled_dataset_names)
        number_of_items_in_test_set = int(number_of_items * test_set_size)
        number_of_items_in_val_set = int(number_of_items * validation_set_size)

        test_dataset_names = shuffled_dataset_names[:number_of_items_in_test_set]
        validation_dataset_names = shuffled_dataset_names[-number_of_items_in_val_set:]

        return test_dataset_names, validation_dataset_names

    def __scrape_website(self):
        """
        Get CAVIAR dataset information using web scraping

        :returns [((xml_file_name, xml_file_url), (tar_file_name, tar_file_url))]
        """

        print('Beginning to scrape website')
        # setup
        options = Options()
        options.headless = True

        driver = webdriver.Chrome(options=options, executable_path='./chromedriver.exe')

        # goto web page
        driver.get('http://homepages.inf.ed.ac.uk/rbf/CAVIARDATA1/')

        # get names of files to download
        table_cells = driver.find_elements_by_tag_name('td')

        annotations_images_pairs = []

        for table_cell in table_cells:
            links_inside_cell = table_cell.find_elements_by_tag_name('a')

            if links_inside_cell:
                xml_file_name = ''
                xml_file_url = ''
                tar_file_name = ''
                tar_file_url = ''

                for link in links_inside_cell:
                    file_name = link.text
                    url = link.get_attribute('href')

                    if file_name[-4:] == '.xml':
                        xml_file_name = file_name
                        xml_file_url = url

                    if file_name[-7:] == '.tar.gz':
                        tar_file_name = file_name
                        tar_file_url = url

                annotations_images_pairs.append(((xml_file_name, xml_file_url), (tar_file_name, tar_file_url)))

        return annotations_images_pairs

    def __download_file(self, url: str, file_name: str, destination_folder: str) -> None:
        """
        Downloads a file from specified url to destination folder
        :param url: The URL of the file to download
        :type url: str
        :param file_name: The downloaded file's new name
        :type file_name: str
        :param destination_folder:
        :type destination_folder:
        :rtype: None
        """

        print('Downloading ' + file_name)
        r = requests.get(url, allow_redirects=True)
        open(destination_folder + '/' + file_name, 'wb').write(r.content)

    def __extract_compressed_dataset(self, tar_file_location, tar_file_name, xml_file_name, image_destination_folder):
        """
        Extracts content of tar file into specified folder
        """

        with tarfile.open(tar_file_location + '/' + tar_file_name) as tar:
            # removing the file extension from the folder name
            # we use the xml files name for the folder, as it will make matching of these easier
            print('Extracting ' + tar_file_name)

            if not os.path.isdir(image_destination_folder):
                os.mkdir(image_destination_folder)

            # count number of files in archive to know how much of the file name to cut off
            count = sum(1 for member in tar if member.isreg())
            end_cut_index = -4
            start_cut_index = end_cut_index - len(str(count))

            for member in tar:
                if member.isdir() or member.name[-8:-4] == '.ppm':
                    continue

                folder_file_seperation = member.name.rsplit('/', 1)

                # Case where images are inside folder in tar file
                if len(folder_file_seperation) == 1:
                    original_file_name = member.name.rsplit('/', 1)[0]

                # Case where images are NOT inside folder in tar file
                else:
                    original_file_name = member.name.rsplit('/', 1)[1]

                # use lstrip('0') to remove leading zeroes in order to match frame numbers in XML annotation
                stripped_number = original_file_name[start_cut_index: end_cut_index].lstrip('0')
                number = 1 if stripped_number == '' else int(stripped_number) + 1

                new_file_name = xml_file_name + str(number) + '.jpg'

                tar.makefile(member, image_destination_folder + '/' + new_file_name)

    def __covert_dataset(self, source_directory, xml_file_name, frame_jump):
        """
        Converts a Caviar dataset in XML format into COCO JSON format

        :parameter source_directory: the directory to find the xml file
        :parameter xml_file_name: is only file name, without path and extension
        :parameter frame_jump: the distance between frames to keep. i.e. if frame_jump=10, then every 10 frame is included
        """

        print('Convert dataset "' + xml_file_name + '" to json format')
        with open(source_directory + '/' + xml_file_name + '.xml') as xml_file:
            data_dict = xmltodict.parse(xml_file.read())

        xml_file.close()

        info = {
            'description': "CAVIAR Dataset",
            'url': "http://homepages.inf.ed.ac.uk/rbf/CAVIAR/",
            'version': "1.0.0",
            'year': 2004,
            'contributor': "EC Funded CAVIAR project/IST 2001 37540",
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

        image_id = 0
        remaining_jumps = frame_jump

        for entry in data_dict['dataset']['frame']:
            frame_number = int(entry['@number'])
            file_name = xml_file_name + str(frame_number + 1) + ".jpg"

            if remaining_jumps > 0:
                remaining_jumps = remaining_jumps - 1
                os.remove(source_directory + '/' + xml_file_name + '/' + file_name)
                continue
            else:
                # Increment image_id
                image_id = image_id + 1

                # Reset remaining_jumps (as we are here, we know that we should skip the next frame_jump frames)
                remaining_jumps = frame_jump

            # image_id = frame_number + 1
            width = 384
            height = 288

            image = {
                'id': image_id,
                'file_name': file_name,
                'width': width,
                'height': height,
                'licence': 1,
            }

            images.append(image)

            if entry['objectlist'] is not None:
                objects = entry['objectlist']['object']
                object_list = []
                if isinstance(objects, list):
                    object_list = objects
                else:
                    object_list.append(objects)

                for obj in object_list:
                    bbox_width = float(obj['box']['@w'])
                    bbox_height = float(obj['box']['@h'])

                    bbox_top_left_x = float(obj['box']['@xc']) - (bbox_width / 2)
                    bbox_top_left_y = float(obj['box']['@yc']) - (bbox_height / 2)

                    bbox = [
                        bbox_top_left_x,
                        bbox_top_left_y,
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

        with open(source_directory + '/' + xml_file_name + '.json', "w") as json_file:
            json_file.write(json_data)

        json_file.close()

    def __concatenate_datasets(self, source_folder, new_dataset_name, datasets):
        """
        Concatenates datasets
        """

        print('Beginning to concatenate dataset to create new dataset: ' + new_dataset_name)

        destination_folder = source_folder + '/' + new_dataset_name

        if not os.path.exists(destination_folder):
            os.mkdir(destination_folder)

        # load the first dataset's json file
        resulting_json_file = open(source_folder + '/' + datasets[0] + '.json')
        to_be_resulting_json_data = json.load(resulting_json_file)
        resulting_json_file.close()

        # Initial highest id values
        highest_image_id = len(to_be_resulting_json_data['images'])
        highest_annotation_id = len(to_be_resulting_json_data['annotations'])

        # load rest of dataset's json files one at a time to concat their data with the first dataset
        for dataset in datasets:
            print("Appending dataset " + dataset + " to " + new_dataset_name)

            json_file_dataset = open(source_folder + '/' + dataset + '.json')
            json_data_dataset = json.load(json_file_dataset)

            # Loop through lists to count up ids
            for image in json_data_dataset['images']:
                image_data_copy = image.copy()
                image_data_copy['id'] = image['id'] + highest_image_id

                to_be_resulting_json_data['images'].append(image_data_copy)

            for annotation in json_data_dataset['annotations']:
                annotation_data_copy = annotation.copy()
                annotation_data_copy['id'] = annotation['id'] + highest_annotation_id
                annotation_data_copy['image_id'] = annotation['image_id'] + highest_image_id

                to_be_resulting_json_data['annotations'].append(annotation_data_copy)

            # Update highest id values
            highest_image_id = highest_image_id + len(json_data_dataset['images'])
            highest_annotation_id = highest_annotation_id + len(json_data_dataset['annotations'])

            json_file_dataset.close()

        resulting_json_data = json.dumps(to_be_resulting_json_data)

        with open(destination_folder + '/' + new_dataset_name + '.json', "w") as resulting_json_file:
            resulting_json_file.write(resulting_json_data)

        resulting_json_file.close()

        # copy images from datasets to one shared folder
        for dataset in datasets:
            path = source_folder + '/' + dataset
            only_files = [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]
            print('Copying content of ' + path + ' to ' + destination_folder)
            for file in only_files:
                shutil.copy(path + '/' + file, destination_folder)
