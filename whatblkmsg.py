import csv
import time
import random
import os
import sys
import subprocess
import re
import urllib.parse
import json
import argparse
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Ensure Unicode characters (emojis) are printed properly in Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ════════════════ CONFIGURATION DEFAULTS ════════════════
CSV_FILE = 'contacts.csv'
TEMPLATES = ['template1.md', 'template2.md', 'template3.md']
STATE_FILE = 'broadcast_state.json'

# Safety delays (seconds)
MIN_DELAY = 25  
MAX_DELAY = 60  

# Rest break settings (to look like a real person)
REST_EVERY_N = 10         # Rest after sending N messages
REST_MIN_MINUTES = 3      # Min rest duration
REST_MAX_MINUTES = 7      # Max rest duration
# ════════════════════════════════════════════════════════

def parse_spintax(text):
    """
    Parses Spintax format: {word1|word2|word3} recursively.
    Example: "{Hello|Hi} {name}, {how are you|hope you're well}"
    """
    pattern = re.compile(r'{([^{}]+)}')
    while True:
        match = pattern.search(text)
        if not match:
            break
        choices = match.group(1).split('|')
        text = text.replace(match.group(0), random.choice(choices), 1)
    return text

def format_number(number):
    """Strips non-digits. If 10 digits, prepends '91'."""
    clean_number = ''.join(filter(str.isdigit, str(number)))
    if len(clean_number) == 10:
        clean_number = '91' + clean_number
    return clean_number

def show_progress_bar(current, total, bar_length=30):
    percent = float(current) * 100 / total
    arrow = '█' * int(percent / 100 * bar_length)
    spaces = '-' * (bar_length - len(arrow))
    print(f"   Progress: [{arrow}{spaces}] {int(percent)}%")

def load_contacts(csv_path):
    contacts = []
    if not os.path.exists(csv_path):
        print(f"❌ Error: Contacts file not found at {csv_path}")
        return contacts
    
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            sample = f.read(2048)
            f.seek(0)
            
            has_header = False
            try:
                has_header = csv.Sniffer().has_header(sample)
            except Exception:
                pass
                
            if has_header:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                name_col = None
                phone_col = None
                
                for field in fieldnames:
                    clean_field = field.strip().lower()
                    if 'name' in clean_field:
                        name_col = field
                    elif any(k in clean_field for k in ['phone', 'number', 'contact', 'mobile']):
                        phone_col = field
                
                # Default fallbacks if detection fails
                if not name_col:
                    name_col = fieldnames[0]
                if not phone_col:
                    phone_col = fieldnames[1] if len(fieldnames) > 1 else fieldnames[0]
                    
                for row in reader:
                    name = row.get(name_col, '').strip()
                    phone = row.get(phone_col, '').strip()
                    if phone:
                        contacts.append({
                            'name': name,
                            'number': format_number(phone),
                            'row_data': {k.strip(): v.strip() for k, v in row.items() if k}
                        })
            else:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        name = row[0].strip()
                        phone = row[1].strip()
                        contacts.append({
                            'name': name,
                            'number': format_number(phone),
                            'row_data': {'name': name, 'phone': phone}
                        })
    except Exception as e:
        print(f"❌ Error reading contacts CSV: {e}")
        
    return contacts

def load_state(state_file):
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                if "completed" not in state: state["completed"] = []
                if "failed" not in state: state["failed"] = []
                return state
        except Exception:
            pass
    return {"completed": [], "failed": []}

def save_state(state, state_file):
    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        print(f"⚠️ Error saving state: {e}")

def wait_for_chat_load(driver, timeout=35):
    """
    Waits for the message box to be editable OR for the 'invalid phone number' popup modal to appear.
    Returns (True, msg_box_element) if loaded successfully.
    Returns (False, None) if the number is invalid.
    """
    start_time = time.time()
    msg_box_xpath = '//div[@contenteditable="true"][@data-tab="10"] | //footer//div[@contenteditable="true"]'
    invalid_xpath = '//*[contains(text(), "Phone number shared via url is invalid") or contains(text(), "invalid number") or contains(text(), "URL is invalid")]'
    
    while time.time() - start_time < timeout:
        # 1. Check if message input box is loaded and active
        try:
            msg_boxes = driver.find_elements(By.XPATH, msg_box_xpath)
            if msg_boxes:
                active_box = msg_boxes[0]
                if active_box.is_displayed() and active_box.is_enabled():
                    return True, active_box
        except Exception:
            pass
            
        # 2. Check if the invalid phone number popup appeared
        try:
            invalid_popups = driver.find_elements(By.XPATH, invalid_xpath)
            if invalid_popups:
                # Find and click the 'OK' or 'Close' button to dismiss it
                ok_buttons = driver.find_elements(By.XPATH, '//button[contains(., "OK")] | //div[@role="button"][contains(., "OK")] | //button[contains(., "Close")] | //div[@role="button"][contains(., "Close")]')
                if ok_buttons:
                    try:
                        ok_buttons[0].click()
                    except Exception:
                        pass
                return False, None
        except Exception:
            pass
            
        time.sleep(0.5)
        
    raise TimeoutError("WhatsApp page took too long to respond (network slowdown or UI update).")

def type_one_bubble(driver, element, text):
    """
    Types the text character-by-character into the message box.
    Simulates typos (1.5% chance) and subsequent self-corrections.
    Adds organic delays between keystrokes and pauses at punctuation.
    """
    typo_map = {
        'a': 'qwsz', 'b': 'vghn', 'c': 'xdfv', 'd': 'ersfxc', 'e': 'wsdr',
        'f': 'rtgvcd', 'g': 'tyhbvf', 'h': 'yujnbg', 'i': 'ujko', 'j': 'uikmhg',
        'k': 'ijlm', 'l': 'okp', 'm': 'njk', 'n': 'bhjm', 'o': 'iklp',
        'p': 'ol', 'q': 'wa', 'r': 'edft', 's': 'wedxz', 't': 'rfgy',
        'u': 'yhji', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tghu', 'z': 'asx'
    }
    
    # Resolve Spintax before typing
    resolved_text = parse_spintax(text)
    
    lines = resolved_text.split('\n')
    for line_idx, line in enumerate(lines):
        for char in line:
            # 1. Simulate Typo
            if char.lower() in typo_map and random.random() < 0.015:
                wrong_char = random.choice(typo_map[char.lower()])
                if char.isupper():
                    wrong_char = wrong_char.upper()
                
                element.send_keys(wrong_char)
                time.sleep(random.uniform(0.12, 0.22))
                element.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.08, 0.18))
                
            # 2. Type correct character
            element.send_keys(char)
            
            # 3. Micro delay between keystrokes
            delay = random.uniform(0.04, 0.12)
            
            # 4. Sentence rhythm pauses
            if char in ['.', '!', '?']:
                delay += random.uniform(0.4, 0.8)
            elif char == ',':
                delay += random.uniform(0.2, 0.4)
            elif char == ' ':
                delay += random.uniform(0.04, 0.1)
                
            time.sleep(delay)
            
        # 5. Shift+Enter for newlines
        if line_idx < len(lines) - 1:
            ActionChains(driver).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
            time.sleep(random.uniform(0.2, 0.45))

def setup_stealth_driver():
    if os.name == 'nt':
        try:
            subprocess.run("taskkill /F /IM chrome.exe /T", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception:
            pass
            
    options = uc.ChromeOptions()
    profile_path = os.path.join(os.getcwd(), 'whatsapp_stealth_profile')
    options.add_argument(f"--user-data-dir={profile_path}")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    
    # Hide automation banners and signatures
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")
    
    try:
        driver = uc.Chrome(options=options)
        # Extra script injection to wipe webdriver property
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
        return driver
    except Exception as e:
        print(f"❌ Error initializing Chrome driver: {e}")
        print("💡 Make sure you don't have other Chrome windows using this profile open.")
        sys.exit(1)

def check_template_health():
    print("📋 [Audit] Checking Template Speeds...")
    valid_templates = False
    for t in TEMPLATES:
        if os.path.exists(t):
            valid_templates = True
            with open(t, "r", encoding="utf-8") as f:
                content = f.read()
                sample = parse_spintax(content)
                length = len(sample)
                # Estimate duration: average typing time + punctuation delays
                estimated_time = length * 0.08 + (sample.count('.') + sample.count('?') + sample.count('!')) * 0.6 + sample.count(',') * 0.3
                print(f"   • {t}: ~{length} chars -> Estimated typing: {estimated_time:.1f}s")
        else:
            print(f"   • {t}: ❌ FILE MISSING")
            
    if not valid_templates:
        print("\n❌ CRITICAL: No template files found!")
        sys.exit(1)
    print("═" * 50)

def send_stealth_broadcast():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # ════════════ HEADER / CREDITS ════════════
    print("\n" + "═"*50)
    print("    🛡️  WHATSAPP STEALTH BROADCAST ENGINE v2.5")
    print("      Credits: S V Stark (Upgraded to Ultra-Stealth)")
    print("      GitHub: https://github.com/SV-stark")
    print("═"*50 + "\n")
    # ══════════════════════════════════════════
    
    # Setup Argument Parser
    parser = argparse.ArgumentParser(description="WhatsApp Stealth Bulk Broadcaster")
    parser.add_argument('--contacts', default=CSV_FILE, help="Path to contacts CSV file")
    parser.add_argument('--reset-state', action='store_true', help="Clear sent history state before starting")
    parser.add_argument('--retry-failed', action='store_true', help="Retry previously failed numbers instead of skipping")
    parser.add_argument('--state-file', default=STATE_FILE, help="Path to state JSON tracking file")
    parser.add_argument('--min-delay', type=int, default=MIN_DELAY, help="Min delay between messages (seconds)")
    parser.add_argument('--max-delay', type=int, default=MAX_DELAY, help="Max delay between messages (seconds)")
    parser.add_argument('--rest-every', type=int, default=REST_EVERY_N, help="Messages before taking a rest break")
    parser.add_argument('--rest-min', type=int, default=REST_MIN_MINUTES, help="Min rest break (minutes)")
    parser.add_argument('--rest-max', type=int, default=REST_MAX_MINUTES, help="Max rest break (minutes)")
    parser.add_argument('--dry-run', action='store_true', help="Validate CSV, templates, and Spintax without launching browser")
    args = parser.parse_args()
    
    check_template_health()
    
    # Handle state reset
    if args.reset_state and not args.dry_run:
        if os.path.exists(args.state_file):
            os.remove(args.state_file)
            print(f"🔄 [State] Sent history in '{args.state_file}' has been reset.")
            
    state = load_state(args.state_file)
    
    # Load contacts
    contacts = load_contacts(args.contacts)
    if not contacts:
        print(f"❌ No valid contacts loaded from {args.contacts}. Exiting.")
        return
        
    total = len(contacts)
    print(f"📂 Loaded {total} contacts from {args.contacts}.")
    
    if args.dry_run:
        print("\n🔍 [Dry-Run] Simulating message generation (No browser will launch)...")
        for index, contact in enumerate(contacts, 1):
            name = contact['name']
            if not name or name.strip() == "":
                name = "{Friend|there|Sir/Madam}"
                contact['name'] = name
                for k in contact['row_data']:
                    if 'name' in k.lower():
                        contact['row_data'][k] = name
            number = contact['number']
            row_data = contact['row_data']
            
            temp_file = random.choice(TEMPLATES)
            try:
                with open(temp_file, "r", encoding="utf-8") as f:
                    template_content = f.read()
            except FileNotFoundError:
                print(f"⚠️ Template file {temp_file} missing. Skipping.")
                continue
                
            # Replace placeholders
            message = template_content
            for key, val in row_data.items():
                message = message.replace(f"{{{key}}}", val)
            message = message.replace("{name}", name)
            
            # Resolve Spintax
            message_final = parse_spintax(message)
            
            print(f"\n👉 [{index}/{total}] Dry-Run target: {contact['name']} ({number}) via {temp_file}")
            print(f"   --- Content Preview ---")
            for line in message_final.split('\n'):
                print(f"   | {line}")
            print(f"   -----------------------")
        print("\n✨ Dry-run complete. Everything looks healthy!")
        return

    # Filter or report state info
    already_sent = len(state["completed"])
    already_failed = len(state["failed"])
    print(f"📊 Historical state: {already_sent} sent successfully, {already_failed} failed.")
    
    if args.retry_failed:
        state["failed"] = []
        save_state(state, args.state_file)
        print("🔄 [State] Retrying all previously failed contacts.")
        
    driver = setup_stealth_driver()
    wait = WebDriverWait(driver, 60)
    
    print("\n   🚀 Launching WhatsApp Web...")
    driver.get('https://web.whatsapp.com')
    
    print("   📷 Please scan QR code if not logged in...")
    wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')))
    print("   ✅ Connected!\n")
    
    sent_this_session = 0
    
    for index, contact in enumerate(contacts, 1):
        name = contact['name']
        if not name or name.strip() == "":
            name = "{Friend|there|Sir/Madam}"
            contact['name'] = name
            for k in contact['row_data']:
                if 'name' in k.lower():
                    contact['row_data'][k] = name
            
        number = contact['number']
        row_data = contact['row_data']
        
        # Check if already processed
        if number in state["completed"]:
            print(f"   [{index}/{total}] Skipping {contact['name']} ({number}) -> Sent successfully.")
            continue
        if number in state["failed"]:
            print(f"   [{index}/{total}] Skipping {contact['name']} ({number}) -> Previously failed.")
            continue
            
        # Select Template randomly
        temp_file = random.choice(TEMPLATES)
        try:
            with open(temp_file, "r", encoding="utf-8") as f:
                template_content = f.read()
        except FileNotFoundError:
            print(f"⚠️ Template file {temp_file} missing. Skipping {contact['name']}.")
            continue
            
        # Replace placeholders dynamically
        message = template_content
        for key, val in row_data.items():
            message = message.replace(f"{{{key}}}", val)
        # Fallback for case-insensitive {name} or standard field
        message = message.replace("{name}", name)
        
        print(f"   [{index}/{total}] Contacting {contact['name']} ({number}) via {temp_file}... ", end="", flush=True)
        
        try:
            # 1. Navigate directly to direct WhatsApp URL
            url = f"https://web.whatsapp.com/send?phone={number}"
            driver.get(url)
            
            # Small grace period for DOM transition
            time.sleep(3)
            
            # 2. Wait for chat load or invalid popup
            chat_status, msg_box = wait_for_chat_load(driver, timeout=35)
            
            if not chat_status:
                print("❌ INVALID NUMBER")
                state["failed"].append(number)
                save_state(state, args.state_file)
                show_progress_bar(index, total)
                time.sleep(random.uniform(2, 5))
                continue
                
            # 3. Simulate Human Typing
            type_one_bubble(driver, msg_box, message)
            
            # 4. Final send check and action
            time.sleep(random.uniform(0.6, 1.2))
            msg_box.send_keys(Keys.ENTER)
            
            print("✅ SENT")
            state["completed"].append(number)
            save_state(state, args.state_file)
            sent_this_session += 1
            show_progress_bar(index, total)
            
            # 5. Smart Rest Breaks
            if sent_this_session > 0 and sent_this_session % args.rest_every == 0 and index < total:
                rest_duration = random.randint(args.rest_min * 60, args.rest_max * 60)
                print(f"\n☕ [Rest Break] Sent {sent_this_session} messages this session.")
                print(f"   Simulating human behavior (resting for {rest_duration // 60} minutes)...")
                for sec in range(rest_duration, 0, -1):
                    sys.stdout.write(f"\r   ⏳ Resuming in: {sec // 60}m {sec % 60}s... ")
                    sys.stdout.flush()
                    time.sleep(1)
                sys.stdout.write("\r" + " " * 45 + "\r")
                print("   🚀 Rest finished. Resuming broadcast...")
                
            # 6. Normal random delay between consecutive messages
            elif index < total:
                delay = random.randint(args.min_delay, args.max_delay)
                for sec in range(delay, 0, -1):
                    sys.stdout.write(f"\r   ⏳ Next message delay: {sec}s... ")
                    sys.stdout.flush()
                    time.sleep(1)
                sys.stdout.write("\r" + " " * 35 + "\r")
                
        except Exception as e:
            print("❌ FAILED")
            print(f"      Reason: {e}")
            state["failed"].append(number)
            save_state(state, args.state_file)
            # Re-initialize or reload WhatsApp base page to recover from crashes
            try:
                driver.get('https://web.whatsapp.com')
                time.sleep(5)
            except Exception:
                pass
                
    print("\n   🎉 Stealth Broadcast Finished.")
    driver.quit()

if __name__ == "__main__":
    send_stealth_broadcast()