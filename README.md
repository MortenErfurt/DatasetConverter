# Implementation of dataset converter

This repo contains a webscraper, downloader and a converter for the CAVIAR dataset, and converter for the Atrium dataset.

The CAVIAR dataset can be found at: https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA1/

The Atrium dataset can be found at: https://www.jpjodoin.com/urbantracker/dataset.html

Both converters converts annotations into COCO JSON annotations.

The caviar_dataset_converter.py is also able to divide the dataset up in to two parts, for e.g. training and testing.

The atrium_dataset_converter.py expects Atrium frames and annotations to be in the same folder as this project. They should be in respectively "atrium_frames" and "atrium_annotations" folders, which is the case if you just download and unzip the two zip files at https://www.jpjodoin.com/urbantracker/dataset/atrium/atrium_frames.zip and https://www.jpjodoin.com/urbantracker/dataset/atrium/atrium_annotations.zip.

Thus it is only for the atrium dataset converter, that data needs to be downloaded in advance. For the CAVIAR dataset converter this is done automatically. However the CAVIAR dataset converter needs a Chrome webdriver, in order to scrape the website. This can be found at: https://chromedriver.chromium.org/downloads. You need to download the one matching your Chrome browsers version.

To try them out, you can run the test.py file, which then converts both datasets.

## Authors:
[Johannes Ernstsen](https://github.com/Ernstsen), [Morten Hansen](https://github.com/MortenErfurt) & [Mathias Jensen](https://github.com/m-atlantis)
