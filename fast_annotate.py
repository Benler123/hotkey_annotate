import os
import csv
import json
import argparse
import time
import sys
import vlc
from PyQt5 import QtCore, QtGui, QtWidgets

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
video_done = False
sign_annotations = []
full_annotation = []
attributes = set()
hotkeys = {}
videos_to_be_deleted_set = set()
# invalid_files is currently unused
invalid_files = []
i = 0
current_video = ""
app = None


annotation = ["sign", "filename"]
attribute_index_map = {}
    
class Player(QtWidgets.QMainWindow):
    def __init__(self, parent=None, annotations=None, directory=None, signs=None, hkeys=None, output=None):
        global hotkey_info
        global video_done
        global annotation
        global attribute_index_map
        global sign_annotations
        global full_annotation
        global attributes
        global hotkeys
        global invalid_files
        global i
        global current_video

        self.directory = directory
        self.signs = signs
        hotkeys = hkeys
        self.output = output

        attribute_index_map = {}
        for i, key in enumerate(hotkeys.keys()):
            attribute_index_map[hotkeys[key]] = i
            hotkey_info = hotkey_info + " {} : {} \n".format(key, hotkeys[key])
        
        super(Player, self).__init__(parent)
        self.setWindowTitle("Media Player")
        # creating a basic vlc instance
        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()
        # video frame
        self.videoframe = QtWidgets.QFrame(
            frameShape=QtWidgets.QFrame.Box, frameShadow=QtWidgets.QFrame.Raised
        )

        if sys.platform.startswith("linux"):  # for Linux using the X Server
            self.mediaplayer.set_xwindow(self.videoframe.winId())
        elif sys.platform == "win32":  # for Windows
            self.mediaplayer.set_hwnd(self.videoframe.winId())
        elif sys.platform == "darwin":  # for MacOS
            self.mediaplayer.set_nsobject(int(self.videoframe.winId()))

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        lay = QtWidgets.QVBoxLayout(central_widget)
        lay.addWidget(self.videoframe)

        self.text_label = QtWidgets.QLabel()
        self.text_label.setText("Current sign:")
        self.text_label.setFixedHeight(20)
        lay.addWidget(self.text_label)

        self.tutorial_info = QtWidgets.QLabel()
        self.tutorial_info.setText("Press Attribute Keys to Add/Remove,(" + BACK_KEY + ") to go back (" + REPLAY_KEY + ") to Replay, or (" + NEXT_KEY + ") to Proceed to Next Video")
        self.tutorial_info.setFixedHeight(40)
        lay.addWidget(self.tutorial_info)
        
        self.annotation_info = QtWidgets.QLabel()
        self.annotation_info.setText("Annotation mapping: " + str(hotkeys))
        self.annotation_info.setFixedHeight(20)
        lay.addWidget(self.annotation_info)

        self.sign_number = 0
        self.i = 0


        self.videos_to_be_deleted_txt = open("Videos_To_Be_Deleted.txt", 'a')

        self.annotations_csv = open(output, 'a')
        self.csv_writer = csv.writer(self.annotations_csv)
        
        # sign and filename are the first 2 in any of the headers
        annotation = ["sign", "filename"]
        annotation.extend(hotkeys.values())
        # Writes a header before each sign
        self.csv_writer.writerow(annotation)
        self.annotations_csv.flush()
        
        self.recording_annotation = ["" for i in range(len(hotkeys))]
        # 2d array that stores a sign's annotation so that it can all be written at once.
        sign_annotations = []
        # Track the invalid files so that if we traverse i backwards, it skips over them
        invalid_files = set()
        
        sign_directory_path = os.path.join(self.directory, self.signs[self.sign_number])
        self.videos = os.listdir(sign_directory_path)
        self.videos.sort()

        self.playFullVideo()

    def add_video_to_be_deleted_txt(self):
        for video in videos_to_be_deleted_set:
            self.videos_to_be_deleted_txt.write(video + "\n")
        videos_to_be_deleted_set.clear()

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        self.process_key(a0.text())
        return super().keyPressEvent(a0)

    def playFullVideo(self):
        global current_video
        if self.i == len(self.videos):
            self.text_label.setText("You have just finished the last sign. Press '=' to go to the next sign or " + BACK_KEY + " to return")
            return
        self.sign_directory_path = os.path.join(self.directory, self.signs[self.sign_number])
        self.videos = os.listdir(self.sign_directory_path)
        self.videos.sort()
        self.text_label.setText(f"Current sign: {self.signs[self.sign_number]}. Current Attributes Are " + (str(attributes) if len(attributes) != 0 else ""))
        current_video = self.videos[self.i]
        print(current_video)
        self.playVideo(os.path.join(self.sign_directory_path, self.videos[self.i]))

    def playVideo(self, filename):
        media = self.instance.media_new(filename)
        self.mediaplayer.set_media(media)
        self.mediaplayer.set_rate(2)
        self.mediaplayer.play()

    def process_key(self, key):
        global hotkey_info
        global video_done
        global annotation
        global attribute_index_map
        global sign_annotations
        global full_annotation
        global attributes
        global hotkeys
        global invalid_files
        global current_video
        global app
        if key in hotkeys:
            if (hotkeys[key] == "Video To Be Deleted"):
                if(current_video in videos_to_be_deleted_set):
                    videos_to_be_deleted_set.remove(current_video)
                else:
                    videos_to_be_deleted_set.add(current_video)
            if (self.recording_annotation[attribute_index_map[hotkeys[key]]] == ""):
                self.recording_annotation[attribute_index_map[hotkeys[key]]] = 'x'
                attributes.add(hotkeys[key])
            else:
                self.recording_annotation[attribute_index_map[hotkeys[key]]] = ""
                attributes.remove(hotkeys[key])

            self.text_label.setText(f"Current sign: {self.signs[self.sign_number]}. Current Attributes Are " + (str(attributes) if len(attributes) != 0 else ""))
        elif key == NEXT_KEY:
            if self.i == len(self.videos):
                sign = self.signs[self.sign_number]
                sign_annotations.sort()
                self.csv_writer.writerows(sign_annotations)
                self.annotations_csv.flush()
                self.add_video_to_be_deleted_txt()
                self.sign_number += 1
                self.i = 0
                if self.sign_number == len(self.signs):
                    done = QtWidgets.QMessageBox()
                    done.setWindowTitle("Annotations complete")
                    done.setText("All requested videos have now been annotated. You can view your annotations in annotations.csv.")
                    done.exec_()
                    app.quit()
                    return
                # sign and filename are the first 2 in any of the headers
                annotation = ["sign", "filename"]
                annotation.extend(hotkeys.values())
                # Writes a header before each sign
                self.csv_writer.writerow(annotation)
                self.annotations_csv.flush()
                self.add_video_to_be_deleted_txt()
                # 2d array that stores a sign's annotation so that it can all be written at once.
                sign_annotations = []
            full_annotation = [self.signs[self.sign_number], self.videos[self.i]]
            full_annotation.extend(self.recording_annotation)
            if (self.i - len(invalid_files) == len(sign_annotations)):
                sign_annotations.append(full_annotation)
            elif ((annotation) != [""] * len(hotkeys)):
                sign_annotations[self.i - len(invalid_files)] = full_annotation
            # switch to next video
            self.i += 1
            self.recording_annotation = ["" for i in range(len(hotkeys))]
            attributes = set()
            self.text_label.setText(f"Current sign: {self.signs[self.sign_number]}. Current Attributes Are " + (str(attributes) if len(attributes) != 0 else ""))
            self.playFullVideo()
        elif key == REPLAY_KEY:
            video_done = True
            self.playFullVideo()
        elif key == BACK_KEY:
            if (self.i < len(self.videos)):
                full_annotation = [self.signs[self.sign_number], self.videos[self.i]]
                full_annotation.extend(annotation)
                if (self.i - len(invalid_files) == len(sign_annotations)):
                    sign_annotations.append(full_annotation)
                elif ((annotation) != [""] * len(hotkeys)):
                    sign_annotations[self.i - len(invalid_files)] = full_annotation
            if (self.i >= 1 + len(invalid_files)):
                self.i -= 1
                self.playFullVideo()
            self.recording_annotation = ["" for i in range(len(hotkeys))]
            video_done = True
            attributes = set()
            self.text_label.setText(f"Current sign: {self.signs[self.sign_number]}. Current Attributes Are " + (str(attributes) if len(attributes) != 0 else ""))
        elif (key == '`'):
            done = QtWidgets.QMessageBox()
            done.setWindowTitle("Annotations complete")
            done.setText("All requested videos have now been annotated. You can view your annotations in annotations.csv.")
            done.exec_()
            app.quit()
            return
        return self.i



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
    # fast_annotate(arguments.directory, arguments.signs, hotkeys, arguments.output)

    app = QtWidgets.QApplication(sys.argv)
    player = Player(directory=arguments.directory, signs=arguments.signs, hkeys=hotkeys, output=arguments.output)
    player.show()
    player.resize(640, 480)
    sys.exit(app.exec_())

