import os
import logging
from PIL import Image, ImageEnhance, ImageOps
from utils.file_helpers import ensure_file_output_dir, generate_unique_file_path

logger = logging.getLogger(__name__)

def process_images(files, resize_method, resize_pct, fixed_width, fixed_height, maintain_aspect,
                   aspect_choice, margin, do_rename, rename_prefix, do_reformat, new_format, app):
    total = len(files)
    app.queue.put((None, "status", "Processing image files..."))
    app.start_progress()
    for i, f in enumerate(files, start=1):
        process_single_image(f, resize_method, resize_pct, fixed_width, fixed_height,
                             maintain_aspect, aspect_choice, margin, do_rename,
                             rename_prefix, do_reformat, new_format, app)
        app.increment_progress(i, total)
    app.queue.put((None, "done", "Image processing complete."))

def process_single_image(file_path, resize_method, resize_pct, fixed_width, fixed_height,
                         maintain_aspect, aspect_choice, margin, do_rename, rename_prefix,
                         do_reformat, new_format, app):
    try:
        img = Image.open(file_path)
        img = ImageOps.exif_transpose(img)
        if resize_method != "none":
            img = crop_to_square(img)
            if resize_method == "percentage":
                img = resize_image_percentage(img, resize_pct)
            elif resize_method == "fixed":
                img = resize_image_fixed(img, fixed_width, fixed_height, maintain_aspect, aspect_choice)
        if margin:
            img = add_image_inner_margin(img)
        img = sharpen_image(img)
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        new_base = f"{rename_prefix}_{base_name}" if do_rename else base_name + "_processed"
        final_ext = new_format if do_reformat else ext.replace('.', '')
        out_dir = ensure_file_output_dir(file_path)
        output_file = generate_unique_file_path(out_dir, new_base, "", final_ext)
        img.save(output_file)
        app.queue.put((file_path, "status", f"Image saved to: {output_file}"))
    except Exception as e:
        logger.error(f"Error processing image {file_path}: {e}")
        app.queue.put((file_path, "status", f"Error: {str(e)}"))

def crop_to_square(img):
    width, height = img.size
    min_side = min(width, height)
    left = (width - min_side) // 2
    top = (height - min_side) // 2
    return img.crop((left, top, left + min_side, top + min_side))

def resize_image_percentage(img, pct):
    width, height = img.size
    new_w = int(width * (pct / 100.0))
    new_h = int(height * (pct / 100.0))
    return img.resize((new_w, new_h), Image.LANCZOS)

def resize_image_fixed(img, fixed_width, fixed_height, maintain_aspect, aspect_choice):
    if maintain_aspect:
        if aspect_choice == "Original":
            orig_width, orig_height = img.size
            ratio = orig_height / orig_width
        else:
            try:
                parts = aspect_choice.split(':')
                if len(parts) == 2:
                    w_ratio = float(parts[0])
                    h_ratio = float(parts[1])
                    ratio = h_ratio / w_ratio
                else:
                    ratio = fixed_height / fixed_width
            except:
                ratio = fixed_height / fixed_width
        new_width = fixed_width
        new_height = int(fixed_width * ratio)
        return img.resize((new_width, new_height), Image.LANCZOS)
    else:
        return img.resize((fixed_width, fixed_height), Image.LANCZOS)

def add_image_inner_margin(img):
    margin = 16
    width, height = img.size
    new_img = Image.new("RGB", (width, height), (255, 255, 255))
    new_img.paste(img.crop((margin, margin, width - margin, height - margin)), (margin, margin))
    return new_img

def sharpen_image(img):
    enhancer = ImageEnhance.Sharpness(img)
    return enhancer.enhance(1.5)
