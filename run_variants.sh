#!/bin/bash
# Usage: ./run_variants.sh (sign) (variant round)
# Example: ./run_variants.sh thankyou 1
python3 fast_annotate.py -d ~/ServerData/sign_language_videos/first_round_datasets/variant_review_set -o ~/ServerData/sign_language_videos/variant_annotations/$2 -s $1 -y hotkeys_variants.json
