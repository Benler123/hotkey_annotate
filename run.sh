#!/bin/bash
# Usage: ./run.sh (review_source_folder_name) (sign)
# Example: ./run.sh review_1 thankyou
python3 fast_annotate.py -d ~/ServerData/sign_language_videos/review_sets/review_misclassified -g $1 -o ~/ServerData/sign_language_videos/annotation_output_misclassified -s $2
