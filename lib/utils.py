import re


def remove_command_string(text):
    return re.sub(r"\/\S+ ", "", text)


def parse_multiple_choice(text):
    # Find text between <multiple-choice> and </multiple-choice> tags
    match = re.search(r"<multiple-choice>(.*?)</multiple-choice>", text, re.DOTALL)
    if match:
        content = match.group(1)
        # Find all instances of text within square brackets
        answers = re.findall(r"\[(.*?)\]", content)
        return answers
    else:
        return []


def purge_multiple_choice(text):
    # Remove text between <multiple-choice> and </multiple-choice> tags
    text = re.sub(
        r"<multiple-choice>(.*?)</multiple-choice>", "", text, flags=re.DOTALL
    )
    return text
