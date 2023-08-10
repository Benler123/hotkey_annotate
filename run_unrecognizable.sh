#!/bin/bash
# Usage: ./run_unrecognizable.sh (review_source_folder_name) (sign)
# Example: ./run_unrecognizable.sh unrecognizable thankyou
python3 fast_annotate.py -d ~/ServerData/sign_language_videos/first_round_datasets/sorted_videos_first_round_250_signs/$1 -o ~/ServerData/sign_language_videos/annotation_output_unrecognizable -s $2