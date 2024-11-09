from test import initialize_model, process_image, process_images_in_directory
import os

initialize_model()

# print(process_image("C:/code/hackaton/test/0012.jpg"))

# print(process_image("C:\\code\\hackaton\\test\\0013.jpg"))

# print(process_image("C:\\code\\hackaton\\test\\1002.jpg"))

process_images_in_directory("C:\\code\\hackaton\\web\\uploaded_images\\test3", "C:\\code\\hackaton\\web\\test.csv")

