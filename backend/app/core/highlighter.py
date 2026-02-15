import fitz

class Highlighter:
    def search_text(self, doc: fitz.Document, query: str):
        """
        Search for text in the document and return coordinates.
        Returns a list of occurrences:
        [
            { "page": 1, "rect": [x0, y0, x1, y1], "text": "..." }
        ]
        """
        results = []
        
        # Simple exact/case-insensitive search
        for page_idx, page in enumerate(doc):
            # Page dimensions (Use cropbox as get_pixmap uses it by default)
            # Cropbox is the visible area. Rect is the media box.
            # search_for returns coordinates relative to the unrotated page.
            # But get_pixmap returns the rotated image.
            # We must transform the coordinates.
            
            box = page.cropbox
            rotation = page.rotation
            mat = page.rotation_matrix
            
            # Rotated Cropbox (to get output image dimensions and offset)
            # Apply matrix to cropbox to find the new bounding box in the rotated space
            rot_box = box * mat
            # rot_box isn't necessarily a valid rect (points might be swapped), so we take valid rect
            rot_rect = rot_box.pagerect # this might be wrong?
            # Actually, standard PyMuPDF way:
            rot_box_rect = fitz.Rect(rot_box)
            
            w = rot_box_rect.width
            h = rot_box_rect.height
            origin_x = rot_box_rect.x0
            origin_y = rot_box_rect.y0

            print(f"DEBUG: Page {page_idx+1} Rot: {rotation}, Box: {box} -> RotBox: {rot_box_rect} (W={w}, H={h})")
            
            hits = page.search_for(query)
            
            # Fallback
            if not hits and len(query.split()) > 1:
                words = query.split()
                candidates = [w for w in words if len(w) > 3]
                if candidates:
                    longest = max(candidates, key=len)
                    hits = page.search_for(longest)
            
            for rect in hits:
                # 1. Transform rect to rotated space
                r = rect * mat
                
                # 2. Normalize relative to the Rotated Cropbox
                # The image matches rot_box_rect.
                
                x0 = (r.x0 - origin_x) / w
                y0 = (r.y0 - origin_y) / h
                x1 = (r.x1 - origin_x) / w
                y1 = (r.y1 - origin_y) / h
                
                # Ensure x0 < x1, y0 < y1 (Rotation might flip them)
                if x0 > x1: x0, x1 = x1, x0
                if y0 > y1: y0, y1 = y1, y0
                
                print(f"DEBUG: Match '{query}' -> Rect: {rect} -> RotRect: {r} -> Norm: {x0:.3f},{y0:.3f}")
                
                results.append({
                    "page": page_idx + 1,
                    "rect": [x0, y0, x1, y1],
                    "text": query
                })
                
        return results
    
    def render_page(self, doc: fitz.Document, page_idx: int) -> bytes:
        """
        Render a specific page as a PNG image.
        """
        if page_idx < 0 or page_idx >= len(doc):
            raise ValueError("Invalid page index")
            
        page = doc[page_idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for clarity
        return pix.tobytes("png")

highlighter = Highlighter()
