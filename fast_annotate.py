import os
import csv
import json
import argparse
import datetime
import sys
import vlc
from pathlib import Path
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
SPEED_UP_KEY = "]"
SLOW_DOWN_KEY = "["
DISPLAY_INFO = "9"
hotkey_info = "Hotkey Info \n"
video_done = False
sign_annotations = []
full_annotation = []
attributes = set()
hotkeys = {}
reject_re_set = set()
i = 0
current_video = ""
app = None

attribute_index_map = {}
    
class Player(QtWidgets.QMainWindow):
    def __init__(self, parent=None, annotations=None, directory=None, sign=None, hkeys=None, output_src=None, reject_path="", annotate_path=""):
        global hotkey_info
        global video_done
        global attribute_index_map
        global sign_annotations
        global full_annotation
        global attributes
        global hotkeys
        global i
        global current_video

        self.directory = directory
        hotkeys = hkeys

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
        self.tutorial_info.setText(f'Press Attribute Keys to Add/Remove, ({SPEED_UP_KEY}) to Speed Up the Video, ({SLOW_DOWN_KEY}) to Slow Down the Video, (' + BACK_KEY + ") to go back, (" + REPLAY_KEY + ") to Replay, or (" + NEXT_KEY + ") to Proceed to Next Video")
        self.tutorial_info.setFixedHeight(20)
        lay.addWidget(self.tutorial_info)
        
        self.annotation_info = QtWidgets.QLabel()
        self.annotation_info.setText("Annotation mapping: " + str(hotkeys))
        self.annotation_info.setFixedHeight(20)
        lay.addWidget(self.annotation_info)

        self.playback_speed = 1.

        self.i = 0

        self.hotkey_keys = list(hotkeys.keys())
        
        self.recording_annotation = ["" for i in range(len(hotkeys))]
        # 2d array that stores a sign's annotation so that it can all be written at once.
        sign_annotations = []

        self.sign = sign
        
        self.sign_directory_path = os.path.join(self.directory, sign)

        self.videos = os.listdir(self.sign_directory_path)
        self.videos.sort()

        output_path = os.path.join(output_src, sign)
        Path(output_path).mkdir(parents=True, exist_ok=True)

        reject_re_path = os.path.join(output_path, "REJECT_RE.txt")
        self.reject_re = open(reject_re_path, 'a')
        self.reject_re.write(f"Session at time {str(datetime.datetime.now())}: \n")

        annotations_csv_path = os.path.join(output_path, "annotations.csv")
        self.annotations_csv = open(annotations_csv_path, 'a')
        self.csv_writer = csv.writer(self.annotations_csv)
        
        # sign and filename are the first 2 in any of the headers
        annotation_header = ["sign", "filename"]
        annotation_header.extend(hotkeys.values())
        # Writes a header before each sign
        self.csv_writer.writerow(annotation_header)
        self.annotations_csv.flush()

        self.playFullVideo()

    def add_video_to_be_deleted_txt(self):
        for video in reject_re_set:
            self.reject_re.write(video + "\n")
        reject_re_set.clear()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.playFullVideo()
        return super().resizeEvent(a0)
    
    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.isAutoRepeat():
            return
        self.process_key(a0.text())
        return super().keyPressEvent(a0)

    def playFullVideo(self):
        global current_video
        self.text_label.setText(f"Current Attributes Are " + (str(attributes) if len(attributes) != 0 else ""))
        current_video = self.videos[self.i]
        print(current_video)
        if self.i % 20 == 19:
            self.tutorial_info.setText(f"You are at a save checkpoint. Press '=' to save current annotations, {BACK_KEY} to return, ({SPEED_UP_KEY}) to Speed Up the Video, ({SLOW_DOWN_KEY}) to Slow Down the Video, or ({REPLAY_KEY}) to replay.")
        else:
            self.tutorial_info.setText(f'Press Attribute Keys to Add/Remove, ({SPEED_UP_KEY}) to Speed Up the Video, ({SLOW_DOWN_KEY}) to Slow Down the Video, (' + BACK_KEY + ") to go back, (" + REPLAY_KEY + ") to Replay, or (" + NEXT_KEY + ") to Proceed to Next Video")
        self.playVideo(os.path.join(self.sign_directory_path, current_video))

    def playVideo(self, filename):
        media = self.instance.media_new(filename)
        self.mediaplayer.set_media(media)
        self.mediaplayer.set_rate(self.playback_speed)
        self.mediaplayer.play()

    def process_key(self, key):
        global hotkey_info
        global video_done
        global attribute_index_map
        global sign_annotations
        global full_annotation
        global attributes
        global hotkeys
        global current_video
        global app
        if key in hotkeys:
            if (hotkeys[key] == "wrong/variant sign"):
                if(current_video in reject_re_set):
                    reject_re_set.remove(current_video)
                else:
                    reject_re_set.add(current_video)
            if (self.recording_annotation[attribute_index_map[hotkeys[key]]] == ""):
                self.recording_annotation[attribute_index_map[hotkeys[key]]] = 'x'
                attributes.add(hotkeys[key])
            else:
                self.recording_annotation[attribute_index_map[hotkeys[key]]] = ""
                attributes.remove(hotkeys[key])

            self.text_label.setText(f"Current Attributes Are " + (str(attributes) if len(attributes) != 0 else ""))
        elif key == NEXT_KEY:
            if self.i >= len(self.videos):
                sign_annotations.sort()
                self.csv_writer.writerows(sign_annotations)
                self.annotations_csv.flush()
                self.add_video_to_be_deleted_txt()
                self.i = 0
                done = QtWidgets.QMessageBox()
                done.setWindowTitle("Annotations complete")
                done.setText("All requested videos have now been annotated. You can view your annotations in annotations.csv.")
                done.exec_()
                app.quit()
                return
            if len(attributes) == 0:
                # Do not allow the user to proceed unless an annotation has been made
                return
            full_annotation = [self.sign, self.videos[self.i]]
            full_annotation.extend(self.recording_annotation)
            if (self.i == len(sign_annotations)):
                sign_annotations.append(full_annotation)
            else:
                sign_annotations[self.i] = full_annotation
            self.i += 1
            if self.i >= len(self.videos):
                self.text_label.setText(f"End of videos. Press {NEXT_KEY} to finish or {BACK_KEY} to return if some signs are unsaved.")
                return
            # switch to next video
            if (self.i == len(sign_annotations)):
                self.recording_annotation = ["" for i in range(len(hotkeys))]
                attributes = set()
            else:
                self.recording_annotation = sign_annotations[self.i][2:]
                attributes = set()
                for idx, mark in enumerate(self.recording_annotation):
                    if mark == 'x':
                        attributes.add(hotkeys[self.hotkey_keys[idx]])
            self.text_label.setText(f"Current Attributes Are " + (str(attributes) if len(attributes) != 0 else ""))
            self.playFullVideo()
        elif key == REPLAY_KEY:
            video_done = True
            self.playFullVideo()
        elif key == BACK_KEY:
            if (self.i < len(self.videos)):
                full_annotation = [self.sign, self.videos[self.i]]
                full_annotation.extend(self.recording_annotation)
                if (self.i == len(sign_annotations)):
                    sign_annotations.append(full_annotation)
                else:
                    sign_annotations[self.i] = full_annotation
            if (self.i % 20 >= 1):
                self.i -= 1
                self.recording_annotation = sign_annotations[self.i][2:]
                attributes = set()
                for idx, mark in enumerate(self.recording_annotation):
                    if mark == 'x':
                        attributes.add(hotkeys[self.hotkey_keys[idx]])
                video_done = True
                self.text_label.setText(f"Current Attributes Are " + (str(attributes) if len(attributes) != 0 else ""))
                self.playFullVideo()
        elif (key == '`'):
            done = QtWidgets.QMessageBox()
            done.setWindowTitle("Annotations complete")
            done.setText("All requested videos have now been annotated. You can view your annotations in annotations.csv.")
            done.exec_()
            app.quit()
            return
        elif key == SPEED_UP_KEY:
            self.playback_speed *= 1.25
            self.playFullVideo()
        elif key == SLOW_DOWN_KEY:
            self.playback_speed /= 1.25
            self.playFullVideo()
        return self.i



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pass in directories to annotate')
    # takes a path to the directory
    parser.add_argument('-d', '--directory', required=True)
    # Output directory where annotations and reject lists will be outputted
    parser.add_argument('-o', '--output', default="")
    # takes a sign to annotate
    parser.add_argument('-s', '--sign', required=True)

    arguments = parser.parse_args()
    # Make a hotkey dict using the json file
    file = open("hotkeys.json")
    hotkeys = json.load(file)
    file.close()
    for key in hotkeys.keys():
        if(key == BACK_KEY or key == NEXT_KEY or key == REPLAY_KEY or key == DISPLAY_INFO):
            raise ValueError("Hotkeys cannot be the same as navigation keys")

    app = QtWidgets.QApplication(sys.argv)
    player = Player(directory=arguments.directory, sign=arguments.sign, hkeys=hotkeys, output_src=arguments.output)
    player.show()
    # Have this so that if the user minimizes it goes back to 640 x 480
    player.resize(640, 480)
    player.showMaximized()
    sys.exit(app.exec_())

