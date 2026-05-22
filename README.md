# WhatsApp Bulk Stealth Messenger

An advanced, human-simulating Python utility to send bulk WhatsApp messages using customizable message templates and contact lists, while evading automation tracking and account bans.

## Features

- **Direct URL Navigation**: Bypasses typing numbers in the WhatsApp Web search input (which has high bot signatures). Instead, loads chat streams directly via URLs.
- **Recursive Spintax Parsing**: Supports nested Spintax syntax, e.g., `{Hello|Hi} {name}, {hope all is well|how are you?}` to ensure every single sent message body is unique.
- **Advanced Human Typing Simulator**: Mimics human keypress rhythm, sentence pause rules at punctuation marks, and realistic spelling mistakes followed by backspace corrections.
- **Smart Breaks & Safety Delays**: Introduces customizable random delays between consecutive messages, along with longer periodic rest breaks (e.g. 5 minutes off after 10 messages) to reflect human fatigue.
- **Session Auto-Resume**: Tracks sent and failed numbers in a session JSON file. If stopped, restarts pick up exactly where you left off.
- **Dry-Run Mode**: Safely test template parsing, CSV parameters, and Spintax outputs locally in the console without opening Chromium or sending actual messages.
- **Auto Name Fallback**: Missing contact names automatically map to dynamic fallbacks (e.g., `{Friend|there|Sir/Madam}`).

---

## Requirements

- Python 3.8+
- Dependencies: `undetected-chromedriver`, `selenium`

Install requirements:
```bash
pip install -r requirements.txt
```

---

## Configuration

### 1. Templates
Place your markdown template files (e.g., `template1.md`, `template2.md`, `template3.md`) in the project directory. You can use standard field placeholders (from your CSV column headers) as well as Spintax options:

Example template:
```markdown
{Hello|Hi|Hey} {name},
{Just wanted to check in|Hope you are having a wonderful day}!
This is a quick notification about {event} happening at {location}.
{Cheers|Best regards},
Your Team
```

### 2. Contacts List (`contacts.csv`)
Create a `contacts.csv` file. The tool automatically detects column headers. Keep a name column and a contact/phone/mobile number column:

Example CSV:
```csv
name,phone,event,location
John Doe,1234567890,Annual Gala,New York
Jane Smith,9876543210,Tech Meetup,San Francisco
,5551234567,Secret Seminar,Miami
```
*Note: If names are missing, they automatically fallback to dynamic greetings.*

---

## Usage

### Sanity & Verification (Dry-Run)
Validate your setup, CSV columns, and Spintax syntax generation in the terminal without opening Chrome or sending messages:
```bash
python whatblkmsg.py --dry-run
```

### Run Broadcast
Start sending messages with default stealth configurations (25s–60s randomized delay, rest every 10 messages):
```bash
python whatblkmsg.py
```

### Advanced Options
You can configure safety delays, rest breaks, and state files directly from the CLI:

```bash
python whatblkmsg.py \
  --contacts my_list.csv \
  --min-delay 30 \
  --max-delay 75 \
  --rest-every 15 \
  --rest-min 5 \
  --rest-max 12 \
  --state-file custom_campaign.json
```

### Command Flags

| Flag | Default | Description |
|---|---|---|
| `--contacts` | `contacts.csv` | Path to your contacts list CSV file. |
| `--dry-run` | `False` | Run campaign validation and print preview messages in console. |
| `--reset-state` | `False` | Wipe out the session history to restart the campaign from index 1. |
| `--retry-failed` | `False` | Retry contacting previously failed numbers. |
| `--state-file` | `broadcast_state.json` | Path to store state progress tracker. |
| `--min-delay` | `25` | Minimum random delay between messages (seconds). |
| `--max-delay` | `60` | Maximum random delay between messages (seconds). |
| `--rest-every` | `10` | Frequency of periodic breaks (messages sent). |
| `--rest-min` | `3` | Minimum break duration (minutes). |
| `--rest-max` | `7` | Maximum break duration (minutes). |

---

## Security & Best Practices

1. **Avoid Spam Reports**: Always message people who have opted-in. If users report/block your account, WhatsApp's automated filters will ban the number, regardless of browser stealth.
2. **Warm-Up Your Number**: Do not send bulk campaigns from brand new numbers. Start with 5-10 messages per day, build history, and gradually scale up.
3. **Session Privacy**: The tool creates a local profile `whatsapp_stealth_profile/` to persist your WhatsApp Web logins. **This folder has been added to `.gitignore`**. Never upload this directory to public Git platforms as it contains your private browser authentication data.

---

## License

This project is licensed under the Mozilla Public License 2.0 — see the `LICENSE` file for details.
