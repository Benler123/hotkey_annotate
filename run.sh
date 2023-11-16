#!/bin/bash
# Usage: ./run.sh (review_source_folder_name) (sign)
#THIS IS TEMPORARY SWITCH TO A DIFFERENT BRANCH
# Example: ./run.sh review_1 batch_10
python3 fast_annotate.py -d ~/ServerData/sign_language_videos/review_sets/review_phrase/ -g $1 -o ~/ServerData/sign_language_videos/annotation_output_phrases/$1 -s $2
