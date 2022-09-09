import json
from pathlib import Path
import shutil
import os.path


class CocoFilter():
    """ Filters the COCO dataset
    """
    def _process_info(self):
        self.info = self.coco['info']
        
    def _process_licenses(self):
        self.licenses = self.coco['licenses']
        
    def _process_categories(self):
        self.categories = dict()
        self.super_categories = dict()
        self.category_set = set()

        for category in self.coco['categories']:
            cat_id = category['id']
            super_category = category['supercategory']
            
            # Add category to categories dict
            if cat_id not in self.categories:
                self.categories[cat_id] = category
                self.category_set.add(category['name'])
            else:
                print(f'ERROR: Skipping duplicate category id: {category}')
            
            # Add category id to the super_categories dict
            if super_category not in self.super_categories:
                self.super_categories[super_category] = {cat_id}
            else:
                self.super_categories[super_category] |= {cat_id} # e.g. {1, 2, 3} |= {4} => {1, 2, 3, 4}

    def _process_images(self):
        self.images = dict()
        for image in self.coco['images']:
            image_id = image['id']
            if image_id not in self.images:
                self.images[image_id] = image
            else:
                print(f'ERROR: Skipping duplicate image id: {image}')
                
    def _process_segmentations(self):
        self.segmentations = dict()
        for segmentation in self.coco['annotations']:
            image_id = segmentation['image_id']
            if image_id not in self.segmentations:
                self.segmentations[image_id] = []
            self.segmentations[image_id].append(segmentation)

    def _filter_categories(self):
        """ Find category ids matching args
            Create mapping from original category id to new category id
            Create new collection of categories
        """
        missing_categories = set(self.filter_categories) - self.category_set    # Count the number of arguments not present in Json
        if len(missing_categories) > 0:
            print(f'Did not find categories: {missing_categories}')
            should_continue = input('Continue? (y/n) ').lower()
            if should_continue != 'y' and should_continue != 'yes':
                print('Quitting early.')
                quit()

        self.new_category_map = dict()
        new_id = 1
        for key, item in self.categories.items():
            if item['name'] in self.filter_categories:
                self.new_category_map[key] = new_id
                new_id += 1

        self.new_categories = []
        for original_cat_id, new_id in self.new_category_map.items():
            new_category = dict(self.categories[original_cat_id])
            new_category['id'] = new_id
            self.new_categories.append(new_category)

    def _filter_no_categories(self):
        """ Find category ids matching args
            Create mapping from original category id to new category id without given arguments
            Create new collection of categories
        """

        self.new_category_map = dict()
        new_id = 1
        for key, item in self.categories.items():
            if item['name'] not in self.filter_no_categories:
                self.new_category_map[key] = new_id
                new_id += 1
            else:
                print('Removing:', item['name'])

        self.new_categories = []
        for original_cat_id, new_id in self.new_category_map.items():
            new_category = dict(self.categories[original_cat_id])
            new_category['id'] = new_id
            self.new_categories.append(new_category)

    def _filter_annotations(self):
        """ Create new collection of annotations matching category ids
            Keep track of image ids matching annotations
        """
        self.new_segmentations = []
        self.new_image_ids = set()
        for image_id, segmentation_list in self.segmentations.items():
            for segmentation in segmentation_list:
                original_seg_cat = segmentation['category_id']
                if original_seg_cat in self.new_category_map.keys():
                    new_segmentation = dict(segmentation)
                    new_segmentation['category_id'] = self.new_category_map[original_seg_cat]
                    self.new_segmentations.append(new_segmentation)
                    self.new_image_ids.add(image_id)


    def _filter_images(self):
        """ Create new collection of images
        """
        self.new_images = []
        for image_id in self.new_image_ids:
            self.new_images.append(self.images[image_id])


    def _filter_removed_images(self):
        self.removed_image_ids = set()
        for image_id, segmentation_list in self.segmentations.items():
            for segmentation in segmentation_list:
                item_cat_id = segmentation["category_id"]
                print("Processing image: ", image_id, "item_category_id in image: ", item_cat_id)
                item_name = self.categories[item_cat_id]["name"]
                if item_name in self.filter_no_categories:
                    self.removed_image_ids.add(image_id)
                    print("Removing image:", image_id, "detected item:", item_name)
        print("Done setting up 'to skipp extraction' images list")


    def _copy_filtered_images(self):
        """ Copy/extract new collection of images into a new folder beside the new json file
        """
        if args.input_images:
            self.image_input_path = Path(args.input_images)
        else:
            print("no input directory given with images. Use --image_input_path <path> to point to the image directory)")
            quit()
        # Verify input images path exists
        if not self.image_input_path.exists():
            print('Input images path not found.')
            print('Quitting early.')
            quit()

        dirpath = os.path.dirname(os.path.abspath(self.output_json_path))
        image_output_path = os.path.join(dirpath, "images")
        print("Copy-extract images to:", image_output_path)

        # Verify output dir does not already exist
        if os.path.exists(image_output_path):
            should_continue = input('Output image folder already exists. Overwrite? (y/n) ').lower()
            if should_continue != 'y' and should_continue != 'yes':
                print('Quitting early.')
                quit()
            else:
                print('deleting old image folder')
                shutil.rmtree(image_output_path)

        print('creating new image folder')
        os.makedirs(image_output_path)

        # Make a list of images to skip (contains items we don't want)
        self._filter_removed_images()

        imagecounter=0
        for image in self.new_images:
            # print(image)
            image_id = image["id"]
            #print("image_id = ", image_id)
            if image_id in self.removed_image_ids:
                print("skipping image", image_id)
            else:
                source_image_path = Path(os.path.join(self.image_input_path, image["file_name"]))
                destination_image_path = Path(os.path.join(image_output_path, image["file_name"]))

                # Verify image does exist
                if source_image_path.exists():
                    pass
                else:
                    should_continue = input('file: ', source_image_path,'missing! This image will be missing if not fixed. Continue? (y/n) ').lower()
                    if should_continue != 'y' and should_continue != 'yes':
                        print("Skipping image that seemed to be missing")
                        continue
                    else:
                        print("quiting copy process")
                        quit()

                imagecounter+=1
                print("copying #", imagecounter, source_image_path, " --> ", destination_image_path)
                shutil.copyfile(source_image_path, destination_image_path)
                if self.number_of_images:
                    if imagecounter >= args.number_of_images:
                        print("user set max number of images reached, stopping extraction of more images.")
                        break
        print('Extracting images done')


    def main(self, args):
        # Open json
        self.input_json_path = Path(args.input_json)
        self.output_json_path = Path(args.output_json)
        self.filter_categories = args.categories
        self.filter_no_categories = args.no_categories
        self.copy_filtered_images = args.copy_filtered_images
        self.number_of_images= args.number_of_images


        # Verify input path exists
        if not self.input_json_path.exists():
            print('Input json path not found.')
            print('Quitting early.')
            quit()

        # Verify output path does not already exist
        if self.output_json_path.exists():
            should_continue = input('Output path already exists. Overwrite? (y/n) ').lower()
            if should_continue != 'y' and should_continue != 'yes':
                print('Quitting early.')
                quit()

        # Verify image path if wanting to extract images
        if self.copy_filtered_images:
            if args.input_images:
                self.image_input_path = Path(args.input_images)
            else:
                print("No input images directory given. Use --image_input_path <path> to point to the image directory")
                quit()

        # Load the json
        print('Loading json file...')
        with open(self.input_json_path) as json_file:
            self.coco = json.load(json_file)
        
        # Process the json
        print('Processing input json...')
        self._process_info()
        self._process_licenses()
        self._process_categories()
        self._process_images()
        self._process_segmentations()

        # Filter to specific categories
        print('Filtering...')
        if self.filter_categories:
            self._filter_categories()

        else:
            pass

        if self.filter_no_categories:
            self._filter_no_categories()
        else:
            pass

        self._filter_annotations()
        self._filter_images()

        # Build new JSON
        new_master_json = {
            'info': self.info,
            'licenses': self.licenses,
            'images': self.new_images,
            'annotations': self.new_segmentations,
            'categories': self.new_categories
        }

        # Write the JSON to a file
        print('Saving new json file...')
        with open(self.output_json_path, 'w+') as output_file:
            json.dump(new_master_json, output_file)

        print('Filtered json saved.')

        # Copy all related images if requested
        if self.copy_filtered_images:
            self._copy_filtered_images()
        else:
            pass

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Filter COCO JSON: "
    "Filters a COCO Instances JSON file to only include specified categories. "
    "This includes images, and annotations. Does not modify 'info' or 'licenses'.")
    
    parser.add_argument("-i", "--input_json", dest="input_json",
        help="path to a json file in coco format")
    parser.add_argument("-o", "--output_json", dest="output_json",
        help="path to save the output json")
    parser.add_argument("-c", "--categories", nargs='+', dest="categories",
        help="List of category names separated by spaces, e.g. -c person dog bicycle")
    parser.add_argument("-nc", "--no_categories", nargs='+', dest="no_categories",
        help="List of category NOT to include names separated by spaces, e.g. -c person dog bicycle")
    parser.add_argument("-cfi", "--copy_filtered_images", action="store_true", dest="copy_filtered_images",
        help="Extract (copy) only images present in new json file to a separate image folder")
    parser.add_argument("-ii", "--input_images", dest="input_images",
        help="path to input_json related image folder")
    """parser.add_argument("-oi", "--output_images", dest="output_images",
        help="path to folder for filtered/extracted images") """
    parser.add_argument("-ni", "--number_of_images", dest="number_of_images", type=int,
        help="number of images wished to copy if not all are wished for.")

    args = parser.parse_args()

    cf = CocoFilter()
    cf.main(args)
