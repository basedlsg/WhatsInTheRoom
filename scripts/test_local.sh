#!/bin/bash
# Local-only test script - NO NETWORK REQUIRED
# Tests floorplan generation and rendering without calling NVIDIA API

set -e  # Exit on error

echo "=============================================="
echo "Local-Only Pipeline Test (No Network Required)"
echo "=============================================="
echo

# Clean previous test data
echo "[1/4] Cleaning previous test data..."
rm -rf data/test_local
mkdir -p data/test_local/floorplans data/test_local/images

# Generate 5 test floorplans
echo "[2/4] Generating 5 synthetic floorplans..."
python -m src.pipeline.generate_dataset \
    --count 5 \
    --regions US_SUBURB \
    --sizes SMALL,MEDIUM \
    --floorplan-dir data/test_local/floorplans \
    --image-dir data/test_local/images

# Verify generation
echo
echo "[3/4] Verifying generated files..."
FLOORPLAN_COUNT=$(ls -1 data/test_local/floorplans/*.json 2>/dev/null | wc -l)
IMAGE_COUNT=$(ls -1 data/test_local/images/*.png 2>/dev/null | wc -l)

echo "  Floorplans: $FLOORPLAN_COUNT JSON files"
echo "  Images: $IMAGE_COUNT PNG files"

if [ "$FLOORPLAN_COUNT" -eq 0 ] || [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "  ❌ FAILED: No files generated"
    exit 1
fi

# Show a sample floorplan
echo
echo "[4/4] Sample generated floorplan:"
SAMPLE=$(ls data/test_local/floorplans/*.json | head -1)
echo "  File: $(basename $SAMPLE)"
echo "  Content preview:"
python -c "
import json
with open('$SAMPLE', 'r') as f:
    data = json.load(f)
print(f\"    ID: {data['id']}\")
print(f\"    Region: {data['region']}\")
print(f\"    Size: {data['size_category']}\")
print(f\"    Rooms: {len(data['rooms'])}\")
print(f\"    Doors: {len(data['doors'])}\")
print(f\"    Mystery room: {data['mystery_room_id'][:8]}...\")
"

echo
echo "=============================================="
echo "✅ SUCCESS: Local pipeline works!"
echo "=============================================="
echo
echo "Generated data in: data/test_local/"
echo "  - Floorplan metadata: data/test_local/floorplans/"
echo "  - Rendered images: data/test_local/images/"
echo
echo "To view an image, open: data/test_local/images/<filename>.png"
echo
echo "=============================================="
