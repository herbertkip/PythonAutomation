import urllib.parse
import urllib.request
import re

def generate_folder_names(user_text, max_chars=45):
    """Generate folder names using Pollinations.AI (no API key needed)."""
    
    # Build the prompt
    prompt = (
        f"Create 5 short folder names under {max_chars} characters for: {user_text}. "
        f"Use only letters, numbers, spaces, hyphens. Return ONLY the names, one per line."
    )
    
    # URL-encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Pollinations.AI text endpoint - completely free, no key needed
    url = f"https://text.pollinations.ai/{encoded_prompt}"
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            result = response.read().decode('utf-8').strip()
        
        # Parse into clean list
        lines = result.split('\n')
        names = []
        for line in lines:
            # Remove common list markers
            cleaned = re.sub(r'^[\d\-\*\.\)\s]+', '', line).strip()
            if cleaned and len(cleaned) <= max_chars and cleaned not in names:
                names.append(cleaned)
        
        return names[:5]
    
    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    print("=" * 60)
    print("  Folder Name Generator (Pollinations.AI - no API key)")
    print("=" * 60)
    
    while True:
        user_input = input("\nEnter text (or 'q' to quit): ").strip()
        if user_input.lower() == 'q':
            break
        if not user_input:
            continue
        
        print("\nGenerating...")
        options = generate_folder_names(user_input)
        
        if options:
            print("\nOptions:")
            for i, name in enumerate(options, 1):
                print(f"  {i}. {name}  [{len(name)} chars]")
        else:
            print("No results. Try again.")

if __name__ == "__main__":
    main()