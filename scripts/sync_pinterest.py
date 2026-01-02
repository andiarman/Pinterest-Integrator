#!/usr/bin/env python3
"""
Pinterest Sync Script
Fetches pins from Pinterest boards and updates library.json

Note: Pinterest doesn't have a public API, so this script uses web scraping
to fetch data from public boards. For production use, consider Pinterest's
official API if you have developer access.
"""

import json
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
import requests
from bs4 import BeautifulSoup

# ============================================
# Configuration
# ============================================
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
LIBRARY_PATH = PROJECT_ROOT / "data" / "library.json"

# Headers to mimic browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


# ============================================
# Data Classes
# ============================================
class PinData:
    """Represents a single Pinterest pin"""
    def __init__(
        self,
        pin_id: str,
        title: str,
        image_url: str,
        description: str = "",
        source_url: str = "",
        board: str = ""
    ):
        self.id = pin_id
        self.title = title
        self.image_url = image_url
        self.description = description
        self.source_url = source_url
        self.board = board
        self.tags = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "image_url": self.image_url,
            "tags": self.tags,
            "description": self.description,
            "source_url": self.source_url,
            "board": self.board
        }


# ============================================
# Pinterest Scraper
# ============================================
class PinterestScraper:
    """Scrapes public Pinterest boards for pin data"""
    
    def __init__(self, config: dict):
        self.config = config
        self.tag_mappings = config.get("tag_mappings", {})
        self.excluded_keywords = config.get("excluded_keywords", [])
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch_board(self, board_url: str, board_name: str) -> list[PinData]:
        """Fetch pins from a Pinterest board"""
        pins = []
        
        try:
            print(f"📌 Fetching board: {board_name}")
            print(f"   URL: {board_url}")
            
            # Try to fetch the board page
            response = self.session.get(board_url, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Pinterest uses JavaScript heavily, so we'll try to find
            # JSON data embedded in the page
            pins = self._extract_pins_from_html(soup, board_name, board_url)
            
            print(f"   ✅ Found {len(pins)} pins")
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error fetching board: {e}")
        except Exception as e:
            print(f"   ❌ Error processing board: {e}")
        
        return pins

    def _extract_pins_from_html(
        self, 
        soup: BeautifulSoup, 
        board_name: str,
        board_url: str
    ) -> list[PinData]:
        """Extract pin data from HTML"""
        pins = []
        
        # Try to find script tags with JSON data
        script_tags = soup.find_all("script", type="application/json")
        
        for script in script_tags:
            try:
                data = json.loads(script.string)
                extracted = self._parse_pinterest_json(data, board_name, board_url)
                pins.extend(extracted)
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Fallback: try to find image elements directly
        if not pins:
            pins = self._extract_from_images(soup, board_name, board_url)
        
        return pins

    def _parse_pinterest_json(
        self, 
        data: dict, 
        board_name: str,
        board_url: str
    ) -> list[PinData]:
        """Parse Pinterest's embedded JSON data"""
        pins = []
        
        # Pinterest's JSON structure varies, so we need to search recursively
        def search_pins(obj, depth=0):
            if depth > 10:  # Prevent infinite recursion
                return
            
            if isinstance(obj, dict):
                # Check if this looks like pin data
                if "images" in obj and "id" in obj:
                    pin = self._create_pin_from_dict(obj, board_name, board_url)
                    if pin:
                        pins.append(pin)
                else:
                    for value in obj.values():
                        search_pins(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    search_pins(item, depth + 1)
        
        search_pins(data)
        return pins

    def _create_pin_from_dict(
        self, 
        data: dict, 
        board_name: str,
        board_url: str
    ) -> Optional[PinData]:
        """Create PinData from a dictionary"""
        try:
            pin_id = data.get("id", "")
            if not pin_id:
                return None
            
            # Get title/description
            title = data.get("title", "") or data.get("grid_title", "") or ""
            description = data.get("description", "") or ""
            
            # Skip excluded content
            full_text = f"{title} {description}".lower()
            for keyword in self.excluded_keywords:
                if keyword.lower() in full_text:
                    return None
            
            # Get image URL
            images = data.get("images", {})
            image_url = ""
            
            # Try to get the best quality image
            for key in ["orig", "736x", "564x", "474x", "236x"]:
                if key in images:
                    image_url = images[key].get("url", "")
                    break
            
            if not image_url:
                return None
            
            # Create source URL
            source_url = f"https://pinterest.com/pin/{pin_id}"
            
            # Generate a clean title if missing
            if not title:
                title = self._generate_title(description, board_name)
            
            pin = PinData(
                pin_id=f"pin_{pin_id}",
                title=title[:100],  # Limit title length
                image_url=image_url,
                description=description[:200],  # Limit description
                source_url=source_url,
                board=board_name
            )
            
            # Get tags from Pinterest's native tags ONLY (no auto-generation)
            pin.tags = self._get_pinterest_tags(data)
            
            return pin
            
        except Exception:
            return None

    def _extract_from_images(
        self, 
        soup: BeautifulSoup, 
        board_name: str,
        board_url: str
    ) -> list[PinData]:
        """Fallback: extract from image elements"""
        pins = []
        
        # Find all images with Pinterest CDN URLs
        for img in soup.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "")
            
            if "pinimg.com" in src and alt:
                # Generate a unique ID from the URL
                pin_id = hashlib.md5(src.encode()).hexdigest()[:12]
                
                pin = PinData(
                    pin_id=f"pin_{pin_id}",
                    title=alt[:100],
                    image_url=src,
                    description=alt[:200],
                    source_url=board_url,
                    board=board_name
                )
                # No auto-generated tags for fallback - leave empty
                pin.tags = []
                pins.append(pin)
        
        return pins[:50]  # Limit to 50 pins

    def _generate_title(self, description: str, board_name: str) -> str:
        """Generate a title from description or board name"""
        if description:
            # Take first sentence or first 50 chars
            first_sentence = description.split(".")[0]
            return first_sentence[:50].strip()
        return f"Material dari {board_name}"

    def _get_pinterest_tags(self, data: dict) -> list[str]:
        """Get tags from Pinterest's native tag data ONLY - no auto-generation"""
        tags = []
        
        # Try different Pinterest tag fields
        # 1. Hashtags from pin
        hashtags = data.get("hashtags", [])
        if hashtags:
            for h in hashtags:
                tag = h.get("tag", "") if isinstance(h, dict) else str(h)
                if tag and tag not in tags:
                    tags.append(tag.lower().replace("#", ""))
        
        # 2. Pin join (Pinterest's tag system)
        pin_join = data.get("pin_join", {})
        if pin_join:
            annotations = pin_join.get("visual_annotation", [])
            for ann in annotations:
                if isinstance(ann, str) and ann not in tags:
                    tags.append(ann.lower())
        
        # 3. Pinner's custom tags
        pinner_tags = data.get("pinner_tags", [])
        if pinner_tags:
            for tag in pinner_tags:
                if isinstance(tag, str) and tag.lower() not in tags:
                    tags.append(tag.lower())
        
        # 4. Board section name as tag
        board_section = data.get("board_section", {})
        if board_section:
            section_name = board_section.get("name", "")
            if section_name and section_name.lower() not in tags:
                tags.append(section_name.lower())
        
        return tags[:5]  # Max 5 tags


# ============================================
# Library Manager
# ============================================
class LibraryManager:
    """Manages the library.json file"""
    
    def __init__(self, library_path: Path):
        self.library_path = library_path
        self.data = self._load_library()

    def _load_library(self) -> dict:
        """Load existing library.json or create new one"""
        if self.library_path.exists():
            try:
                with open(self.library_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        
        return {
            "materials": [],
            "boards": [],
            "last_sync": None
        }

    def update_materials(self, new_pins: list[PinData]) -> int:
        """Update library with new pins, returns count of new materials"""
        existing_ids = {m["id"] for m in self.data["materials"]}
        new_count = 0
        
        for pin in new_pins:
            if pin.id not in existing_ids:
                self.data["materials"].append(pin.to_dict())
                new_count += 1
            else:
                # Update existing material
                for i, m in enumerate(self.data["materials"]):
                    if m["id"] == pin.id:
                        self.data["materials"][i] = pin.to_dict()
                        break
        
        # Update boards list
        boards = list(set(m["board"] for m in self.data["materials"]))
        self.data["boards"] = sorted(boards)
        
        # Update sync time
        self.data["last_sync"] = datetime.now().isoformat()
        
        return new_count

    def save(self):
        """Save library to file"""
        self.library_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.library_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        
        print(f"\n💾 Library saved to: {self.library_path}")
        print(f"   Total materials: {len(self.data['materials'])}")
        print(f"   Boards: {len(self.data['boards'])}")


# ============================================
# Main Function
# ============================================
def main():
    print("=" * 50)
    print("🔄 Pinterest Sync Script")
    print("=" * 50)
    
    # Load configuration
    print("\n📋 Loading configuration...")
    
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        print(f"   ⚠️ Config not found at {CONFIG_PATH}")
        print("   Using default configuration")
        config = {
            "boards": [],
            "tag_mappings": {
                "kayu": ["wood", "timber", "jati", "teak"],
                "batik": ["batik", "pattern", "motif"],
                "batu": ["stone", "marble", "granite"]
            },
            "excluded_keywords": []
        }
    
    # Check for environment variable override
    env_boards = os.environ.get("PINTEREST_BOARDS")
    if env_boards:
        try:
            boards_from_env = json.loads(env_boards)
            if isinstance(boards_from_env, list):
                config["boards"] = [
                    {"name": f"Board {i+1}", "url": url} 
                    for i, url in enumerate(boards_from_env)
                ]
        except json.JSONDecodeError:
            pass
    
    boards = config.get("boards", [])
    
    if not boards:
        print("\n⚠️ No boards configured!")
        print("   Add boards to config.json or set PINTEREST_BOARDS environment variable")
        print("\n   Example config.json:")
        print('   {"boards": [{"name": "My Board", "url": "https://pinterest.com/user/board"}]}')
        
        # Demo mode: keep existing data
        print("\n🎭 Running in demo mode - keeping existing library.json")
        return
    
    # Initialize scraper and library manager
    scraper = PinterestScraper(config)
    library = LibraryManager(LIBRARY_PATH)
    
    # Fetch all boards
    all_pins = []
    print(f"\n🔍 Fetching {len(boards)} board(s)...")
    
    for board in boards:
        board_name = board.get("name", "Unknown Board")
        board_url = board.get("url", "")
        
        if board_url:
            pins = scraper.fetch_board(board_url, board_name)
            all_pins.extend(pins)
    
    # Update library
    if all_pins:
        new_count = library.update_materials(all_pins)
        library.save()
        print(f"\n✅ Sync complete!")
        print(f"   New materials added: {new_count}")
    else:
        print("\n⚠️ No pins found. Library unchanged.")
        print("   This might happen if:")
        print("   - The board URLs are incorrect")
        print("   - Pinterest is blocking the request")
        print("   - The boards are private")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
