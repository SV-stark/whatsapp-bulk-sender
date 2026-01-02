# whatsapp-bulk-sender

A small Python utility to send WhatsApp messages in bulk using message templates and a contact list. This repository contains the main script (whatblkmsg.py), a few example templates, and a requirements file. Use this README as a starting point — edit the usage examples to match the script's actual command-line options if needed.

## Features
- Send templated WhatsApp messages to many contacts
- Support for multiple message templates (template1.md, template2.md, …)
- Simple CSV contact import
- Configurable sending pace and basic logging

## Requirements
- Python 3.8+
- See requirements.txt for Python package dependencies

## Installation
1. Clone the repository:
   git clone https://github.com/SV-stark/whatsapp-bulk-sender.git
2. Change into the project directory:
   cd whatsapp-bulk-sender
3. (Optional) Create and activate a virtual environment:
   python -m venv .venv
   source .venv/bin/activate  # macOS / Linux
   .\.venv\Scripts\activate   # Windows
4. Install dependencies:
   pip install -r requirements.txt

## Configuration
- Templates: Edit the markdown files (template1.md, template2.md, etc.) to set the message content. Use placeholders for personalization, e.g.:
  Hello {name}, this is a quick message about {event}.
- Contacts: Provide contacts in a CSV file (example: contacts.csv) with at minimum a phone column. Example CSV columns:
  phone,name,email
  15551234567,John Doe,john@example.com
- Script options: The usage below shows common/typical options — adjust to match the actual flags in whatblkmsg.py.

## Usage (example)
Basic example (adjust flags to match the script):
python whatblkmsg.py --contacts contacts.csv --template template1.md --delay 2 --log sent.log

Example with inline options:
- --contacts / -c : path to CSV with contacts
- --template / -t : path to message template file
- --delay / -d : seconds delay between messages (to avoid rate limits)
- --headless : run browser in headless mode (if using a browser automation approach)
- --log : path to a log file for sent/failed entries

Example CSV (contacts.csv):
phone,name
15551234567,John Doe
15559876543,Jane Smith

Example template (template1.md):
Hello {name},

This is a message about our upcoming event. Please reply if you can attend.

Regards,
Your Name

Note: If the tool relies on a browser automation library (e.g., selenium) or a web-based WhatsApp session, you may need to scan the QR code once and keep that session profile available.

## Safety & Rate Limits
- Use responsibly. Avoid sending unsolicited messages or spam.
- Respect WhatsApp terms of service and local regulations.
- Use sensible delays between messages and consider batching.

## Troubleshooting
- If messages are not sending, check that:
  - The WhatsApp session is active (if using a logged-in browser profile).
  - The phone numbers are in the correct international format.
  - Required dependencies from requirements.txt are installed.
- Check the script log (if available) for per-contact errors.

## Development
- Edit templates and test locally before running on large lists.
- Add unit tests or dry-run mode to verify output without sending messages.
- Consider adding retry logic, concurrency controls, and better error handling.

## Contributing
Contributions, bug reports, and pull requests are welcome. Please open an issue or submit a PR with a clear description of the change.

## License
This project is licensed under the Mozilla Public License 2.0 — see the LICENSE file for details.
