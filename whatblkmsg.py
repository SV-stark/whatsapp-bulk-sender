import csv
import time
import random
import os
import sys
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# ════════════════ CONFIGURATION ════════════════
CSV_FILE = 'contacts.csv'
TEMPLATES = ['template1.md', 'template2.md', 'template3.md']
MIN_DELAY = 5  
MAX_DELAY = 15  
MAX_TYPING_DURATION = 12.0  # Seconds cap
# ═══════════════════════════════════════════════

def format_number(number):
    """
    Strips non-digits. 
    If 10 digits, adds '91'.
    """
    clean_number = ''.join(filter(str.isdigit, str(number)))
    if len(clean_number) == 10:
        clean_number = '91' + clean_number
    return clean_number

def show_progress_bar(current, total, bar_length=30):
    percent = float(current) * 100 / total
    arrow = '█' * int(percent / 100 * bar_length)
    spaces = '-' * (bar_length - len(arrow))
    print(f"   Progress: [{arrow}{spaces}] {int(percent)}%")

def check_template_health():
    print("📋 [Audit] Checking Template Speeds...")
    valid_templates = False
    for t in TEMPLATES:
        if os.path.exists(t):
            valid_templates = True
            with open(t, "r", encoding="utf-8") as f:
                content = f.read()
                length = len(content)
                chars_per_sec = length / MAX_TYPING_DURATION
                status = "✅ OK" if chars_per_sec <= 15 else "⚠️ FAST"
                print(f"   • {t}: {length} chars -> ~{chars_per_sec:.1f} chars/sec | {status}")
        else:
            print(f"   • {t}: ❌ FILE MISSING")
    
    if not valid_templates:
        print("\n❌ CRITICAL: No template files found!")
        sys.exit(1)
    print("═" * 50)

def type_one_bubble(driver, element, text):
    """
    Types the message with a self-correcting timer to ensure it strictly 
    adheres to MAX_TYPING_DURATION, regardless of message length.
    """
    length = len(text)
    if length == 0: return

    # 1. Calculate Target Duration
    # We use a cap: It will take MAX_TYPING_DURATION, unless the text is 
    # short (e.g., "Hi"), in which case it uses a natural speed (0.15s/char).
    target_duration = min(MAX_TYPING_DURATION, length * 0.15)
    
    start_time = time.time()
    lines = text.split('\n')
    chars_processed = 0

    for i, line in enumerate(lines):
        idx = 0
        while idx < len(line):
            # Check time status
            elapsed = time.time() - start_time
            progress = chars_processed / length
            expected_time = progress * target_duration

            # 2. Dynamic Chunking (The Speed Fix)
            # If we are falling behind (Selenium is too slow), type more chars at once
            if elapsed > expected_time + 1.0: # Critical lag (>1s behind)
                chunk_size = random.randint(3, 6) 
            elif elapsed > expected_time:     # Slight lag
                chunk_size = random.randint(2, 3)
            else:                             # On schedule
                chunk_size = 1 

            # Get the chunk and type it
            chunk = line[idx:idx+chunk_size]
            element.send_keys(chunk)
            
            # Update counters
            idx += len(chunk)
            chars_processed += len(chunk)

            # 3. Smart Sleep
            # Only sleep if we are AHEAD of schedule. 
            # If behind, we skip sleep to catch up.
            current_elapsed = time.time() - start_time
            target_timestamp = (chars_processed / length) * target_duration
            
            remaining_sleep = target_timestamp - current_elapsed
            if remaining_sleep > 0:
                time.sleep(remaining_sleep)

        # Handle Newline (Shift+Enter)
        if i < len(lines) - 1:
            ActionChains(driver).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
            chars_processed += 1
            # Brief pause for the DOM to react to the newline
            time.sleep(0.05)

def setup_stealth_driver():
    if os.name == 'nt':
        try:
            subprocess.run("taskkill /F /IM chrome.exe /T", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except: pass
    
    options = uc.ChromeOptions()
    profile_path = os.path.join(os.getcwd(), 'whatsapp_stealth_profile')
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    
    try:
        return uc.Chrome(options=options)
    except Exception as e:
        print(f"❌ Error initializing driver: {e}"); sys.exit(1)

def send_stealth_broadcast():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # ════════════ HEADER / CREDITS ════════════
    print("\n" + "═"*50)
    print("      WHATSAPP BULK MESSENGER v1.0")
    print("      Credits: S V Stark")
    print("      GitHub: https://github.com/SV-stark")
    print("═"*50 + "\n")
    # ══════════════════════════════════════════

    check_template_health()
    
    contacts = []
    try:
        with open(CSV_FILE, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:
                    contacts.append({
                        'name': row[0].strip(), 
                        'number': format_number(row[1])
                    })
    except FileNotFoundError:
        print("❌ contacts.csv not found!"); return

    driver = setup_stealth_driver()
    wait = WebDriverWait(driver, 60)
    
    print("\n   🚀 Starting Engine...")
    driver.get('https://web.whatsapp.com')

    print("   📷 Waiting for WhatsApp login...")
    wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')))
    print("   ✅ Connected!\n")

    total = len(contacts)

    for index, contact in enumerate(contacts, 1):
        name = contact['name']
        number = contact['number']
        
        # Select Template
        temp_file = random.choice(TEMPLATES)
        with open(temp_file, "r", encoding="utf-8") as f:
            message = f.read().replace("{name}", name)

        # UPDATED: Now shows Template Name in the log
        print(f"   [{index}/{total}] Sending to {name} ({number}) via {temp_file}... ", end="", flush=True)
        
        try:
            # 1. Search for Number
            search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
            search_box.clear()
            # Type number quickly (search doesn't need human typing)
            for ch in number:
                search_box.send_keys(ch)
                time.sleep(0.05) 
            
            time.sleep(1.5)
            search_box.send_keys(Keys.ENTER)
            
            # 2. Locate Message Box
            msg_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
            
            # 3. Type Message (One Bubble Logic)
            type_one_bubble(driver, msg_box, message)
            
            # 4. Send
            time.sleep(0.5)
            msg_box.send_keys(Keys.ENTER)
            
            print("✅ SENT")
            show_progress_bar(index, total)
            
            # 5. Cooldown
            if index < total:
                delay = random.randint(MIN_DELAY, MAX_DELAY)
                # Simple countdown on the same line to keep console clean
                for i in range(delay, 0, -1):
                    sys.stdout.write(f"\r   ⏳ Cooldown: {i}s... ")
                    sys.stdout.flush()
                    time.sleep(1)
                # Clear cooldown line
                sys.stdout.write("\r" + " "*30 + "\r")

        except Exception as e:
            print(f"❌ FAILED")
            print(f"      Reason: {e}")
            driver.get('https://web.whatsapp.com'); time.sleep(5)

    print("\n   🎉 Broadcast Finished.")
    driver.quit()

if __name__ == "__main__":
    send_stealth_broadcast()