#!/bin/bash
# Usage: ./run_variants.sh (sign)
# Example: ./run_variants.sh sun
python3 fast_annotate.py -d ~/ServerData/sign_language_videos/first_round_datasets/variant_review_set -o ~/ServerData/sign_language_videos/annotation_output_variants/$1 -s $1
