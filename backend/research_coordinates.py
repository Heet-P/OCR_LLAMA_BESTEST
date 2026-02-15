
import fitz
import sys

def analyze_pdf_coordinates(file_path, search_labels):
    doc = fitz.open(file_path)
    print(f"Analyzing {file_path} with {len(doc)} pages...")

    results = {}

    for page_num, page in enumerate(doc):
        print(f"--- Page {page_num + 1} ---")
        
        # 1. Search for Labels
        for label in search_labels:
            print(f"Searching for label: '{label}'")
            # Loose search
            text_instances = page.search_for(label)
            if text_instances:
                print(f"  Found '{label}' at: {text_instances}")
                
                # For each instance, look for nearby "______" or "....."
                # We can search for patterns
                underscores = page.search_for("____")
                dots = page.search_for("....")
                
                candidates = underscores + dots
                
                # Find nearest candidate to the right or below
                best_cand = None
                min_dist = float('inf')
                
                label_rect = text_instances[0] # Take first for now
                
                for cand in candidates:
                    # Check if candidate is "after" the label
                    # 1. Same line, to the right
                    if abs(cand.y0 - label_rect.y0) < 10 and cand.x0 > label_rect.x0:
                         dist = cand.x0 - label_rect.x1
                         if dist < min_dist:
                             min_dist = dist
                             best_cand = cand
                    
                    # 2. Below (Next line)
                    elif cand.y0 > label_rect.y0 and cand.y0 < label_rect.y0 + 50: # Within 50 units down
                         # Closer in X alignment?
                         dist = ((cand.x0 - label_rect.x0)**2 + (cand.y0 - label_rect.y1)**2)**0.5
                         if dist < min_dist:
                             min_dist = dist
                             best_cand = cand
                             
                if best_cand:
                    print(f"  -> Found input zone at {best_cand}")
                    results[label] = {"page": page_num, "rect": [best_cand.x0, best_cand.y0, best_cand.x1, best_cand.y1]}
                else:
                    print(f"  -> No visual input zone found near label.")
                    # Fallback: Just append right after label?
            else:
                print(f"  Label '{label}' not found.")

    return results

if __name__ == "__main__":
    # Create a dummy PDF for testing since we might not have one
    doc = fitz.open()
    page = doc.new_page()
    
    # Draw some "Form" elements
    page.insert_text((50, 50), "Full Name: _______________________", fontsize=12)
    page.insert_text((50, 100), "Email Address:", fontsize=12)
    page.insert_text((150, 100), ".......................", fontsize=12)
    
    page.insert_text((50, 150), "Phone Number:", fontsize=12)
    # Vector line example
    page.draw_line((150, 160), (300, 160))
    
    filename = "test_form.pdf"
    doc.save(filename)
    print(f"Created {filename}")
    
    labels = ["Full Name", "Email Address", "Phone Number"]
    analyze_pdf_coordinates(filename, labels)
