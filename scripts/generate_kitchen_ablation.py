import json
import string
from pathlib import Path
from tqdm import tqdm
from PIL import ImageFont

from src.core.models import Floorplan
from src.rendering.image_renderer import FloorplanRenderer
from src.rendering.styles import DEFAULT_STYLE

class AnonymizedRenderer(FloorplanRenderer):
    def __init__(self, style=DEFAULT_STYLE):
        super().__init__(style)
        self.room_names = {}
        self.available_names = list(string.ascii_uppercase)
        
    def render_to_image(self, floorplan: Floorplan):
        # Reset names for each floorplan
        self.room_names = {}
        self.name_idx = 0
        return super().render_to_image(floorplan)

    def _draw_room_label(self, draw, room, scale, offset_x, offset_y):
        center = room.bounds.center
        center_x = center.x * scale + offset_x
        center_y = center.y * scale + offset_y

        if room.id not in self.room_names:
            if self.name_idx < len(self.available_names):
                self.room_names[room.id] = f"Room {self.available_names[self.name_idx]}"
                self.name_idx += 1
            else:
                self.room_names[room.id] = f"Room {self.name_idx}"
                self.name_idx += 1

        label = self.room_names[room.id]

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.style.font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((center_x, center_y), label, font=font, anchor="mm")
        draw.text((center_x, center_y), label, fill=self.style.text_color, font=font, anchor="mm")

def main():
    with open("data/floorplan_qa_benchmark/dataset_index.json") as f:
        clean_data = json.load(f)
        
    # Get first 69 kitchen entries from the scientific dataset
    kitchen_data = [d for d in clean_data if d["ground_truth"] == "kitchen"]
    ablation_data = kitchen_data[:69]
    
    out_dir = Path("data/kitchen_ablation")
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    
    renderer = AnonymizedRenderer()
    
    # Process and render
    final_dataset = []
    for entry in tqdm(ablation_data, desc="Generating Ablation Images"):
        fp_path = Path("data/floorplan_qa_benchmark/floorplans") / f"{entry['floorplan_id']}.json"
        with open(fp_path) as fp_file:
            fp_dict = json.load(fp_file)
        fp = Floorplan.from_dict(fp_dict)
        
        # Save new image
        img_path = img_dir / f"{fp.id}.png"
        renderer.render(fp, str(img_path))
        
        # Update entry format to match typical evaluator expectation
        new_entry = {
            "floorplan_id": fp.id,
            "image_path": f"images/{fp.id}.png",
            "ground_truth": entry["ground_truth"],
            "difficulty": fp_dict.get("mystery_room", {}).get("difficulty", "medium"),
            "split": "clean"
        }
        final_dataset.append(new_entry)
        
    with open(out_dir / "dataset.json", "w") as f:
        json.dump(final_dataset, f, indent=2)
        
    print(f"Generated {len(final_dataset)} anonymized floorplans in {out_dir}")

if __name__ == "__main__":
    main()
