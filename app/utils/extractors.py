import re
import json
import os
import dateparser

current_dir = os.path.dirname(os.path.abspath(__file__))

time_words_file = os.path.join(current_dir, '..', 'data', 'time_words.json')
with open(time_words_file, 'r', encoding='utf-8') as f:
    time_words = json.load(f)

hours_dict = time_words['hours']
minutes_dict = time_words['minutes']
modifiers = time_words['modifiers']

digits_file = os.path.join(current_dir, '..', 'data', 'digits.json')
with open(digits_file, 'r', encoding='utf-8') as f:
    digits_data = json.load(f)

HUNDREDS = digits_data["hundreds"]
TENS = digits_data["tens"]
ONES = digits_data["ones"]

POLISH_MONTH_REGEX = r"(sty|lut|mar|kwie|maj|cze|lip|sie|wrze|paź|paz|lis|gru)"

def validate_pesel(pesel: str):
    if len(pesel) != 11 or not pesel.isdigit():
        return False
    weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    checksum = sum(w * int(p) for w, p in zip(weights, pesel[:-1])) % 10
    checksum = (10 - checksum) % 10
    return checksum == int(pesel[-1])

def parse_up_to_999(token_list):
    number = 0
    for t in token_list:
        if t in HUNDREDS:
            number += HUNDREDS[t]
        elif t in TENS:
            number += TENS[t]
        elif t in ONES:
            number += ONES[t]
        else:
            if t.isdigit():
                val = int(t)
                if val <= 999:
                    number += val
                else:
                    return None
            else:
                return None
    if 0 <= number <= 999:
        return number
    return None

def parse_phone_candidate(fragment: str):
    lowered = fragment.lower()
    tokens = re.split(r"[^a-z0-9ąćęłńóśźż]+", lowered)
    tokens = [t for t in tokens if t]
    digit_chunks = []
    i = 0
    while i < len(tokens):
        parsed_ok = False
        for size in [3, 2, 1]:
            if i + size <= len(tokens):
                subset = tokens[i : i+size]
                value = parse_up_to_999(subset)
                if value is not None:
                    digit_chunks.append(str(value))
                    i += size
                    parsed_ok = True
                    break
        if not parsed_ok:
            if tokens[i].isdigit():
                digit_chunks.append(tokens[i])
                i += 1
            else:
                return None
    return "".join(digit_chunks)

def is_phone_number(digits: str) -> bool:
    if len(digits) == 11 and validate_pesel(digits):
        return False
    if len(digits) == 9:
        return True
    if len(digits) == 11 and digits.startswith("48"):
        return True
    return False

def extract_phone_with_positions(text: str):
    results = []

    phone_pattern = r"\+?\d[\d\s\-]{5,15}\d"
    for match in re.finditer(phone_pattern, text):
        original_fragment = match.group(0)
        digits = re.sub(r"[^\d]", "", original_fragment)
        if is_phone_number(digits):
            results.append({
                "phone": original_fragment,
                "start": match.start(),
                "stop": match.end()
            })

    pattern_complex = r"[a-z0-9\-\sąćęłńóśźż:\(\)\.,_/]{5,200}"
    for match in re.finditer(pattern_complex, text, flags=re.IGNORECASE):
        original_fragment = match.group(0)
        digits = parse_phone_candidate(original_fragment)
        if digits and is_phone_number(digits):
            duplicate = any(
                (r["phone"] == original_fragment and r["start"] == match.start() and r["stop"] == match.end())
                for r in results
            )
            if not duplicate:
                results.append({
                    "phone": original_fragment,
                    "start": match.start(),
                    "stop": match.end()
                })

    return results


def extract_dates_with_positions(text: str):

    results = []

    numeric_date_patterns = [r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b"]
    word_month_pattern = (
        r"\b(\d{1,2})\s+("
        r"styczeń|stycznia|lut|luty|lutego|marzec|marca|kwiecień|kwietnia|maj|maja|"
        r"czerwiec|czerwca|lipiec|lipca|sierpień|sierpnia|wrzesień|września|wrzesnia|"
        r"październik|pazdziernik|października|pazdziernika|listopad|listopada|"
        r"grudzień|grudnia"
        r")\s+(\d{4})\b"
    )
    all_patterns = numeric_date_patterns + [word_month_pattern]
    combined_pattern = r"|".join(f"({pat})" for pat in all_patterns)

    for match in re.finditer(combined_pattern, text, flags=re.IGNORECASE):
        fragment = match.group(0)

        parsed = dateparser.parse(fragment, languages=["pl"], settings={
            "DATE_ORDER": "DMY",
            "STRICT_PARSING": True,
            "REQUIRE_PARTS": ["year", "month", "day"]
        })
        if parsed and 1900 <= parsed.year <= 2100:
            results.append({
                "date": fragment,
                "start": match.start(),
                "stop": match.end()
            })

    extra_pattern = r"\b(\S+)\s+(\S+)\s+(\d{4})\b"
    for match in re.finditer(extra_pattern, text, flags=re.IGNORECASE):
        original_fragment = match.group(0)
        day_candidate = match.group(1)
        month_candidate = match.group(2)
        year_candidate = match.group(3)

        day_val = parse_day_or_month(day_candidate) 
        month_val = parse_day_or_month(month_candidate) 

        if not year_candidate.isdigit():
            continue
        year_val = int(year_candidate)

        if day_val and 1 <= day_val <= 31 and month_val and 1 <= month_val <= 12:
            if 1900 <= year_val <= 2100:
                results.append({
                    "date": original_fragment,
                    "start": match.start(),
                    "stop": match.end()
                })

    return results

def parse_day_or_month(fragment: str):
    
    lowered = fragment.lower()
    tokens = re.split(r"[^a-z0-9ąćęłńóśźż]+", lowered)
    tokens = [t for t in tokens if t]
    if not tokens:
        return None
    value = parse_up_to_999(tokens)
    return value

def extract_pesel_with_positions(text: str):
    results = []
    pure_pesel_pattern = r"\b(\d{11})\b"
    for match in re.finditer(pure_pesel_pattern, text):
        candidate = match.group(1)
        if validate_pesel(candidate):
            results.append({
                "pesel": candidate,
                "start": match.start(),
                "stop": match.end()
            })

    pattern_complex = r"[a-z0-9\-\sąćęłńóśźż:\(\)\.,_/]{10,200}"
    for match in re.finditer(pattern_complex, text, flags=re.IGNORECASE):
        fragment = match.group(0)
        candidate = parse_pesel_candidate(fragment)
        if candidate and validate_pesel(candidate):
            duplicate = any(
                (r["pesel"] == candidate and r["start"] == match.start() and r["stop"] == match.end())
                for r in results
            )
            if not duplicate:
                results.append({
                    "pesel": candidate,
                    "start": match.start(),
                    "stop": match.end()
                })
    return results

def parse_pesel_candidate(fragment: str):
    lowered = fragment.lower()
    tokens = re.split(r"[^a-z0-9ąćęłńóśźż]+", lowered)
    tokens = [t for t in tokens if t]

    digit_chunks = []
    for token in tokens:
        spelled_val = parse_up_to_999([token])
        if spelled_val is not None:
            digit_chunks.append(str(spelled_val))
            continue

        if token.isdigit() and len(token) <= 11:
            digit_chunks.append(token)
            continue

        return None

    combined = "".join(digit_chunks)
    if len(combined) == 11 and combined.isdigit():
        return combined
    return None


def extract_time(text: str):
    results = []
    time_patterns = [
        r'\b(?:o\s+godzin(?:ie|ą)\s+)?(?P<hour>(%s))\s+(?P<minute>(%s))(?:\s+(?P<modifier>(%s)))?\b' % (
            '|'.join(re.escape(k) for k in sorted(hours_dict.keys(), key=lambda x: -len(x))),
            '|'.join(re.escape(k) for k in sorted(minutes_dict.keys(), key=lambda x: -len(x))),
            '|'.join(re.escape(k) for k in modifiers.keys())
        ),
        r'\b(?:o\s+godzin(?:ie|ą)\s+)?(?P<hour>(%s))(?:\s+(?P<modifier>(%s)))?\b' % (
            '|'.join(re.escape(k) for k in sorted(hours_dict.keys(), key=lambda x: -len(x))),
            '|'.join(re.escape(k) for k in modifiers.keys())
        ),
        r'\b(?P<minute>(%s))\s+minut(?:a|y)?\s+po\s+(?P<hour>(%s))(?:\s+(?P<modifier>(%s)))?\b' % (
            '|'.join(re.escape(k) for k in sorted(minutes_dict.keys(), key=lambda x: -len(x))),
            '|'.join(re.escape(k) for k in sorted(hours_dict.keys(), key=lambda x: -len(x))),
            '|'.join(re.escape(k) for k in modifiers.keys())
        ),
        r'\bza\s+(?P<minute>(%s))\s+minut(?:a|y)?\s+(?P<hour>(%s))(?:\s+(?P<modifier>(%s)))?\b' % (
            '|'.join(re.escape(k) for k in sorted(minutes_dict.keys(), key=lambda x: -len(x))),
            '|'.join(re.escape(k) for k in sorted(hours_dict.keys(), key=lambda x: -len(x))),
            '|'.join(re.escape(k) for k in modifiers.keys())
        ),
        r'\bwpół\s+do\s+(?P<hour>(%s))(?:\s+(?P<modifier>(%s)))?\b' % (
            '|'.join(re.escape(k) for k in sorted(hours_dict.keys(), key=lambda x: -len(x))),
            '|'.join(re.escape(k) for k in modifiers.keys())
        ),
    ]
    for pattern in time_patterns:
        matches = re.finditer(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            hour_word = match.group('hour').lower() if match.groupdict().get('hour') else None
            minute_word = match.group('minute').lower() if match.groupdict().get('minute') else None
            modifier_word = match.group('modifier').lower() if match.groupdict().get('modifier') else None
            hour = hours_dict.get(hour_word) if hour_word else None
            minute = None
            if hour is not None:
                segment = match.group(0).lower()
                if 'wpół do' in segment:
                    minute = 30
                    hour = (hour - 1) % 24
                elif 'za' in segment and minute_word:
                    minute_value = minutes_dict.get(minute_word)
                    if minute_value is not None:
                        minute = 60 - minute_value
                elif 'po' in segment and minute_word:
                    minute_value = minutes_dict.get(minute_word)
                    if minute_value is not None:
                        minute = minute_value
                elif minute_word:
                    minute = minutes_dict.get(minute_word, 0)
                if modifier_word:
                    if modifiers[modifier_word] == 'PM' and hour < 12:
                        hour += 12
                    elif modifiers[modifier_word] == 'AM' and hour >= 12:
                        hour -= 12
                if hour is not None and minute is not None:
                    results.append({
                        "time": f"{hour:02d}:{minute:02d}",
                        "original": match.group(0),
                        "start": match.start(),
                        "stop": match.end(),
                    })

    time_pattern_numeric = r"""
        \b
        (?:[01]?\d|2[0-3])
        [.:]
        [0-5]\d
        (?:[.:][0-5]\d)?
        \b
    """
    matches = re.finditer(time_pattern_numeric, text, re.VERBOSE)
    for match in matches:
        results.append({
            "time": match.group(0),
            "start": match.start(),
            "stop": match.end(),
        })
    return results
