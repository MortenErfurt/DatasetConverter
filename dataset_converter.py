import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import tarfile
import xmltodict
import json

class DatasetConverter:
    # TODO: Field variables..
    def get_datasets(self):
        annotations_images_pairs = self.__scrape_website()

        download_folder = 'downloads'

        for annotations_images_pair in annotations_images_pairs:
            xml_file_name = annotations_images_pair[0][0]
            xml_file_url = annotations_images_pair[0][1]
            tar_file_name = annotations_images_pair[1][0]
            tar_file_url = annotations_images_pair[1][1]

            self.__download_file(xml_file_url, xml_file_name, download_folder)
            self.__download_file(tar_file_url, tar_file_name, download_folder)

            images_destination_folder = download_folder + '/' + xml_file_name[:-4]
            self.__extract_compressed_dataset(download_folder, tar_file_name, images_destination_folder)


    """
    Private method for getting CAVIAR dataset information using web scraping
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


    def __download_file(self, url, file_name, destination_folder):
        print('Downloading ' + file_name)
        r = requests.get(url, allow_redirects=True)
        open(destination_folder + '/' + file_name, 'wb').write(r.content)


    def __extract_compressed_dataset(self, tar_file_location, tar_file_name, image_destination_folder):
        print('Extracting compressed datasets')
        with tarfile.open(tar_file_location) as tar:
            # removing the file extension from the folder name
            # we use the xml files name for the folder, as it will make matching of these easier
            print('Processing compressed file: ' + tar_file_name)
            os.mkdir(image_destination_folder)
            for member in tar:
                if member.isdir():
                    continue
                file_name = member.name.rsplit('/', 1)[1]
                tar.makefile(member, image_destination_folder + '/' + file_name)


    """
    :param xml_file_name is only file name, without path and extension
    """
    def __covert_dataset(self, source_directory, image_name_prefix, xml_file_name, json_file_name):
        print('Beginning to convert dataset')
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
            file_name = image_name_prefix + str(1000 + frame_number) + ".jpg"
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


    def concatenate_datasets(self, source_folder, destination_folder, datasets):
        if not os.path.exists(destination_folder):
            os.mkdir(destination_folder)

        # datasets is just a list of strings
        # hence dataset is a string
        # for dataset in datasets:
        #     if os.path.exists(dataset):
        #         for file_name in os.scandir(dataset):
                    # file_name.name[:-8]
