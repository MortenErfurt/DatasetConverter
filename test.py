import caviar_dataset_converter
import atrium_dataset_converter

# converter = caviar_dataset_converter.CaviarDatasetConverter()
# converter.create_test_and_validation_datasets()

atrium_conver = atrium_dataset_converter.AtriumDatasetConverter()
atrium_conver.convert_dataset(19)