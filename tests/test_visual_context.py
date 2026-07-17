from pathlib import Path
from tempfile import TemporaryDirectory

import server.visual_context as visual_context


def test_uploaded_image_node_becomes_bounded_vision_input():
    original_upload_dir = visual_context.UPLOAD_DIR
    try:
        with TemporaryDirectory() as tmp:
            upload_dir = Path(tmp)
            image_path = upload_dir / "reference.png"
            image_path.write_bytes(b"image-bytes")
            visual_context.UPLOAD_DIR = upload_dir
            canvas = {
                "nodes": [
                    {
                        "id": "image-a",
                        "type": "image",
                        "title": "Reference hand",
                        "payload": {
                            "image_file": "uploads/reference.png",
                            "image_url": "/uploads/reference.png",
                            "mime_type": "image/png",
                        },
                    }
                ]
            }
            result = visual_context.visual_context_for_nodes(canvas, ["image-a"])
            assert result["references"][0]["node_id"] == "image-a"
            assert result["inputs"][0]["data_url"].startswith("data:image/png;base64,")
    finally:
        visual_context.UPLOAD_DIR = original_upload_dir
