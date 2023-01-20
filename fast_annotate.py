import cv2
import os
import csv
import json
import argparse


'''
TODO
Make it so you can start where you left off
Make it so the hotkeys can't be setkeys
Make it so two hotkeys can't be the same 
'''

# Once the csv is written to, it is very hard to overwrite
# unless you read in the entire csv file and create a new temporary one every time.
# This seems wildly inefficient.
# Instead since it seems  very difficult to allow users to start where they left off, we can make it so the program
# only writes when all videos for a sign are finished. In the future, once I figure out how to allow users to start
# where they left off, using the exit key can write what is currently being saved.

BACK_KEY = "0"
REPLAY_KEY = "-"
NEXT_KEY = "="
DISPLAY_INFO = "9"
hotkey_info = "Hotkey Info \n"

def process_key(key, annotation, attribute_index_map, sign_annotations, full_annotation, attributes, hotkeys, invalid_files, cap, i, current_video):
    if key in hotkeys:
        if (annotation[attribute_index_map[hotkeys[key]]] == ""):
            annotation[attribute_index_map[hotkeys[key]]] = 'x'
            attributes.add(hotkeys[key])
            print("ADDING " + hotkeys[key])

        else:
            annotation[attribute_index_map[hotkeys[key]]] = ""
            attributes.remove(hotkeys[key])
            print("REMOVING " + hotkeys[key])
    elif key == NEXT_KEY:
        full_annotation.extend(annotation)
        # Check if we are on a new line. If not we are setting in the array

        if (i - len(invalid_files) == len(sign_annotations)):
            sign_annotations.append(full_annotation)
            print("Appending " + current_video + " With Attributes " + str(attributes))
        elif ((annotation) != [""] * len(hotkeys)):
            print("Changing " + current_video + " To " + str(attributes))
            sign_annotations[i - len(invalid_files)] = full_annotation
        i = i + 1
    elif key == REPLAY_KEY:
        cap.release()
    elif key == BACK_KEY:
        full_annotation.extend(annotation)
        if (i - len(invalid_files) == len(sign_annotations)):
            sign_annotations.append(full_annotation)
            print("Appending " + current_video + " With Attributes " + str(attributes))
        elif ((annotation) != [""] * len(hotkeys)):
            print("Changing " + current_video + " To " + str(attributes))
            sign_annotations[i - len(invalid_files)] = full_annotation
        if (i >= 1 + len(invalid_files)):
            i = i - 1
        else:
            print("AT FIRST FILE")
        cap.release()
    elif (key == '9'):
        print(hotkey_info)
    elif (key == '`'):
        print(
            "QUITTING" +
            "\n--------------")
        '''
        Make it so quitting writes what is currently in sign_annotations.
        '''
        exit()
    return i
def fast_annotate(directory, signs, hotkeys, output):
    # Tracks what row is currently  being annotated
    global hotkey_info
    attribute_index_map = {}
    for i, key in enumerate(hotkeys.keys()):
        attribute_index_map[hotkeys[key]] = i
        hotkey_info = hotkey_info + " {} : {} \n".format(key, hotkeys[key])

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
            # 2d array that stores a sign's annotation so that it can all be written at once.
            sign_annotations = []
            # Track the invalid files so that if we traverse i backwards, it skips over them
            invalid_files = set()
            #This is a really bandaid solution. Needs to be fixed in the future
            bad_videos_annotations = []
            bad_videos_indexes = set()
            i = 0
            # Traverses through each video in the directory
            while(i <= len(videos)):
                if (i == len(videos)):
                    print(
                        "You have just finished the last sign. Press any key to go to the next sign or " + BACK_KEY + " to return")
                    key = chr(cv2.waitKey(0) & 0xFF)
                    if (key == BACK_KEY):
                        i = i - 1
                    else:
                        i = i + 1
                        continue
                # First element in annotation row is the video name
                full_annotation = [sign, videos[i]]
                # stores the full path of the current video
                current_video = os.path.join(sign_directory_path, videos[i])
                if (i in invalid_files):
                    print("SKIPPING " + current_video + " INVALID FILE")
                    invalid_files.remove(i)
                    i = i - 1
                    continue
                print("--------------\n"
                    + "VIDEO: " + videos[i])
                if (current_video[-3:] != "mp4"):
                    print(
                          "SKIPPING" + current_video + " INVALID FILE TYPE" +
                          "\n--------------")
                    invalid_files.add(i)
                    i = i + 1
                    continue
                cap = cv2.VideoCapture(current_video)
                # Case when video file cannot be read
                annotation = [""] * len(hotkeys)
                # Set that stores the current attributes for the video
                attributes = set()
                if not cap.isOpened():
                    print(
                          "VIDEO DID NOT OPEN. WRITING Video Doesn't Play" +
                          "\n--------------")

                    annotation[attribute_index_map["Video Doesn't Play"]] = 'x'
                    full_annotation.extend(annotation)
                    if i not in bad_videos_indexes:
                        bad_videos_annotations.append(full_annotation)
                        bad_videos_indexes.add(i)
                    invalid_files.add(i)
                    i = i + 1
                    continue
                else:
                    while(cap.isOpened()):
                        ret, frame = cap.read()
                        if ret == True:
                            # Display Resulting frame
                            cv2.imshow('Frame', frame)
                            key = chr(cv2.waitKey(1) & 0xFF)
                            i = process_key(key, annotation, attribute_index_map, sign_annotations, full_annotation, attributes, hotkeys, invalid_files, cap, i, current_video)
                            if(key == BACK_KEY or key == NEXT_KEY or key == REPLAY_KEY):
                                cap.release()
                        else:
                            key = None
                            while key != BACK_KEY and key != NEXT_KEY and key != REPLAY_KEY:
                                print("Current Attributes Are " + (str(attributes) if len(attributes) != 0 else ""))
                                print("Press Attribute Keys to Add/Remove,(" + BACK_KEY + ") to go back (" + REPLAY_KEY + ") to Replay, or (" + NEXT_KEY + ") to Proceed to Next Video")
                                key = chr(cv2.waitKey(0) & 0xFF)
                                i = process_key(key, annotation, attribute_index_map, sign_annotations, full_annotation,
                                                attributes, hotkeys, invalid_files, cap, i, current_video)
                            break

            print("Finished sign {" + sign + "} writing annotations" + "\n--------------")
            sign_annotations.extend(bad_videos_annotations)
            sign_annotations.sort()
            csv_writer.writerows(sign_annotations)
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
    for key in hotkeys.keys():
        if(key == BACK_KEY or key == NEXT_KEY or key == REPLAY_KEY or key == DISPLAY_INFO):
            raise ValueError("Hotkeys cannot be the same as navigation keys")
    fast_annotate(arguments.directory, arguments.signs, hotkeys, arguments.output)




