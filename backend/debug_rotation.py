import fitz

def test_rotation_logic():
    # Create a dummy PDF with rotation
    doc = fitz.open()
    page = doc.new_page(width=100, height=200)
    
    # Add text at specific location (unrotated)
    # x=10, y=10
    shape = page.new_shape()
    shape.insert_text((10, 20), "HelloRotated")
    shape.commit()
    
    # Rotate the page 90 degrees clockwise
    page.set_rotation(90)
    
    # 1. Search (Unrotated coords expected)
    hits = page.search_for("HelloRotated")
    rect = hits[0]
    print(f"Unrotated Search Rect: {rect}")
    print(f"Page Rotation: {page.rotation}")
    
    # 2. Render (Rotated Image expected)
    pix = page.get_pixmap()
    print(f"Rotated Image Size: W={pix.width}, H={pix.height}")
    
    # The new width should be 200, height 100.
    
    # 3. Transform Logic
    # If we want the rect on the rotated image.
    # 90 deg clockwise: (x, y) -> (h - y, x) ??
    # PyMuPDF has page.derotation_matrix? Or page.rotation_matrix?
    
    mat = page.rotation_matrix
    print(f"Rotation Matrix: {mat}")
    
    # Apply matrix to rect
    rot_rect = rect * mat
    print(f"Rotated Rect (Matrix): {rot_rect}")
    
    # Normalize
    # If rotated 90, width is now height?
    
    # Manual check:
    # Point (10, 20) on 100x200 page.
    # Rotated 90 deg CW.
    # 100x200 becomes 200x100.
    # (10, 20) -> goes to top-right? No.
    # 0,0 (top-left) -> 90 -> top-right.
    
    # Let's see what PyMuPDF returns.

if __name__ == "__main__":
    test_rotation_logic()
