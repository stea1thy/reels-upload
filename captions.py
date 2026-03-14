import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from replit import db
import json
import tempfile

username = os.getenv('INSTAGRAM_USERNAME')
password = os.getenv('INSTAGRAM_PASSWORD')

if not username or not password:
    print("ERROR: Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in Secrets")
    exit(1)

reels_folder = "reels"

if not os.path.exists(reels_folder):
    os.makedirs(reels_folder)
    print(f"Created {reels_folder} folder. Please upload your .mp4 videos to this folder.")
    exit(0)

hashtags = [
    "fypdrop", "sorawave", "neuronrot", "visionflux", "neural", "oddcore",
    "alphasigma", "npczone", "hallucinated", "remixcore", "skibidisky", "ohiorot",
    "mindset", "gyatty", "fanumburst", "spedmode", "viralwave", "synthcore",
    "aurahex", "oddwave", "sorarealm", "realtype", "goobified", "altvibes",
    "editwave", "brainmelter", "scrollshock", "crine", "brainzoned", "tuff",
    "son", "raw", "sigmamode", "rotshift", "webcore", "glassmode", "jawline",
    "rizzpulse", "goonmode", "goobling", "drainer", "drainwave", "ultrareal",
    "fanumrise", "sigmaflow", "ohioglitch", "brainlock", "randomized", "spededit",
    "cursedit", "hyperrealism", "lofirot", "trendedit", "glitchline", "soraglitch",
    "rottokyo", "mewsnap", "sorabeat", "dreamvibe", "surrealist", "rotshift2",
    "oddedit", "nonsensical", "reelboost", "viralfeed", "editloop", "memeflow",
    "npcglitch", "chroniconline", "rotshiftx", "illusioned", "scrollwave",
    "brainbuzz", "sigmawar", "npcenergy", "webnet", "rotstorm", "psychrot",
    "wavecore", "realmworld", "violetcore", "soradream", "soraverse2", "flickerfx",
    "digitalvoid", "sorarized", "unrealsnap", "trendcore", "pushflow", "sorarun",
    "mindwarp", "soraskin", "glitchphase", "dreamfracture", "packdrop", "rotsnap"
]

def setup_stealth_driver():
    """Sets up a Chrome driver with anti-detection settings"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')

    # IMPORTANT: Comment out headless for reCAPTCHA
    # chrome_options.add_argument('--headless=new')

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument('--window-size=1920,1080')

    # Realistic settings
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')

    # User agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        print("Starting Chrome browser...", flush=True)
        service = Service()

        # Use temp directory for fresh profile
        temp_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f'--user-data-dir={temp_dir}')

        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Stealth scripts
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
            '''
        })

        print("Browser ready!", flush=True)
        return driver
    except Exception as e:
        print(f"Failed to start Chrome: {e}", flush=True)
        return None

def save_session_cookies(driver):
    """Save session cookies"""
    try:
        cookies = driver.get_cookies()
        db["instagram_cookies"] = json.dumps(cookies)
        db["instagram_username"] = username
        print("✓ Session saved")
    except Exception as e:
        print(f"⚠️ Could not save cookies: {e}")

def load_session_cookies(driver):
    """Load session cookies"""
    try:
        if "instagram_cookies" in db and "instagram_username" in db:
            if db["instagram_username"] == username:
                cookies = json.loads(db["instagram_cookies"])
                for cookie in cookies:
                    driver.add_cookie(cookie)
                print("✓ Loaded session")
                return True
    except Exception as e:
        print(f"⚠️ Could not load cookies: {e}")
    return False

def handle_post_login_prompts(driver):
    """Handle post-login prompts"""
    prompts = [
        ("//button[contains(text(), 'Not Now')]", "Save Info"),
        ("//button[contains(text(), 'Not now')]", "Save Info"),
    ]
    for xpath, prompt_name in prompts:
        try:
            button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            button.click()
            print(f"✓ Dismissed {prompt_name}")
            time.sleep(1)
        except:
            continue

def wait_for_login_form(driver, timeout=10):
    """Wait for login form to appear after clicking login button"""
    print("⏳ Waiting for login form...", flush=True)
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check for various login form indicators
        login_form_indicators = [
            "//input[@name='username']",
            "//input[@name='password']",
            "//form[contains(@class, 'login')]",
            "//div[contains(@class, 'login-form')]",
            "//h1[contains(text(), 'Log in')]",
        ]

        for indicator in login_form_indicators:
            try:
                element = driver.find_element(By.XPATH, indicator)
                if element.is_displayed():
                    print(f"✓ Login form appeared: {indicator}", flush=True)
                    return True
            except:
                continue

        time.sleep(0.5)

    print("❌ Login form didn't appear", flush=True)
    return False

def find_login_fields(driver):
    """Find username and password fields with multiple strategies"""
    print("🔍 Looking for login fields...", flush=True)

    # STRATEGY 1: Modern Instagram login form
    username_selectors = [
        (By.XPATH, "//input[@name='username']"),
        (By.XPATH, "//input[@aria-label='Phone number, username, or email']"),
        (By.XPATH, "//input[@placeholder='Phone number, username, or email']"),
        (By.NAME, "username"),
        (By.XPATH, "//input[@type='text' and contains(@class, 'input')]"),
    ]

    password_selectors = [
        (By.XPATH, "//input[@name='password']"),
        (By.XPATH, "//input[@type='password']"),
        (By.XPATH, "//input[@aria-label='Password']"),
        (By.NAME, "password"),
    ]

    # Try each username selector
    username_field = None
    for by, selector in username_selectors:
        try:
            username_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((by, selector))
            )
            print(f"✓ Found username: {selector}", flush=True)
            break
        except:
            continue

    # If not found, try to find ANY input that could be username
    if not username_field:
        print("⚠️ Trying alternative username search...", flush=True)
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in all_inputs:
            inp_type = inp.get_attribute("type")
            inp_name = inp.get_attribute("name")
            placeholder = inp.get_attribute("placeholder") or ""

            if (inp_type == "text" and 
                (inp_name == "username" or 
                 "phone" in placeholder.lower() or 
                 "username" in placeholder.lower() or 
                 "email" in placeholder.lower())):
                username_field = inp
                print("✓ Found username by scanning inputs", flush=True)
                break

    # Find password field
    password_field = None
    for by, selector in password_selectors:
        try:
            password_field = driver.find_element(by, selector)
            print(f"✓ Found password: {selector}", flush=True)
            break
        except:
            continue

    # If password not found, look for password input
    if not password_field:
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in all_inputs:
            if inp.get_attribute("type") == "password":
                password_field = inp
                print("✓ Found password by scanning", flush=True)
                break

    return username_field, password_field

def login_to_instagram(driver):
    """Complete login process with better form handling"""
    print("🔐 Starting login...", flush=True)

    # Go to Instagram
    driver.get("https://www.instagram.com")
    time.sleep(random.uniform(3, 5))

    # Save initial page
    driver.save_screenshot("instagram_home.png")

    # STEP 1: Find and click login button
    login_found = False
    login_selectors = [
        "//a[@href='/accounts/login/']",
        "//button[contains(text(), 'Log in')]",
        "//span[contains(text(), 'Log in')]",
        "//div[contains(text(), 'Log in')]",
        "//*[contains(text(), 'Log in') and @role='button']",
    ]

    for selector in login_selectors:
        try:
            login_btn = driver.find_element(By.XPATH, selector)
            print(f"✓ Found login button: {selector}", flush=True)

            # Click with human-like pause
            ActionChains(driver).move_to_element(login_btn).pause(0.5).click().perform()
            login_found = True
            time.sleep(random.uniform(2, 4))
            break
        except:
            continue

    if not login_found:
        print("⚠️ No login button found, trying direct URL...", flush=True)
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(random.uniform(3, 5))

    # Save login page
    driver.save_screenshot("login_page.png")

    # STEP 2: Wait for login form
    if not wait_for_login_form(driver):
        # Maybe we're already on login page
        print("Checking if already on login form...", flush=True)

    # STEP 3: Find login fields
    username_field, password_field = find_login_fields(driver)

    if not username_field or not password_field:
        print("❌ Could not find login fields", flush=True)
        # Save page for debugging
        with open("login_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("📄 Saved page source to login_debug.html", flush=True)
        return False

    # STEP 4: Fill credentials
    print("⌨️ Typing username...", flush=True)
    username_field.click()
    time.sleep(0.3)
    username_field.clear()

    for i, char in enumerate(username):
        username_field.send_keys(char)
        if i < 3:
            time.sleep(random.uniform(0.05, 0.1))
        elif i > len(username) - 3:
            time.sleep(random.uniform(0.2, 0.3))
        else:
            time.sleep(random.uniform(0.1, 0.2))

    time.sleep(random.uniform(1, 2))

    print("⌨️ Typing password...", flush=True)
    password_field.click()
    time.sleep(0.3)
    password_field.clear()

    for i, char in enumerate(password):
        password_field.send_keys(char)
        if i < 2:
            time.sleep(random.uniform(0.05, 0.1))
        elif i > len(password) - 2:
            time.sleep(random.uniform(0.2, 0.3))
        else:
            time.sleep(random.uniform(0.1, 0.2))

    time.sleep(random.uniform(1, 2))

    # STEP 5: Find and click submit
    submit_selectors = [
        "//button[@type='submit']",
        "//button[contains(text(), 'Log in')]",
        "//div[contains(text(), 'Log in') and @role='button']",
    ]

    submit_button = None
    for selector in submit_selectors:
        try:
            submit_button = driver.find_element(By.XPATH, selector)
            print(f"✓ Found submit button", flush=True)
            break
        except:
            continue

    if submit_button:
        submit_button.click()
        print("✓ Submitted login", flush=True)
    else:
        password_field.send_keys(Keys.RETURN)
        print("✓ Submitted with Enter", flush=True)

    # STEP 6: Wait and handle challenges
    print("⏳ Waiting for login response...", flush=True)
    time.sleep(random.uniform(5, 8))

    # Save state after login attempt
    driver.save_screenshot("after_login_attempt.png")

    # Check for reCAPTCHA challenge
    if "/challenge/" in driver.current_url:
        print("⚠️ Security challenge detected!", flush=True)
        return handle_recaptcha_challenge(driver)

    # STEP 7: Handle post-login prompts
    handle_post_login_prompts(driver)

    # STEP 8: Verify login
    time.sleep(3)

    # Check multiple success indicators
    success_indicators = [
        "//nav",
        "//a[@href='/']",
        "//div[@role='navigation']",
        "//input[@placeholder='Search']",
    ]

    for indicator in success_indicators:
        try:
            driver.find_element(By.XPATH, indicator)
            print(f"✓ Logged in! Found: {indicator}", flush=True)
            save_session_cookies(driver)
            return True
        except:
            continue

    # Also check URL
    if "login" not in driver.current_url and "challenge" not in driver.current_url:
        print(f"✓ Likely logged in. URL: {driver.current_url[:80]}...", flush=True)
        save_session_cookies(driver)
        return True

    print("❌ Login verification failed", flush=True)
    return False

def handle_recaptcha_challenge(driver):
    """Handle the reCAPTCHA challenge"""
    print("🛡️ Attempting to solve reCAPTCHA...", flush=True)
    driver.save_screenshot("recaptcha_page.png")

    try:
        # Look for the checkbox in your screenshot
        # From your image: "I'm not a robot" checkbox

        # Try multiple checkbox selectors
        checkbox_selectors = [
            "//div[@role='checkbox']",
            "//div[contains(text(), 'not a robot')]",
            "//label[contains(text(), 'not a robot')]",
            "//span[contains(text(), 'not a robot')]",
            "//input[@type='checkbox']",
        ]

        for selector in checkbox_selectors:
            try:
                checkbox = driver.find_element(By.XPATH, selector)
                print(f"✓ Found checkbox: {selector}", flush=True)

                # Click it
                checkbox.click()
                print("✓ Clicked checkbox", flush=True)

                # Wait for response
                time.sleep(random.uniform(3, 5))

                # Check if solved
                if "/challenge/" not in driver.current_url:
                    print("✅ reCAPTCHA solved!", flush=True)
                    return True
                break
            except:
                continue

        # If still on challenge, try clicking anywhere in the challenge area
        print("⚠️ Trying alternative click...", flush=True)
        try:
            # Click in the middle of the viewport (where checkbox likely is)
            actions = ActionChains(driver)
            actions.move_by_offset(200, 300).click().perform()
            time.sleep(3)

            if "/challenge/" not in driver.current_url:
                print("✅ Challenge bypassed!", flush=True)
                return True
        except:
            pass

        print("❌ Could not solve reCAPTCHA automatically", flush=True)
        return False

    except Exception as e:
        print(f"❌ Error with reCAPTCHA: {e}", flush=True)
        return False

def upload_reel(driver, video_path):
    """Upload a reel"""
    try:
        caption = f"@buubbees\n\n"
        selected_hashtags = random.sample(hashtags, k=min(len(hashtags), 5))
        caption += ' '.join(['#' + tag for tag in selected_hashtags])

        print(f"  Caption: {caption[:50]}...")

        upload_delay = random.uniform(1.5, 4.0)
        print(f"  Waiting {upload_delay:.1f}s...")
        time.sleep(upload_delay)

        driver.get("https://www.instagram.com")
        time.sleep(random.uniform(2, 4))

        # Try to find create button
        try:
            create_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//div[@role='button']//*[local-name()='svg' and @aria-label='New post'] | "
                    "//div[text()='Create'] | "
                    "//button[contains(@class, '_acan')]"
                ))
            )
            create_btn.click()
        except:
            driver.get("https://www.instagram.com/create/select/")

        time.sleep(random.uniform(2, 4))

        # Upload file
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        file_input.send_keys(os.path.abspath(video_path))

        print(f"  Uploading...")
        time.sleep(random.uniform(5, 8))

        # Click through steps
        next_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
        )
        next_btn.click()
        time.sleep(2)

        next_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
        )
        next_btn.click()
        time.sleep(2)

        # Add caption
        caption_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, 
                "//div[@role='textbox'] | "
                "//textarea[@aria-label='Write a caption…']"
            ))
        )

        caption_area.click()
        time.sleep(0.5)
        caption_area.send_keys(Keys.CONTROL + "a")
        caption_area.send_keys(Keys.DELETE)

        for char in caption:
            caption_area.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        time.sleep(1)

        # Share
        share_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Share')]"))
        )
        share_btn.click()

        print(f"  Upload initiated")
        time.sleep(random.uniform(8, 12))

        return True

    except Exception as e:
        print(f"  Upload failed: {str(e)[:100]}...")
        driver.save_screenshot(f"upload_error_{int(time.time())}.png")
        return False

def delete_reel(video_path):
    """Delete video after upload"""
    try:
        os.remove(video_path)
        print(f"  Deleted {os.path.basename(video_path)}")
    except Exception as e:
        print(f"  Failed to delete: {e}")

def main():
    """Main function"""
    print("=" * 60)
    print("Instagram Reels Uploader")
    print("=" * 60)

    reels_files = sorted([f for f in os.listdir(reels_folder) if f.endswith(".mp4")])

    if not reels_files:
        print(f"No videos in {reels_folder}")
        return

    print(f"Found {len(reels_files)} video(s)")

    driver = setup_stealth_driver()
    if not driver:
        print("Failed to start browser")
        return

    try:
        # Try loading session
        driver.get("https://www.instagram.com")
        time.sleep(2)

        if load_session_cookies(driver):
            driver.refresh()
            time.sleep(3)
            try:
                driver.find_element(By.XPATH, "//nav")
                print("✅ Resumed session")
            except:
                print("Session expired")
                if not login_to_instagram(driver):
                    print("Login failed")
                    driver.quit()
                    return
        else:
            if not login_to_instagram(driver):
                print("Login failed")
                driver.quit()
                return

        # Upload videos
        for index, reel in enumerate(reels_files, start=1):
            reel_path = os.path.join(reels_folder, reel)
            print(f"\n[{index}/{len(reels_files)}] {reel}")

            if upload_reel(driver, reel_path):
                delete_reel(reel_path)
            else:
                wait = random.uniform(120, 300)
                print(f"  Waiting {wait:.1f}s...")
                time.sleep(wait)
                continue

            if index < len(reels_files):
                wait = random.uniform(45, 90)
                print(f"  Next in {wait:.1f}s...")
                time.sleep(wait)

        print("\n✅ Upload complete!")

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        try:
            driver.quit()
            print("Browser closed")
        except:
            pass

def keep_alive_server():
    """Keep Replit alive"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Bot running')

    server = HTTPServer(('0.0.0.0', 8080), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print("Keep-alive server started")

if __name__ == "__main__":
    keep_alive_server()
    main()
    time.sleep(3600)