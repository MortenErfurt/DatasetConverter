import os
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import tarfile
import xmltodict
import json
import shutil


class DatasetConverter:
    """
    Downloads Caviar datasets, converts them to COCO format, and splits them up into test and validation sets
    """

    def create_test_and_validation_datasets(self, download_files=False):
        annotations_images_pairs = self.__scrape_website()

        download_folder = 'downloads'

        # for annotations_images_pair in annotations_images_pairs:
        #     xml_file_name = annotations_images_pair[0][0]
        #     xml_file_url = annotations_images_pair[0][1]
        #     tar_file_name = annotations_images_pair[1][0]
        #     tar_file_url = annotations_images_pair[1][1]
        #
        #     if download_files:
        #         self.__download_file(xml_file_url, xml_file_name, download_folder)
        #         self.__download_file(tar_file_url, tar_file_name, download_folder)
        #
        #     # xml file name with out .xml
        #     xml_file_name_no_ext = xml_file_name[:-4]
        #
        #     images_destination_folder = download_folder + '/' + xml_file_name_no_ext
        #     self.__extract_compressed_dataset(download_folder, tar_file_name, xml_file_name_no_ext,
        #                                       images_destination_folder)
        #
        #     self.__covert_dataset(download_folder, xml_file_name_no_ext)

        dataset_names = self.__retrieve_dataset_names(annotations_images_pairs)
        (test_dataset_names, validation_dataset_names) = self.__shuffle_and_split_list_of_dataset_names(dataset_names)
        self.__concatenate_datasets(download_folder, 'test', test_dataset_names)
        # self.__concatenate_datasets(download_folder, 'validation', validation_dataset_names)

    """
    Retrieves dataset names from list of tuples containing names for xml, tar and url
    Dataset name is the same as the name of the xml file without the .xml extension
    
    :parameter annotations_images_pairs list of ((xml_file_name, xml_file_url), (tar_file_name, tar_file_url)) tuples
    :returns list of dataset names
    """

    def __retrieve_dataset_names(self, annotations_images_pairs):
        dataset_names = []
        for annotations_images_pair in annotations_images_pairs:
            dataset_names.append((annotations_images_pair[0][0])[:-4])

        return dataset_names

    """
    First shuffles the list of annotations in order to randomize the test/validation set split
    Then splits the list of annotations into two lists, 
    where 70% of org. list is in first, and the remaining 30% is in the other
    
    :parameter dataset_names is the list of dataset names
    :returns test_dataset_names, validation_dataset_names lists
    """

    def __shuffle_and_split_list_of_dataset_names(self, dataset_names):
        shuffled_dataset_names = dataset_names.copy()
        random.shuffle(shuffled_dataset_names)

        number_of_items = len(shuffled_dataset_names)
        number_of_items_in_test_set = int(number_of_items * 0.7)
        number_of_items_in_val_set = number_of_items - number_of_items_in_test_set

        test_dataset_names = shuffled_dataset_names[:number_of_items_in_test_set]
        validation_dataset_names = shuffled_dataset_names[-number_of_items_in_val_set:]

        return test_dataset_names, validation_dataset_names

    """
    Get CAVIAR dataset information using web scraping
    
    :returns [((xml_file_name, xml_file_url), (tar_file_name, tar_file_url))]
    """

    def __scrape_website(self):
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

    """
    Downloads a file from specified url to destination folder
    """

    def __download_file(self, url, file_name, destination_folder):
        print('Downloading ' + file_name)
        r = requests.get(url, allow_redirects=True)
        open(destination_folder + '/' + file_name, 'wb').write(r.content)

    """
    Extracts content of tar file into specified folder
    """

    def __extract_compressed_dataset(self, tar_file_location, tar_file_name, xml_file_name, image_destination_folder):
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

    """
    Converts a Caviar dataset in XML format into COCO JSON format
    
    :parameter xml_file_name is only file name, without path and extension
    """

    def __covert_dataset(self, source_directory, xml_file_name):
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
        empty_images = []
        person_images = []

        licenses.append({
            'url': "http://creativecommons.org/licenses/by-nc-sa/2.0/",
            'id': 1,
            'name': "Attribution-NonCommercial-ShareAlike License"
        })

        categories.append({
            'id': 1,
            'name': "pedestrain",  # Misspelled on purpose
            'supercategory': "pedestrain"
        })

        for entry in data_dict['dataset']['frame']:
            frame_number = int(entry['@number'])
            image_id = frame_number + 1
            file_name = xml_file_name + str(frame_number + 1) + ".jpg"
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
                    bbox_width = float(obj['box']['@w'])
                    bbox_height = float(obj['box']['@h'])

                    bbox = [
                        float(obj['box']['@xc']),
                        float(obj['box']['@yc']),
                        bbox_width,
                        bbox_height
                    ]

                    annotation = {
                        'id': len(annotations) + 1,
                        'image_id': image_id,
                        'category_id': 1,
                        'iscrowd': 1 if (len(objects) > 1) else 0,
                        'bbox': bbox,
                        'width': width,
                        'height': height,
                        'segmentation': [],
                        'area': bbox_width * bbox_height
                    }

                    annotations.append(annotation)

        json_dict = {
            'info': info,
            'licenses': licenses,
            'categories': categories,
            'images': images,
            'annotations': annotations,
            'empty_images': empty_images,
            'person_images': person_images
        }

        json_data = json.dumps(json_dict)

        with open(source_directory + '/' + xml_file_name + '.json', "w") as json_file:
            json_file.write(json_data)

        json_file.close()

    """
    Concatenates datasets
    """

    def __concatenate_datasets(self, source_folder, new_dataset_name, datasets):
        print('Beginning to concatenate dataset to create new dataset: ' + new_dataset_name)

        destination_folder = source_folder + '/' + new_dataset_name

        if not os.path.exists(destination_folder):
            os.mkdir(destination_folder)

        # load the first dataset's json file
        json_file = open(source_folder + '/' + datasets[0] + '.json')
        json_data = json.load(json_file)
        highest_image_id = json_data['images'][-1:][0]['id']

        # copy images from datasets to one shared folder
        for dataset in datasets:
            path = source_folder + '/' + dataset
            only_files = [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]
            print('Copying content of ' + path + ' to ' + destination_folder)
            for file in only_files:
                shutil.copy(path + '/' + file, destination_folder)
