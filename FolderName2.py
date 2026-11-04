from freellama import FreeLlama

# The model to use (fast is usually sufficient for this task)
bot = FreeLlama(mode="fast")

def generate_folder_names(user_text, max_chars=45):
    """Generates folder name ideas using a free LLM service."""
    
    system_prompt = (
        f"You are a helpful assistant that creates concise, descriptive folder names. "
        f"Your task is to generate 5 folder name options based on the provided text. "
        f"Each folder name MUST be under {max_chars} characters. "
        f"Use only letters, numbers, spaces, hyphens, and underscores. "
        f"Return ONLY the list of names, each on a new line. Do not include numbering or bullet points."
    )
    
    # Combine system prompt and user input into a single message for the free client
    full_prompt = f"{system_prompt}\n\nText: {user_text}\n\nFolder names:"
    
    try:
        # The freellama .ask() method sends the prompt and returns the response
        response_text = bot.ask(full_prompt)
        
        # Clean up the response into a list
        lines = response_text.strip().split('\n')
        folder_names = []
        
        for line in lines:
            # Remove common list markers and extra whitespace
            cleaned = line.strip().lstrip('0123456789.-*) ').strip()
            # Enforce the character limit as a safety check
            if cleaned and len(cleaned) <= max_chars:
                folder_names.append(cleaned)
        
        return folder_names[:5]  # Return a maximum of 5 names

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def main():
    print("=" * 60)
    print("  Free AI Folder Name Generator (max 45 chars)")
    print("=" * 60)
    print("Paste your text and press Enter.\n")
    
    while True:
        user_input = input("> ").strip()
        
        if not user_input:
            print("[!] No input provided. Exiting.")
            break
        
        print("\nThinking...")
        options = generate_folder_names(user_input)
        
        if not options:
            print("\nCould not generate folder names. The service might be busy or the response format was unexpected.")
        else:
            print("\n" + "=" * 60)
            print("  Generated Folder Names:")
            print("=" * 60)
            
            for i, name in enumerate(options, 1):
                status = "✓" if len(name) <= 45 else "✗ OVER LIMIT"
                print(f"  {i}. {name}  [{len(name)} chars] {status}")
            
            print("=" * 60)
        
        again = input("\nGenerate for another text? (y/n): ").strip().lower()
        if again != 'y':
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()