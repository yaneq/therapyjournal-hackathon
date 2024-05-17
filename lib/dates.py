from datetime import datetime


def get_date_prefix(format: str = "%Y-%m-%d %H:%M") -> str:
    """
    Function returns the current date and time as a prefix to a prompt message.
    """
    date_string = datetime.today().strftime(format)

    return "Message sent at " + date_string + ": \n\n"
