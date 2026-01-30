import re
import math


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def find_palindromes(text: str, min_length: int = 3) -> list[str]:
    text_lower = text.lower()
    palindromes = []

    words = re.findall(r'\w+', text_lower)

    for word in words:
        if len(word) >= min_length and word == word[::-1]:
            palindromes.append(word)

        for i in range(len(word)):
            for j in range(i + min_length, len(word) + 1):
                substring = word[i:j]
                if substring == substring[::-1]:
                    palindromes.append(substring)

    return list(set(palindromes))


def contains_palindrome(text: str, min_length: int = 3) -> bool:
    return len(find_palindromes(text, min_length)) > 0
