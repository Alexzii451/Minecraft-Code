import requests
from PIL import Image, ImageDraw
import os
import json
from datetime import datetime

# Constants
UPKEEP_COST_PER_CHUNK = 30.0

# Suppress the DecompressionBombWarning
Image.MAX_IMAGE_PIXELS = None

# Directory containing the pre-downloaded tiles
tiles_dir = 'C:/Users/alexz/Desktop/LandClaimsChecker/tiles'
removed_dir = 'LandClaimsChecker/removed_logs'
maps_dir = 'LandClaimsChecker/maps'

# Ensure the maps directory exists
os.makedirs(maps_dir, exist_ok=True)

# Load the stitched map image
map_image_path = os.path.join(tiles_dir, 'combined_map.png')
map_image = Image.open(map_image_path)

# Calculate the total width and height in pixels
tile_size = 128
map_width, map_height = map_image.size

# Create an overlay image for transparency
overlay = Image.new('RGBA', (map_width, map_height), (255, 255, 255, 0))
overlay_draw = ImageDraw.Draw(overlay)

# Known corner coordinates
top_left_coords = (-13312, -12064)
top_right_coords = (9216, -12064)
bottom_left_coords = (-13312, 11488)

# Calculate the scale
scale_x = (top_right_coords[0] - top_left_coords[0]) / map_width
scale_y = (bottom_left_coords[1] - top_left_coords[1]) / map_height


# Function to translate game coordinates to pixel coordinates
def game_to_pixel(x, z):
    pixel_x = (x - top_left_coords[0]) / scale_x
    pixel_y = (z - top_left_coords[1]) / scale_y
    return pixel_x, pixel_y


# Function to load the latest removed claims file
def get_latest_removed_file(removed_folder):
    log_files = [f for f in os.listdir(removed_folder) if f.endswith('.json')]
    log_files.sort(reverse=True)
    if len(log_files) < 1:
        return None
    return log_files[0]


# Load the latest removed claims
latest_removed_file = get_latest_removed_file(removed_dir)
if latest_removed_file:
    removed_claims = json.load(open(os.path.join(removed_dir, latest_removed_file)))
    unclaimed_claims_count = len(removed_claims)

    for claim in removed_claims:
        claim_coords_x = claim['coordinates']['x']
        claim_coords_z = claim['coordinates']['z']
        claim_pixels = [game_to_pixel(x, z) for x, z in zip(claim_coords_x, claim_coords_z)]

        # Draw the polygon in transparent red
        overlay_draw.polygon(claim_pixels, outline=(255, 0, 0, 255), fill=(255, 0, 0, 128))

        # Calculate bounding box for the ellipse
        min_x = min([pixel[0] for pixel in claim_pixels])
        max_x = max([pixel[0] for pixel in claim_pixels])
        min_y = min([pixel[1] for pixel in claim_pixels])
        max_y = max([pixel[1] for pixel in claim_pixels])

        # Draw a larger and bolder red ellipse around the claim
        margin = 300  # Increase the size of the circle
        boldness = 40  # Increase the boldness of the circle
        ellipse_box = [min_x - margin, min_y - margin, max_x + margin, max_y + margin]
        overlay_draw.ellipse(ellipse_box, outline=(255, 0, 0, 255), width=boldness)

    # Combine the overlay with the map image
    combined_image = Image.alpha_composite(map_image.convert('RGBA'), overlay)

    # Save the final image with a timestamp
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(maps_dir, f'combined_map_with_removed_claims_{current_time}.png')
    combined_image.save(output_path)
    combined_image.show()

    # Print the results
    print(f"Number of claims that were removed: {unclaimed_claims_count}")
else:
    print("No removed claims file found.")
