import os
import csv
import json
import argparse
import datetime
import sys
import vlc
import pandas as pd
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets

'''
TODO
Make it so you can start where you left off
Make it so the self.hotkeys can't be setkeys
Make it so two self.hotkeys can't be the same 
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
app = None
    
class Player(QtWidgets.QMainWindow):
    def __init__(self, parent=None, annotations=None, directory=None, group=None, sign=None, hotkeys=None,
                 output_src=None, ignore_existing=False, skip_existing=True):
        self.directory = directory
        self.group = group
        self.hotkeys = hotkeys
        self.resetCurrentAnnotation()

        self.attribute_index_map = {}
        for i, key in enumerate(self.hotkeys.keys()):
            self.attribute_index_map[self.hotkeys[key]] = i
            
        self.current_video = ""
        
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
        self.text_label.setFixedHeight(40)
        lay.addWidget(self.text_label)

        self.tutorial_info = QtWidgets.QLabel()
        self.tutorial_info.setText(f'Press Attribute Keys to Add/Remove, ({SPEED_UP_KEY}) to Speed Up the Video, '
                                   f'({SLOW_DOWN_KEY}) to Slow Down the Video, ({BACK_KEY}) to go back, ({REPLAY_KEY}) '
                                   f'to Replay, or ({NEXT_KEY}) to Proceed to Next Video')
        self.tutorial_info.setFixedHeight(40)
        lay.addWidget(self.tutorial_info)
        
        self.annotation_info = QtWidgets.QLabel()
        self.annotation_info.setText("Annotation mapping: " + str(self.hotkeys))
        self.annotation_info.setFixedHeight(40)
        lay.addWidget(self.annotation_info)

        self.playback_speed = 1.

        self.i = 0

        self.hotkey_keys = list(self.hotkeys.keys())

        # 2d array that stores a sign's annotation so that it can all be written at once.
        self.sign_annotations = []

        self.sign = sign
        
        self.sign_directory_path = os.path.join(self.directory, self.group, sign)

        self.videos = os.listdir(self.sign_directory_path)
        self.videos.sort()

        output_path = os.path.join(output_src, sign)
        Path(output_path).mkdir(parents=True, exist_ok=True)

        # see which files have already been annotated
        self.annotated_files = set()
        self.preannotated = {}
        csv_exists = False
        if not ignore_existing:
            annotation_filepath = os.path.join(output_path, "annotations.csv")
            if os.path.exists(annotation_filepath):
                csv_exists = True
                
                # I (Bill) indented in these lines since these would run when the file did not exist
                existing_annotations = pd.read_csv(annotation_filepath)
                existing_annotations.drop_duplicates(subset='sign', keep='last')

                for index, row in existing_annotations.iterrows():
                    self.preannotated[row['filename']] = row

        if skip_existing:
            videos_in = self.videos
            self.videos = []
            for vid in videos_in:
                filename = vid.split('/')[-1]
                if filename not in self.preannotated:
                    self.videos.append(filename)

        self.reject_re_set = set()

        reject_re_path = os.path.join(output_path, "REJECT_RE.txt")
        self.reject_re = open(reject_re_path, 'a')
        self.reject_re.write(f"Session at time {str(datetime.datetime.now())}: \n")

        # group_no_special_symbols = ''.join(e for e in group if e.isalnum())
        # datetime_str = datetime.datetime.now().strftime('%y-%m-%d-%H:%M:%S')
        # annotation_filepath = os.path.join(output_path, f"{group_no_special_symbols}_{datetime_str}_annotations.csv")
        annotation_filepath = os.path.join(output_path, "annotations.csv")
        self.annotations_csv = open(annotation_filepath, 'a')
        self.csv_writer = csv.writer(self.annotations_csv)
        
        # sign and filename are the first 2 in any of the headers
        annotation_header = ["sign", "filename"]
        annotation_header.extend(self.hotkeys.values())
        # Writes a header before each sign
        if not csv_exists:
            self.csv_writer.writerow(annotation_header)
            self.annotations_csv.flush()

        self.attributes = set()

        if len(self.videos) == 0:
            print("All videos have been annotated!")
            self.exitPlayer()
            return

        self.loadAnnotationFromCSV()

        self.playFullVideo()

    def loadExistingAnnotation(self):
        self.recording_annotation = self.sign_annotations[self.i][2:]
        self.attributes = set()
        for idx, mark in enumerate(self.recording_annotation):
            if mark == 'x':
                self.attributes.add(self.hotkeys[self.hotkey_keys[idx]])

    def storeCurrentAnnotation(self):
        full_annotation = [self.sign, self.videos[self.i]]
        full_annotation.extend(self.recording_annotation)
        self.csv_writer.writerow(full_annotation)
        self.annotations_csv.flush()
        if self.i == len(self.sign_annotations):
            self.sign_annotations.append(full_annotation)
        else:
            self.sign_annotations[self.i] = full_annotation

    def resetCurrentAnnotation(self):
        self.recording_annotation = ["" for i in range(len(self.hotkeys))]

    def loadAnnotationFromCSV(self):
        for idx, key in enumerate(self.hotkeys):
            filename = self.videos[self.i]
            if filename in self.preannotated:
                if self.preannotated[filename][self.hotkeys[key]] == 'x':
                    self.recording_annotation[idx] = 'x'
        self.attributes = set()
        for idx, mark in enumerate(self.recording_annotation):
            if mark == 'x':
                self.attributes.add(self.hotkeys[self.hotkey_keys[idx]])

    def exitPlayer(self):
        done = QtWidgets.QMessageBox()
        done.setWindowTitle("Annotations complete")
        done.setText("All requested videos have now been annotated. You can view your annotations in annotations.csv.")
        done.exec_()
        app.quit()
        return

    def updateAnnotationLabel(self):
        self.text_label.setText(f"Current attributes are {str(self.attributes)}")

    def addVideoToBeDeletedTxt(self):
        for video in self.reject_re_set:
            self.reject_re.write(video + "\n")
        self.reject_re_set.clear()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.playFullVideo()
        return super().resizeEvent(a0)
    
    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.isAutoRepeat():
            return
        self.processKey(a0.text())
        return super().keyPressEvent(a0)

    def playFullVideo(self):
        self.updateAnnotationLabel()
        self.current_video = self.videos[self.i]
        print(self.current_video)
        self.tutorial_info.setText(f'Press Attribute Keys to Add/Remove, ({SPEED_UP_KEY}) to Speed Up the Video, '
                                   f'({SLOW_DOWN_KEY}) to Slow Down the Video, ({BACK_KEY}) to go back, ({REPLAY_KEY}) '
                                   f'to Replay, or ({NEXT_KEY}) to Proceed to Next Video")')
        self.playVideo(os.path.join(self.sign_directory_path, self.current_video))

    def playVideo(self, filename, end_callback=None):
        media = self.instance.media_new(filename)
        self.mediaplayer.set_media(media)
        self.mediaplayer.set_rate(self.playback_speed)
        if end_callback:
            events = self.mediaplayer.event_manager()
            events.event_attach(vlc.EventType.MediaPlayerEndReached, end_callback)
        self.mediaplayer.play()

    def processKey(self, curr_key):
        global app
        if curr_key in self.hotkeys:
            if self.hotkeys[curr_key] == "wrong/variant sign":
                if self.current_video in self.reject_re_set:
                    self.reject_re_set.remove(self.current_video)
                else:
                    self.reject_re_set.add(self.current_video)
            if self.recording_annotation[self.attribute_index_map[self.hotkeys[curr_key]]] == "":
                self.recording_annotation[self.attribute_index_map[self.hotkeys[curr_key]]] = 'x'
                self.attributes.add(self.hotkeys[curr_key])
            else:
                self.recording_annotation[self.attribute_index_map[self.hotkeys[curr_key]]] = ''
                self.attributes.remove(self.hotkeys[curr_key])
            self.updateAnnotationLabel()
        elif curr_key == NEXT_KEY:
            if self.i == len(self.videos):
                self.annotations_csv.flush()
                self.addVideoToBeDeletedTxt()
                self.exitPlayer()
                return
            if len(self.attributes) == 0:
                # Do not allow the user to proceed unless an annotation has been made
                return
            self.storeCurrentAnnotation()
            self.i += 1
            if self.i == len(self.videos):
                self.updateAnnotationLabel()
                self.text_label.setText(f"End of videos. Press {NEXT_KEY} to finish or {BACK_KEY} to return if some "
                                        f"signs are unsaved. {self.text_label.text()}")
                return
            # switch to next video
            if self.i == len(self.sign_annotations):
                self.resetCurrentAnnotation()
                self.loadAnnotationFromCSV()
            else:
                self.loadExistingAnnotation()
            self.playFullVideo()
        elif curr_key == REPLAY_KEY:
            if self.i < len(self.videos):
                self.playFullVideo()
        elif curr_key == BACK_KEY:
            if self.i < len(self.videos):
                self.storeCurrentAnnotation()
            if self.i >= 1:
                self.i -= 1
                self.loadExistingAnnotation()
                self.updateAnnotationLabel()
                self.playFullVideo()
        elif curr_key == '`':
            self.exitPlayer()
            return
        elif curr_key == SPEED_UP_KEY:
            self.playback_speed *= 1.25
            self.playFullVideo()
        elif curr_key == SLOW_DOWN_KEY:
            self.playback_speed /= 1.25
            self.playFullVideo()
        return self.i


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pass in directories to annotate')
    # takes a path to the source directory
    parser.add_argument('-d', '--directory', required=True)
    # takes the group of signs (a subdirectory) in the source directory to be annotated
    parser.add_argument('-g', '--group', default="", required=False)
    # Output directory where annotations and reject lists will be outputted
    parser.add_argument('-o', '--output', default="")
    # takes a sign to annotate
    parser.add_argument('-s', '--sign', required=True)
    # takes the hotkey dictionary to annotate with
    parser.add_argument('-h', '--hotkey', default="hotkeys.json")

    arguments = parser.parse_args()
    # Make a hotkey dict using the json file
    file = open(arguments.hotkey)
    hotkeys = json.load(file)
    file.close()
    for key in hotkeys.keys():
        if key == BACK_KEY or key == NEXT_KEY or key == REPLAY_KEY or key == DISPLAY_INFO:
            raise ValueError("hotkeys cannot be the same as navigation keys")

    app = QtWidgets.QApplication(sys.argv)
    player = Player(directory=arguments.directory, group=arguments.group, sign=arguments.sign, hotkeys=hotkeys,
                    output_src=arguments.output)
    if len(player.videos) != 0:
        player.show()
        # Have this so that if the user minimizes it goes back to 640 x 480
        player.resize(640, 480)
        sys.exit(app.exec_())

