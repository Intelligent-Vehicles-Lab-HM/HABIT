#!/bin/bash
# Download HABIT motion data (4,730 .pkl files) from Google Drive
#
# Usage:
#   bash scripts/download_motion_data.sh
#
# Requires: gdown (pip install gdown)

set -e

DEST_DIR="data/motions"
FILE_ID="1L_BPWBYE-Ho5ieSKZSN-LRNP2OfDdVIi"
ZIP_NAME="habit_motion_data.zip"

# Check for gdown
if ! command -v gdown &> /dev/null; then
    echo "gdown is required but not installed. Install it with:"
    echo "  pip install gdown"
    echo ""
    echo "Or download manually from:"
    echo "  https://drive.google.com/file/d/${FILE_ID}/view?usp=sharing"
    echo "Then extract .pkl files into ${DEST_DIR}/"
    exit 1
fi

echo "Downloading HABIT motion data..."
gdown "${FILE_ID}" -O "${ZIP_NAME}"

echo "Extracting to ${DEST_DIR}/..."
mkdir -p "${DEST_DIR}"
unzip -j "${ZIP_NAME}" "*.pkl" -d "${DEST_DIR}/"

echo "Cleaning up..."
rm "${ZIP_NAME}"

NUM_FILES=$(ls "${DEST_DIR}"/*.pkl 2>/dev/null | wc -l)
echo "Done. ${NUM_FILES} motion files in ${DEST_DIR}/"
