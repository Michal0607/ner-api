import re
import json
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(current_dir, '..', 'data', 'time_words.json')

with open(json_file_path, 'r', encoding='utf-8') as f:
    time_words = json.load(f)

hours_dict = time_words['hours']
minutes_dict = time_words['minutes']
modifiers = time_words['modifiers']

def extract_dates_with_positions(text):
    date_pattern = r"\b\d{1,2}\s+(stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia)\s+\d{4}\b"
    matches = re.finditer(date_pattern, text, re.IGNORECASE)
    results = []
    for match in matches:
        results.append({
            "date": match.group(0),
            "start": match.start(),
            "stop": match.end(),
        })
    return results

def extract_pesel_with_positions(text):
    results = []
    pattern = r"\b\d{11}\b"
    matches = re.finditer(pattern, text)
    for match in matches:
        pesel = match.group()
        if validate_pesel(pesel):
            results.append({
                "pesel": pesel,
                "start": match.start(),
                "stop": match.end(),
            })
    return results

def extract_time(text):
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
                if 'wpół do' in match.group(0).lower():
                    minute = 30
                    hour = (hour - 1) % 24
                elif 'za' in match.group(0).lower() and minute_word:
                    minute_value = minutes_dict.get(minute_word)
                    if minute_value is not None:
                        minute = 60 - minute_value
                elif 'po' in match.group(0).lower() and minute_word:
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
                    time_formatted = f"{hour:02d}:{minute:02d}"
                    results.append({
                        "time": time_formatted,
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

def validate_pesel(pesel):
    if len(pesel) != 11 or not pesel.isdigit():
        return False
    weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    checksum = sum(w * int(p) for w, p in zip(weights, pesel[:-1])) % 10
    checksum = (10 - checksum) % 10
    return checksum == int(pesel[-1])