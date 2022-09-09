# COCO Manager
This repo will include various Python scripts to manage COCO datasets.

For now, the following functionality is available and applies to the Object Detection annotation format. Learn more here: http://cocodataset.org/#format-data

## Filter
filter.py allows you to filter an existing COCO Instances JSON file by categories.

The following command will filter the input instances json to only include images and annotations for the categories person, dog, or cat:
```python filter.py --input_json c:\users\you\annotations\instances_train2017.json --output_json c:\users\you\annotations\filtered.json --categories person dog cat```

Note: This isn't looking for images with all categories in one. It includes images that have at least one of the specified categories.

Other function : 

--no_categories person dog cat      --> [ 
Only eliminates these categories from the output_json.]

--copy_filtered_images  --> Extract (copy) only images present in new json file to a separate image folder

--input_images  --> path to folder for filtered/extracted images

-- n

# Example Commands : 
```python3 filter.py --input_json /mnt/d/DeepLearning/MSCOCO/annotations_trainval2017/annotations/instances_val2017.json --output_json /mnt/d/DeepLearning/MSCOCO/SOS5backgrounds/test.json --no_categories person -cfi -ii /mnt/d/DeepLearning/MSCOCO/val2017 -ni 10```

This wil make a json file without any "person" annotations and will also make a new "image" folder beside the new json file containing only images without the class "pesons". The number of images to copy is set to 10. This can be handy to quickly evaluate if classes are indeed removed without copying all images.




# Immersive Limit Resources
For more helpful resources, please check out https://www.immersivelimit.com/tutorials.