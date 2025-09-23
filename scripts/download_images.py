
import json
import requests
import os
from hashlib import md5
from urllib.parse import urlparse
import sys

def download_images():
    
    json_file = "app/data/demo_books.json"
    images_dir = "app/static/images"
    
    os.makedirs(images_dir, exist_ok=True)
    
    with open(json_file, 'r') as f:
        books = json.load(f)
    
    print(f"Processing {len(books)} books...")
    
    updated_books = []
    
    for i, book in enumerate(books):
        print(f"Processing book {i+1}/{len(books)}: {book['title']}")
        
        original_url = book.get('cover_image_url', '')
        
        if not original_url or original_url.startswith('/static/'):
            updated_books.append(book)
            continue
        
        try:
            book_id = book.get('id', str(i))
            url_hash = md5(original_url.encode()).hexdigest()[:8]
            
            parsed_url = urlparse(original_url)
            path = parsed_url.path
            ext = os.path.splitext(path)[1] if os.path.splitext(path)[1] else '.jpg'
            
            filename = f"book_{i+1}_{url_hash}{ext}"
            local_path = os.path.join(images_dir, filename)
            
            response = requests.get(original_url, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as img_file:
                img_file.write(response.content)
            
            book_copy = book.copy()
            book_copy['cover_image_url'] = f"/static/images/{filename}"
            updated_books.append(book_copy)
            
            print(f"  ✓ Downloaded: {filename}")
            
        except Exception as e:
            print(f"  ✗ Failed to download {original_url}: {e}")
            updated_books.append(book)
    
    with open(json_file, 'w') as f:
        json.dump(updated_books, f, indent=2)
    
    print(f"Updated {json_file} with local image paths")
    print(f"Downloaded images to {images_dir}")

if __name__ == "__main__":
    download_images()
