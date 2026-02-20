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

    def _normalize_pdf_field_name(self, pdf_field_name):
        """
        Remove PDF field type suffixes and normalize the name.
        Examples:
        - 'Given Name Text Box' -> 'given name'
        - 'Family Name Text Box' -> 'family name'
        - 'Country Combo Box' -> 'country'
        - 'Gender List Box' -> 'gender'
        - 'Driving License Check Box' -> 'driving license'
        """
        # Common PDF field type suffixes to remove
        suffixes = [
            ' text box', ' textbox', ' text',
            ' combo box', ' combobox', ' combo',
            ' list box', ' listbox', ' list',
            ' check box', ' checkbox', ' check',
            ' formatted field', ' formattedfield', ' formatted',
            ' field', ' box'
        ]
        
        normalized = pdf_field_name.lower().strip()
        
        # Remove suffixes (try longest first)
        for suffix in sorted(suffixes, key=len, reverse=True):
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
                break
        
        return normalized
    
    def _normalize_label(self, label):
        """
        Normalize schema label for matching.
        """
        if not label:
            return ""
        # Convert to lowercase and strip
        normalized = label.lower().strip()
        return normalized
    
    def _calculate_match_score(self, label_words, pdf_field_words):
        """
        Calculate a match score between label words and PDF field words.
        Returns a score from 0.0 to 1.0, where 1.0 is perfect match.
        """
        if not label_words or not pdf_field_words:
            return 0.0
        
        # Count exact word matches
        exact_matches = sum(1 for word in label_words if word in pdf_field_words)
        
        # Count partial matches (word contains or is contained in another word)
        partial_matches = 0
        for label_word in label_words:
            for pdf_word in pdf_field_words:
                if label_word in pdf_word or pdf_word in label_word:
                    partial_matches += 0.5
                    break
        
        # Calculate score: exact matches are worth more
        total_possible = len(label_words)
        if total_possible == 0:
            return 0.0
        
        score = (exact_matches + min(partial_matches, total_possible - exact_matches)) / total_possible
        
        # Bonus for exact string match
        label_str = ' '.join(label_words)
        pdf_str = ' '.join(pdf_field_words)
        if label_str == pdf_str:
            score = 1.0
        
        return score
    
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
        
        # Track which PDF fields have been mapped to prevent duplicates
        used_pdf_fields = set()
        
        for field in fields:
            label = field.get('label', '')
            field_id = field.get('id')
            
            if not label:
                print(f"DEBUG: Skipping field {field_id} - no label")
                continue
            
            # Normalize label and split into words
            normalized_label = self._normalize_label(label)
            label_words = [w for w in normalized_label.replace('_', ' ').replace('-', ' ').split() if w]
            
            if not label_words:
                print(f"DEBUG: Skipping field {field_id} - empty label after normalization")
                continue
            
            print(f"DEBUG: Matching schema field '{field_id}' with label '{label}' (normalized: '{normalized_label}', words: {label_words})")
            
            best_match = None
            best_score = 0.0
            match_threshold = 0.3  # Minimum score to consider a match
            
            for pdf_field in pdf_fields:
                # Skip if already mapped
                if pdf_field in used_pdf_fields:
                    continue
                
                # Normalize PDF field name (remove type suffixes)
                normalized_pdf = self._normalize_pdf_field_name(pdf_field)
                pdf_words = [w for w in normalized_pdf.replace('_', ' ').replace('-', ' ').split() if w]
                
                if not pdf_words:
                    continue
                
                # Calculate match score
                score = self._calculate_match_score(label_words, pdf_words)
                
                print(f"  Comparing with PDF field '{pdf_field}' (normalized: '{normalized_pdf}', words: {pdf_words}) -> score: {score:.2f}")
                
                if score > best_score and score >= match_threshold:
                    best_score = score
                    best_match = pdf_field
            
            if best_match:
                mapping[field_id] = best_match
                used_pdf_fields.add(best_match)
                print(f"✓ MATCHED: '{field_id}' ('{label}') -> '{best_match}' (score: {best_score:.2f})")
            else:
                print(f"✗ NO MATCH: '{field_id}' ('{label}') - best score was {best_score:.2f} (below threshold {match_threshold})")
                
        print(f"DEBUG: Total mappings created: {len(mapping)}")
        return mapping

mapper = CoordinateMapper()
