import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import tarfile


def run():
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

    # TODO: move to separate method
    # download the files
    for annotations_images_pair in annotations_images_pairs:
        xml_file_name = annotations_images_pair[0][0]
        xml_file_url = annotations_images_pair[0][1]
        tar_file_name = annotations_images_pair[1][0]
        tar_file_url = annotations_images_pair[1][1]

        # download xml file
        print('Downloading ' + xml_file_name)
        r = requests.get(xml_file_url, allow_redirects=True)
        open('downloads/' + xml_file_name, 'wb').write(r.content)

        # download tar file
        print('Downloading ' + tar_file_name)
        r = requests.get(tar_file_url, allow_redirects=True)
        tar_file_location = 'downloads/' + tar_file_name
        open(tar_file_location, 'wb').write(r.content)

        # TODO: move to separate method
        with tarfile.open(tar_file_location) as tar:
            # removing the file extension from the folder name
            # we use the xml files name for the folder, as it will make matching of these easier
            destination_folder = 'downloads/' + xml_file_name[:-4]
            print('Processing compressed file: ' + tar_file_name)
            os.mkdir(destination_folder)
            for member in tar:
                if member.isdir():
                    continue
                file_name = member.name.rsplit('/', 1)[1]
                tar.makefile(member, destination_folder + '/' + file_name)


run()
