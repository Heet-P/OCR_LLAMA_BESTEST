import fitz

class CoordinateMapper:
    def get_field_coordinates(self, doc, schema):
        """
        Scan the PDF document to find coordinates for fields defined in the schema.
        Returns a dictionary: { field_id: { page_idx, rect: fitz.Rect } }
        """
        results = {}
        fields = schema.get('fields', [])
        
        # Pre-scan pages for text to avoid repeated IO
        # For small-medium PDFs this is fine.
        
        for field in fields:
            label = field.get('label')
            field_id = field.get('id')
            
            if not label:
                continue
                
            match = self._find_field_location(doc, label)
            if match:
                results[field_id] = match
                
        return results

    def _find_field_location(self, doc, label):
        """
        Finds the best writing location for a given label.
        Strategy:
        1. Search for Label.
        2. Look for "______" or "....." to the right or below.
        3. If no line found, default to 'Right of Label'.
        """
        
        # 1. Search for Label
        for page_idx, page in enumerate(doc):
            # Debug: Check if page has text
            text_len = len(page.get_text())
            if text_len < 10:
                print(f"WARNING: Page {page_idx} has very little text ({text_len} chars). It might be an image/scan. Visual mapping will likely fail.")
                
            label_instances = page.search_for(label)
            
            if not label_instances:
                continue
                
            # Use the first instance for now (simplification)
            # In complex forms, we might need to verify context
            label_rect = label_instances[0]
            
            # 2. Look for Lines (____ or ....)
            # We search a "Region of Interest" (ROI) around the label
            roi = fitz.Rect(label_rect.x0, label_rect.y0 - 10, page.rect.width, label_rect.y1 + 50)
            
            # Search for patterns
            underscores = page.search_for("____", clip=roi)
            dots = page.search_for("....", clip=roi)
            lines = underscores + dots
            
            best_candidate = None
            min_dist = float('inf')
            
            # Heuristic: Find closest line
            for line in lines:
                # Calculate distance from label end
                
                # Case A: Same line (Right)
                if abs(line.y1 - label_rect.y1) < 10 and line.x0 > label_rect.x0:
                     dist = line.x0 - label_rect.x1
                     if dist < min_dist:
                         min_dist = dist
                         best_candidate = line
                
                # Case B: Next line (Below)
                elif line.y0 > label_rect.y0:
                     # Calculate visual distance
                     dist = ((line.x0 - label_rect.x0)**2 + (line.y0 - label_rect.y1)**2)**0.5
                     # Penalty for vertical distance to prefer same-line
                     dist = dist * 1.5 
                     
                     if dist < min_dist:
                         min_dist = dist
                         best_candidate = line
            
            if best_candidate:
                # We found a line! Return its rect.
                # Adjust slightly upwards to write ON the line
                target_rect = fitz.Rect(best_candidate.x0, best_candidate.y0 - 5, best_candidate.x1, best_candidate.y1)
                return {"page_idx": page_idx, "rect": target_rect, "method": "visual_line"}
            
            # 3. Fallback: Right of Label (Simple)
            # If no line detected, just designate the space to the right
            # Estimated width = 200
            target_rect = fitz.Rect(label_rect.x1 + 10, label_rect.y0, label_rect.x1 + 210, label_rect.y1)
            return {"page_idx": page_idx, "rect": target_rect, "method": "fallback_right"}
            
        return None

    def map_acroform_fields(self, doc, schema):
        """
        Maps extracted schema field IDs to PDF Form (AcroForm) widget names.
        Returns { field_id: widget_name }
        """
        mapping = {}
        fields = schema.get('fields', [])
        
        # Collect all PDF widget names
        pdf_fields = []
        for page in doc:
            for widget in page.widgets():
                if widget.field_name:
                    pdf_fields.append(widget.field_name)
        
        print(f"DEBUG: Found PDF Form Fields: {pdf_fields}")
        
        for field in fields:
            label = field.get('label', '').lower()
            field_id = field.get('id')
            
            # Simple fuzzy match: Check if label is part of pdf field name
            # or pdf field name is part of label.
            # Strip underscores and spaces for better matching
            clean_label = label.replace("_", "").replace(" ", "")
            
            best_match = None
            
            for pdf_field in pdf_fields:
                clean_pdf = pdf_field.lower().replace("_", "").replace(" ", "")
                
                if clean_label in clean_pdf or clean_pdf in clean_label:
                    best_match = pdf_field
                    break
            
            if best_match:
                mapping[field_id] = best_match
                
        return mapping

mapper = CoordinateMapper()
