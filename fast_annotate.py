import cv2
import os
import csv
import json
import argparse


'''
TODO
Make it so you can start where you left off
'''

def add_or_remove_attribute(key, annotation, attribute_index_map, attributes, hotkeys):
    if key in hotkeys:
        if (annotation[attribute_index_map[hotkeys[key]]] == ""):
            annotation[attribute_index_map[hotkeys[key]]] = 'x'
            attributes.add(hotkeys[key])
            print("--------------\n"
                  "ADDING " + hotkeys[key] +
                  "\n--------------")
        else:
            annotation[attribute_index_map[hotkeys[key]]] = ""
            attributes.remove(hotkeys[key])
            print("--------------\n"
                  "REMOVING " + hotkeys[key] +
                  "\n--------------")

def fast_annotate(directory, signs, hotkeys, output):
    # Tracks what row is currently  being annotated
    attribute_index_map = {}
    for i, value in enumerate(hotkeys.values()):
        attribute_index_map[value] = i
    with open(output, 'a') as annotations_csv:
        csv_writer = csv.writer(annotations_csv)
        for sign_number, sign in enumerate(signs):
            print("%%%%%%%%%%%%%%\n"
                  "ANNOTATING " + str(sign) +
                  "\n%%%%%%%%%%%%%%")
            # sign and filename are the first 2 in any of the headers
            annotation = ["sign", "filename"]
            annotation.extend(hotkeys.values())
            # Writes a header before each sign
            csv_writer.writerow(annotation)
            sign_directory_path = os.path.join(directory, sign)
            videos = os.listdir(sign_directory_path)
            videos.sort()
            i = 0
            # Traverses through each video in the directory
            while(i < len(videos)):
                # First element in annotation row is the video name
                full_annotation = [sign, videos[i]]
                # stores the full path of the current video
                current_video = os.path.join(sign_directory_path, videos[i])
                print("--------------\n"
                    + "VIDEO: " + videos[i] +
                      "\n--------------")
                if (current_video[-3:] != "mp4"):
                    print("--------------\n"
                          "SKIPPING" + current_video + " INVALID FILE TYPE" +
                          "\n--------------")
                    i = i + 1
                    continue
                cap = cv2.VideoCapture(current_video)
                # Case when video file cannot be read
                annotation = [""] * len(hotkeys)
                # Set that stores the current attributes for the video
                attributes = set()
                if not cap.isOpened():
                    print("--------------\n"
                          "VIDEO DID NOT OPEN. WRITING Video Doesn't Play" +
                          "\n--------------")
                    annotation[attribute_index_map["Video Doesn't Play"]] = 'x'
                    full_annotation.extend(annotation)
                    csv_writer.writerow(full_annotation)
                    i = i + 1
                else:
                    while(cap.isOpened()):
                        ret, frame = cap.read()
                        if ret == True:
                            # Display Resulting frame
                            cv2.imshow('Frame', frame)
                            key = chr(cv2.waitKey(1) & 0xFF)
                            add_or_remove_attribute(key, annotation, attribute_index_map, attributes, hotkeys)
                        else:
                            key = None
                            while  key != '-' and key != '=':
                                print("Current Attributes Are " + (str(attributes) if len(attributes) != 0 else ""))
                                print("Press Corresponding Attribute Keys to Add/Remove, (-) to Replay, or (=) to Proceed to Next Video")
                                key = chr(cv2.waitKey(0) & 0xFF)
                                if(key == '=') :
                                    full_annotation.extend(annotation)
                                    csv_writer.writerow(full_annotation)
                                    i = i + 1
                                if(key == '`'):
                                    print("--------------\n"
                                          "QUITTING" +
                                          "\n--------------")
                                    exit()
                                else:
                                    add_or_remove_attribute(key, annotation, attribute_index_map, attributes, hotkeys)
                            break
        print("--------------\n\n"
              + str(signs) + "Have been annotated and written"
              "\n\n--------------")




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pass in directories to annotate')
    # takes a path to the directory
    parser.add_argument('-d', '--directory', required=True)
    # CSV file that annotations will be output to
    parser.add_argument('-o', '--output', default="annotations.csv")
    # takes a list of 1 or more signs to annotate
    parser.add_argument('-s', '--signs', nargs='+', required=True)

    arguments = parser.parse_args()
    # Make a hotkey dict using the json file
    file = open("hotkeys.json")
    hotkeys = json.load(file)
    file.close()
    fast_annotate(arguments.directory, arguments.signs, hotkeys, arguments.output)




