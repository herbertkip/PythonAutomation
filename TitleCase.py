def to_title_case(text):
    """
    Convert text to Title Case.
    First letter of each word is capitalized, rest is lowercase.
    """
    return text.title()


def to_title_case_smart(text):
    """
    Smarter Title Case conversion that:
    - Handles apostrophes correctly (e.g., "don't" -> "Don't", not "Don'T")
    - Handles hyphens correctly (e.g., "well-known" -> "Well-Known")
    - Preserves existing uppercase for acronyms is NOT done here (see smart_title)
    """
    import re
    # Capitalize first letter of each word, lowercase the rest,
    # but handle apostrophes: letter after ' stays lowercase.
    def capitalize_word(match):
        word = match.group(0)
        return word[0].upper() + word[1:].lower()
    
    # Match word boundaries but keep apostrophe-connected letters together
    return re.sub(r"\b[A-Za-z][A-Za-z']*", capitalize_word, text)


def smart_title(text):
    """
    Even smarter Title Case that keeps common small words lowercase
    (unless they're the first or last word).
    """
    small_words = {
        'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in', 'nor',
        'of', 'on', 'or', 'per', 'the', 'to', 'up', 'via', 'vs'
    }
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        lower_word = word.lower()
        is_first_or_last = (i == 0 or i == len(words) - 1)
        
        # Check if the word (ignoring punctuation) is a small word
        stripped = word.strip('.,;:!?"\'()[]{}')
        
        if stripped.lower() in small_words and not is_first_or_last:
            result.append(lower_word)
        else:
            # Capitalize first letter, keep rest lowercase
            # but preserve original case for things like "iPhone" is not handled
            result.append(word[0].upper() + word[1:].lower() if word else word)
    
    return ' '.join(result)


def main():
    print("=" * 50)
    print("  TEXT TO TITLE CASE CONVERTER")
    print("=" * 50)
    print()
    
    # Prompt for text
    text = input("Enter the text to convert: ")
    
    if not text.strip():
        print("\nNo text entered. Exiting.")
        return
    
    print("\n" + "-" * 50)
    print("RESULTS")
    print("-" * 50)
    
    # Option 1: Simple .title()
    print("\n[1] Standard Title Case (.title()):")
    print(f"    {to_title_case(text)}")
    
    # Option 2: Apostrophe-aware
    print("\n[2] Apostrophe-aware Title Case:")
    print(f"    {to_title_case_smart(text)}")
    
    # Option 3: Smart (keeps small words lowercase)
    print("\n[3] Smart Title Case (small words lowercase):")
    print(f"    {smart_title(text)}")
    
    print()


if __name__ == "__main__":
    main()