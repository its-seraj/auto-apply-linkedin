'''
Author:     Seraj Khan
LinkedIn:   https://www.linkedin.com/in/its-seraj/
GitHub:     https://github.com/its-seraj
'''


# Imports
import os
import csv
import re
import pyautogui

# Set CSV field size limit to prevent field size errors
csv.field_size_limit(1000000)  # Set to 1MB instead of default 131KB

from random import choice, shuffle, randint
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchWindowException, ElementNotInteractableException, WebDriverException, StaleElementReferenceException

from config.personals import *
from config.questions import *
from config.resume_profile import STRONG_MATCH_KEYWORDS, SUPPORTING_MATCH_KEYWORDS, RECENT_EMPLOYER
from config.search import *
from config.secrets import use_AI, username, password, ai_provider, llm_model
from config.settings import *

from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
from modules.job_matcher import evaluate_job_fit, evaluate_job_title
from modules.validator import validate_config

# For resume extraction and intelligent matching
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

if use_AI:
    from modules.ai.openaiConnections import ai_create_openai_client, ai_extract_skills, ai_answer_question, ai_close_openai_client
    from modules.ai.deepseekConnections import deepseek_create_client, deepseek_extract_skills, deepseek_answer_question
    from modules.ai.geminiConnections import gemini_create_client, gemini_extract_skills, gemini_answer_question

from typing import Literal


pyautogui.FAILSAFE = False
# if use_resume_generator:    from resume_generator import is_logged_in_GPT, login_GPT, open_resume_chat, create_custom_resume


#< Global Variables and logics

if run_in_background == True:
    pause_at_failed_question = False
    pause_before_submit = False
    run_non_stop = False
    auto_submit = True  # Force auto_submit when running in background

first_name = first_name.strip()
middle_name = middle_name.strip()
last_name = last_name.strip()
full_name = first_name + " " + middle_name + " " + last_name if middle_name else first_name + " " + last_name

useNewResume = True
randomly_answered_questions = set()

# Resume text for intelligent matching (NEW FEATURE)
resume_text = resume_text_for_matching.strip() if resume_text_for_matching else ""

tabs_count = 1
easy_applied_count = 0
external_jobs_count = 0
failed_count = 0
skip_count = 0
dailyEasyApplyLimitReached = False

re_experience = re.compile(r'[(]?\s*(\d+)\s*[)]?\s*[-to]*\s*\d*[+]*\s*year[s]?', re.IGNORECASE)

desired_salary_lakhs = str(round(desired_salary / 100000, 2))
desired_salary_monthly = str(round(desired_salary/12, 2))
desired_salary = str(desired_salary)

current_ctc_lakhs = str(round(current_ctc / 100000, 2))
current_ctc_monthly = str(round(current_ctc/12, 2))
current_ctc = str(current_ctc)

notice_period_months = str(notice_period//30)
notice_period_weeks = str(notice_period//7)
notice_period = str(notice_period)

aiClient = None
##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------
about_company_for_ai = None # TODO extract about company for AI
##<

#>


#< Login Functions
def is_logged_in_LN() -> bool:
    '''
    Function to check if user is logged-in in LinkedIn
    * Returns: `True` if user is logged-in or `False` if not
    '''
    try:
        current_url = driver.current_url.lower()
        if "linkedin.com/feed" in current_url or "linkedin.com/jobs" in current_url or "linkedin.com/in/" in current_url:
            return True
        
        # Check for profile avatar, global navigation, or me menu
        if try_xp(driver, "//nav[contains(@class, 'global-nav')]", click=False):
            return True
        if try_xp(driver, "//img[contains(@class, 'global-nav__me-photo')]", click=False):
            return True
        if try_xp(driver, "//button[contains(@class, 'global-nav__primary-link-me-menu-trigger')]", click=False):
            return True

        if try_linkText(driver, "Sign in"): return False
        if try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]', click=False): return False
        if try_linkText(driver, "Join now"): return False
        if "login" in current_url or "checkpoint" in current_url or "signup" in current_url:
            return False
            
        print_lg("Didn't find Sign in link, assuming user is logged in!")
        return True
    except Exception:
        return False


def login_LN() -> None:
    '''
    Function to login for LinkedIn
    * Tries to login using given `username` and `password` from `secrets.py`
    * If failed, tries to login using saved LinkedIn profile button if available
    * If both failed, asks user to login manually
    '''
    print_lg("Attempting LinkedIn login...")
    driver.get("https://www.linkedin.com/login")
    try:
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
        if username and password:
            try:
                text_input_by_ID(driver, "username", username, 2)
            except Exception as e:
                print_lg("Couldn't find username field.")
            try:
                text_input_by_ID(driver, "password", password, 2)
            except Exception as e:
                print_lg("Couldn't find password field.")
            try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]')
    except Exception as e1:
        try:
            profile_button = find_by_class(driver, "profile__details")
            profile_button.click()
        except Exception as e2:
            print_lg("Couldn't find profile button to login.")

    # Wait up to 10 seconds to see if auto login or redirect succeeds
    for _ in range(10):
        sleep(1)
        if is_logged_in_LN():
            print_lg("Login successful! Session saved to profile.")
            return

    print_lg("Auto login requires verification (e.g. CAPTCHA, 2FA, or credentials). Please log in manually in the browser window.")
    manual_login_retry(is_logged_in_LN, 3)
    if is_logged_in_LN():
        print_lg("Manual login confirmed! Session will be saved for future launches.")
#>



def get_applied_job_ids() -> set[str]:
    '''
    Function to get a `set` of applied job's Job IDs
    * Returns a set of Job IDs from existing applied jobs history csv file
    '''
    job_ids: set[str] = set()
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                job_ids.add(row[0])
    except FileNotFoundError:
        print_lg(f"The CSV file '{file_name}' does not exist.")
    return job_ids



# ===========================================================================================
# NEW LINKEDIN UI (2024+) — URL-Based Filters & Resilient Helpers
# All filters (Location, Date Posted, Easy Apply, Experience Level, Job Type, Remote, Sort)
# are encoded directly into the LinkedIn search URL. This avoids fragile UI clicks and modal errors.
# ===========================================================================================

def build_linkedin_search_url(keywords: str) -> str:
    '''
    Builds a LinkedIn job search URL with all search preferences and filters
    cleanly encoded as query parameters. This ensures LinkedIn applies filters
    server-side, avoiding UI interaction errors.
    '''
    from urllib.parse import urlencode
    params = {}
    params['keywords'] = keywords.strip()

    # Search location
    if search_location and search_location.strip():
        params['location'] = search_location.strip()

    # Date posted (f_TPR)
    # Options: "Past 24 hours" -> r86400, "Past week" -> r604800, "Past month" -> r2592000
    if date_posted and date_posted.strip().lower() != "any time":
        dp_lower = date_posted.strip().lower()
        if "24" in dp_lower:
            params['f_TPR'] = 'r86400'
        elif "week" in dp_lower:
            params['f_TPR'] = 'r604800'
        elif "month" in dp_lower:
            params['f_TPR'] = 'r2592000'

    # Easy Apply only (f_AL)
    if easy_apply_only:
        params['f_AL'] = 'true'

    # Experience level (f_E)
    # Mapping: Internship=1, Entry level=2, Associate=3, Mid-Senior level=4, Director=5, Executive=6
    exp_code_map = {
        "internship": "1",
        "entry level": "2",
        "entry-level": "2",
        "associate": "3",
        "mid-senior level": "4",
        "senior": "4",
        "director": "5",
        "executive": "6",
    }
    if experience_level:
        exp_codes = []
        for exp in experience_level:
            c = exp_code_map.get(exp.strip().lower())
            if c and c not in exp_codes:
                exp_codes.append(c)
        if exp_codes:
            params['f_E'] = ','.join(exp_codes)

    # Job type / Employment type (f_JT)
    # Full-time=F, Part-time=P, Contract=C, Temporary=T, Volunteer=V, Internship=I, Other=O
    job_type_code_map = {
        "full-time": "F",
        "part-time": "P",
        "contract": "C",
        "temporary": "T",
        "volunteer": "V",
        "internship": "I",
        "other": "O",
    }
    if job_type:
        jt_codes = []
        for jt in job_type:
            c = job_type_code_map.get(jt.strip().lower())
            if c and c not in jt_codes:
                jt_codes.append(c)
        if jt_codes:
            params['f_JT'] = ','.join(jt_codes)

    # Workplace style / On-site / Remote (f_WT)
    # On-site=1, Remote=2, Hybrid=3
    work_style_code_map = {
        "on-site": "1",
        "remote": "2",
        "hybrid": "3",
    }
    if on_site:
        wt_codes = []
        for ws in on_site:
            c = work_style_code_map.get(ws.strip().lower())
            if c and c not in wt_codes:
                wt_codes.append(c)
        if wt_codes:
            params['f_WT'] = ','.join(wt_codes)

    # Sort By (sortBy)
    # Most recent=DD, Most relevant=R
    if sort_by:
        sb_lower = sort_by.strip().lower()
        if "recent" in sb_lower:
            params['sortBy'] = 'DD'
        elif "relevant" in sb_lower:
            params['sortBy'] = 'R'

    query_str = urlencode(params)
    return f"https://www.linkedin.com/jobs/search-results/?{query_str}"


def _new_ui_open_dropdown(button_text: str) -> bool:
    '''Opens a filter dropdown pill by its button text. Returns True on success.'''
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f'//button[contains(normalize-space(),"{button_text}")]'))
        )
        scroll_to_view(driver, btn)
        btn.click()
        buffer(0.5)
        return True
    except Exception as e:
        print_lg(f"Could not open filter dropdown '{button_text}': {e}")
        return False


def _new_ui_click_show_results() -> None:
    '''Clicks the "Show results" button inside an open filter dropdown.'''
    try:
        btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, '//button[normalize-space()="Show results"]'))
        )
        btn.click()
        buffer(click_gap)
    except Exception:
        print_lg("Could not find 'Show results' button in filter dropdown")


def dismiss_feedback_modal() -> None:
    '''
    Dismisses feedback modals (such as "Why are these results not helpful?"),
    popups, or dialog overlays that can block job card interaction.
    '''
    try:
        close_buttons = driver.find_elements(By.XPATH, 
            "//div[contains(@role, 'dialog')]//button[contains(@aria-label, 'Dismiss') or contains(@aria-label, 'Close') or contains(normalize-space(), 'Cancel') or contains(normalize-space(), 'Dismiss')]"
        )
        for btn in close_buttons:
            if btn.is_displayed():
                btn.click()
                sleep(0.3)
                return
    except Exception:
        pass
    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except Exception:
        pass


def apply_filters() -> None:
    '''
    Applies search filters. In the new LinkedIn UI (2024+), all standard filters
    (Location, Date Posted, Easy Apply, Experience Level, Job Type, Remote, Sort)
    are applied natively via URL parameters generated in build_linkedin_search_url().
    
    This function handles any remaining filters that require UI interaction
    (e.g., specific company inclusion/search) and the pause-after-search prompt.
    '''
    try:
        recommended_wait = 1 if click_gap < 1 else 0

        # Company filter (search input inside Company dropdown)
        if companies:
            if _new_ui_open_dropdown("Company"):
                for company in companies:
                    try:
                        company_input = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH,
                                '//input[contains(@placeholder,"company") or contains(@aria-label,"company") '
                                'or contains(@placeholder,"Company") or contains(@aria-label,"Company")]'
                            ))
                        )
                        company_input.click()
                        company_input.send_keys(Keys.CONTROL + "a")
                        company_input.send_keys(Keys.DELETE)
                        company_input.send_keys(company)
                        sleep(1.0)
                        try:
                            suggestion = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, f'//label[contains(normalize-space(),"{company}")]'))
                            )
                            suggestion.click()
                            buffer(0.3)
                        except Exception:
                            ActionChains(driver).send_keys(Keys.DOWN, Keys.ENTER).perform()
                            buffer(0.3)
                    except Exception as e2:
                        print_lg(f"Could not add company '{company}' to filter", e2)
                _new_ui_click_show_results()
                buffer(recommended_wait)

        # Pause after filters if configured
        global pause_after_filters
        if pause_after_filters and not auto_submit:
            if "Turn off Pause after search" == pyautogui.confirm(
                "Filters have been applied. You can adjust your search results now.",
                "Please check your results",
                ["Turn off Pause after search", "Look's good, Continue"]
            ):
                pause_after_filters = False

    except Exception as e:
        print_lg("Setting additional preferences failed!")
        print_lg(e)


def get_page_info() -> tuple[WebElement | None, int]:
    '''
    Function to get pagination element and current page number.
    Supports both old (artdeco-pagination) and new LinkedIn UI structures.
    '''
    # Attempt 1: Standard legacy pagination container
    try:
        pagination_element = try_find_by_classes(driver, ["jobs-search-pagination__pages", "artdeco-pagination", "artdeco-pagination__pages"])
        if pagination_element:
            scroll_to_view(driver, pagination_element)
            active_btn = pagination_element.find_element(By.XPATH, ".//button[contains(@class, 'active')]")
            return pagination_element, int(active_btn.text.strip())
    except Exception:
        pass

    # Attempt 2: New UI pagination buttons (button[aria-label="Page N"])
    try:
        page_buttons = driver.find_elements(By.XPATH, "//button[starts-with(@aria-label, 'Page ')]")
        if page_buttons:
            container = page_buttons[0].find_element(By.XPATH, "./..")
            for btn in page_buttons:
                aria = btn.get_attribute("aria-label") or ""
                if btn.get_attribute("aria-current") in ("true", "page") or "active" in (btn.get_attribute("class") or "").lower():
                    m = re.search(r'\d+', aria)
                    if m:
                        return container, int(m.group(0))
            return container, 1
    except Exception:
        pass

    return None, 1



# >>>>>>>>>>> INTELLIGENT RESUME MATCHING (NEW FEATURE) <<<<<<<<<<<
def extract_resume_text_from_pdf() -> str:
    '''
    Extract text from PDF resume file for intelligent matching
    '''
    global resume_text
    if resume_text:  # Already loaded from config
        return resume_text
    
    try:
        if PyPDF2 is None:
            print_lg("PyPDF2 not installed. Skipping PDF resume extraction.")
            return ""
        
        resume_path = os.path.abspath(default_resume_path)
        if not os.path.exists(resume_path):
            print_lg(f"Resume file not found at {resume_path}")
            return ""
        
        print_lg(f"Extracting text from resume: {resume_path}")
        with open(resume_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        resume_text = text
        print_lg("Resume text extracted successfully!")
        return text
    except Exception as e:
        print_lg(f"Failed to extract resume text: {e}")
        return ""


def check_intelligent_resume_match(job_title: str, job_description: str) -> tuple[bool, str]:
    '''
    Check if a job matches the user's resume skills/experience.
    Uses deterministic resume-aware matching first, then AI if available.
    
    Returns: (should_apply: bool, match_reason: str)
    '''
    global resume_text, aiClient
    
    if not intelligent_resume_matching:
        return False, "Feature disabled"
    
    try:
        # Extract resume text if not already done
        if not resume_text:
            extract_resume_text_from_pdf()
        
        if not resume_text:
            print_lg("No resume text available for intelligent matching")
            return False, "No resume text"
        
        is_match, match_reason = evaluate_job_fit(job_title, job_description, allowed_job_titles)
        if is_match:
            print_lg(f"Resume matcher accepted '{job_title}': {match_reason}")
            return True, match_reason
        
        if use_AI and aiClient:
            try:
                matching_prompt = f"""
Analyze if this job is a good match for someone with this resume/experience:

RESUME/EXPERIENCE:
{resume_text[:2000]}

JOB TITLE:
{job_title[:300]}

JOB DESCRIPTION:
{job_description[:2000]}

Consider:
1. Technical skills match (even if job title is different)
2. Experience level match
3. Industry/domain match
4. Growth potential

Respond with ONLY a JSON object like this:
{{"is_match": true/false, "confidence": 0.0-1.0, "reason": "brief explanation"}}
"""
                
                if ai_provider.lower() == "openai":
                    response = aiClient.chat.completions.create(
                        model=llm_model,
                        messages=[{"role": "user", "content": matching_prompt}],
                        temperature=0.3
                    )
                    result_text = response.choices[0].message.content.strip()
                elif ai_provider.lower() == "gemini":
                    try:
                        response = aiClient.generate_content(matching_prompt, request_options={"timeout": 15})
                        result_text = response.text.strip()
                    except Exception as ge:
                        print_lg(f"Gemini API matching timed out or failed: {ge}")
                        result_text = ""
                elif ai_provider.lower() == "deepseek":
                    response = aiClient.chat.completions.create(
                        model=llm_model,
                        messages=[{"role": "user", "content": matching_prompt}],
                        temperature=0.3
                    )
                    result_text = response.choices[0].message.content.strip()
                else:
                    result_text = ""
                
                # Parse JSON response
                if result_text:
                    import json
                    try:
                        # Extract JSON from response (might have extra text)
                        json_start = result_text.find('{')
                        json_end = result_text.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = result_text[json_start:json_end]
                            match_data = json.loads(json_str)
                            
                            is_match = match_data.get("is_match", False)
                            confidence = match_data.get("confidence", 0)
                            reason = match_data.get("reason", "")
                            
                            if is_match and confidence > 0.5:
                                print_lg(f"✓ AI Resume Match Found! Confidence: {confidence*100:.0f}% - {reason}")
                                return True, f"AI matched (confidence: {confidence:.2f})"
                    except Exception as e:
                        print_lg(f"Failed to parse AI response: {e}")
            except Exception as e:
                print_lg(f"AI matching failed: {e}")

        return False, match_reason
        
    except Exception as e:
        print_lg(f"Error in intelligent resume matching: {e}")
        return False, f"Error: {str(e)}"

#<



def get_job_main_details(
    job: WebElement,
    blacklisted_companies: set,
    rejected_jobs: set,
) -> tuple[str, str, str, str, str, bool, bool, str]:
    '''
    # Function to get job main details.
    Compatible with both NEW LinkedIn UI (div[role="button"]) and OLD UI (li[data-occludable-job-id]).
    Returns a tuple of:
    (job_id, title, company, work_location, work_style, skip, title_allowed, title_reason)
    '''
    title = ""
    company = ""
    work_location = ""
    work_style = ""
    job_id = None

    scroll_to_view(driver, job, True)

    # 1. Job ID from modern LinkedIn componentkey or data attributes
    ck = job.get_dom_attribute('componentkey') or ""
    m_ck = re.search(r'ref-(\d+)', ck)
    if m_ck:
        job_id = m_ck.group(1)
    else:
        job_id = job.get_dom_attribute('data-job-id') or job.get_dom_attribute('data-occludable-job-id')

    if not job_id:
        try:
            # Check inner element with componentkey, data-job-id or data-occludable-job-id
            inner_id_el = job.find_element(By.XPATH, ".//*[@componentkey or @data-job-id or @data-occludable-job-id]")
            inner_ck = inner_id_el.get_dom_attribute('componentkey') or ""
            m_inner = re.search(r'ref-(\d+)', inner_ck)
            if m_inner:
                job_id = m_inner.group(1)
            else:
                job_id = inner_id_el.get_dom_attribute('data-job-id') or inner_id_el.get_dom_attribute('data-occludable-job-id')
        except Exception:
            pass
    if not job_id:
        try:
            href = job.get_attribute('href') or ""
            m = re.search(r'/jobs/view/(\d+)', href) or re.search(r'currentJobId=(\d+)', href)
            if m:
                job_id = m.group(1)
            else:
                link_el = job.find_element(By.XPATH, ".//a[contains(@href, '/jobs/view/')]")
                href = link_el.get_attribute('href') or ""
                m = re.search(r'/jobs/view/(\d+)', href)
                if m:
                    job_id = m.group(1)
        except Exception:
            pass

    # 2. Extract title, company, location
    # Priority A: Modern LinkedIn paragraph structure (verified from live DOM dump)
    try:
        ps = job.find_elements(By.TAG_NAME, 'p')
        if len(ps) >= 2:
            spans = ps[0].find_elements(By.TAG_NAME, 'span')
            raw_title = ""
            for s in spans:
                t = s.text.strip()
                if t:
                    raw_title = t
                    break
            if not raw_title:
                raw_title = ps[0].text.strip()
            raw_title = re.sub(r'\(verified job\)', '', raw_title, flags=re.IGNORECASE).strip()
            raw_title = re.sub(r'^selected,\s*', '', raw_title, flags=re.IGNORECASE).strip()
            title = raw_title.strip()
            company = ps[1].text.strip()
            if len(ps) >= 3:
                work_location = ps[2].text.strip()
    except Exception:
        pass

    # Priority B: Legacy UI structure fallback
    if not title or not company:
        try:
            title_el = job.find_element(By.XPATH, ".//a[contains(@class, 'job-card-list__title') or contains(@class, 'job-card-container__link')] | .//a[contains(@href, '/jobs/view/')] | .//a")
            title = title_el.text.split("\n", 1)[0].strip()
            other_details = job.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle').text
            index = other_details.find(' · ')
            if index != -1:
                company = other_details[:index].strip()
                work_location = other_details[index+3:].strip()
            else:
                company = other_details.strip()
        except Exception:
            card_text = job.text
            lines = [line.strip() for line in card_text.split('\n') if line.strip() and line.strip() != '·']
            if lines and not title:
                raw_title = lines[0]
                raw_title = re.sub(r'^selected,\s*', '', raw_title, flags=re.IGNORECASE)
                raw_title = re.sub(r'\s*\(verified job\)', '', raw_title, flags=re.IGNORECASE)
                title = raw_title.strip()
            if len(lines) >= 2 and not company:
                company = lines[1].strip()
            if len(lines) >= 3 and not work_location:
                work_location = lines[2].strip()

    # Extract work style (Remote, Hybrid, On-site) from work_location if present in parens
    if '(' in work_location and ')' in work_location:
        work_style = work_location[work_location.rfind('(')+1:work_location.rfind(')')].strip()
        work_location = work_location[:work_location.rfind('(')].strip()

    # Validation guard against non-jobs and UI buttons (e.g. "More", "Dismiss", "Feedback")
    invalid_titles = {'more', 'see more', 'dismiss', 'close', 'cancel', 'send', 'feedback', 'are these results helpful?'}
    if not title or title.lower() in invalid_titles or len(title) < 3 or not company:
        print_lg(f"Skipping invalid non-job element (title: '{title}', company: '{company}', job_id: '{job_id}')")
        return (job_id or "", title, company, work_location, work_style, True, False, "Not a valid job card")

    # Skip if previously rejected due to blacklist, current employer, or already applied
    skip = False
    title_allowed = True
    title_reason = "Title not evaluated"
    company_low = company.lower().strip()

    if RECENT_EMPLOYER and RECENT_EMPLOYER.lower() in company_low:
        print_lg(f'Skipping "{title} | {company}" job (Current Employer: {RECENT_EMPLOYER}). Job ID: {job_id}!')
        skip = True
    elif any(bad_comp.lower() in company_low for bad_comp in about_company_bad_words if bad_comp):
        print_lg(f'Skipping "{title} | {company}" job (Blacklisted Company Name). Job ID: {job_id}!')
        skip = True
    elif company in blacklisted_companies:
        print_lg(f'Skipping "{title} | {company}" job (Blacklisted Company). Job ID: {job_id}!')
        skip = True
    elif job_id and job_id in rejected_jobs: 
        print_lg(f'Skipping previously rejected "{title} | {company}" job. Job ID: {job_id}!')
        skip = True

    if not skip:
        skip, title_allowed, title_reason = evaluate_job_title(title, allowed_job_titles)
        if skip:
            print_lg(f'Skipping "{title} | {company}" job ({title_reason}). Job ID: {job_id}!')
        elif not title_allowed:
            print_lg(f'"{title} | {company}" needs description-based validation. Job ID: {job_id}!')

    # Check if already applied from card text
    card_text = job.text.lower()
    if "applied" in card_text:
        skip = True
        print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')

    # Click the job card to load right detail pane
    try: 
        if not skip:
            job.click()
            buffer(click_gap)
            # If job_id was not on the card, extract from currentJobId in URL or right pane view link
            if not job_id:
                m = re.search(r'currentJobId=(\d+)', driver.current_url)
                if m:
                    job_id = m.group(1)
                else:
                    try:
                        view_link = driver.find_element(By.XPATH, "//a[contains(@href, '/jobs/view/')]")
                        href = view_link.get_attribute('href')
                        m2 = re.search(r'/jobs/view/(\d+)', href)
                        if m2:
                            job_id = m2.group(1)
                    except Exception:
                        pass
                if not job_id:
                    job_id = f"gen_{abs(hash(title + company))}"
    except Exception as e:
        print_lg(f'Failed to click "{title} | {company}" job. Job ID: {job_id}!') 
        discard_job()
        try:
            job.click()
        except Exception:
            pass

    buffer(click_gap)
    return (str(job_id or ""), title, company, work_location, work_style, skip, title_allowed, title_reason)


# Function to check for Blacklisted words in About Company
def check_blacklist(rejected_jobs: set, job_id: str, company: str, blacklisted_companies: set) -> tuple[set, set, WebElement] | ValueError:
    jobs_top_card = try_find_by_classes(driver, ["job-details-jobs-unified-top-card__primary-description-container","job-details-jobs-unified-top-card__primary-description","jobs-unified-top-card__primary-description","jobs-details__main-content"])
    about_company_el = try_find_by_classes(driver, ["jobs-company__box", "job-details-company-module", "jobs-company__box--fade-in"])
    if not about_company_el:
        try:
            about_company_el = driver.find_element(By.XPATH, "//div[contains(@class,'jobs-company')] | //section[contains(@class,'company-module')]")
        except Exception:
            about_company_el = None

    if about_company_el:
        scroll_to_view(driver, about_company_el)
        about_company_org = about_company_el.text
        about_company = about_company_org.lower()
        skip_checking = False
        for word in about_company_good_words:
            if word.lower() in about_company:
                print_lg(f'Found the word "{word}". So, skipped checking for blacklist words.')
                skip_checking = True
                break
        if not skip_checking:
            if RECENT_EMPLOYER and RECENT_EMPLOYER.lower() in about_company:
                rejected_jobs.add(job_id)
                blacklisted_companies.add(company)
                raise ValueError(f'\n"{about_company_org}"\n\nMatches current employer "{RECENT_EMPLOYER}".')
            for word in about_company_bad_words: 
                if word.lower() in about_company: 
                    rejected_jobs.add(job_id)
                    blacklisted_companies.add(company)
                    raise ValueError(f'\n"{about_company_org}"\n\nContains "{word}".')
        buffer(click_gap)
        if jobs_top_card:
            scroll_to_view(driver, jobs_top_card)
    return rejected_jobs, blacklisted_companies, jobs_top_card



# Function to extract years of experience required from About Job
def extract_years_of_experience(text: str) -> int:
    # Extract all patterns like '10+ years', '5 years', '3-5 years', etc.
    matches = re.findall(re_experience, text)
    if len(matches) == 0: 
        print_lg(f'\n{text}\n\nCouldn\'t find experience requirement in About the Job!')
        return 0
    return max([int(match) for match in matches if int(match) <= 12])



def get_job_description(
    job_title: str,
    title_allowed: bool,
    title_reason: str,
) -> tuple[
    str | Literal['Unknown'],
    int | Literal['Unknown'],
    bool,
    str | None,
    str | None
    ]:
    '''
    # Job Description
    Function to extract job description from About the Job.
    ### Returns:
    - `jobDescription: str | 'Unknown'`
    - `experience_required: int | 'Unknown'`
    - `skip: bool`
    - `skipReason: str | None`
    - `skipMessage: str | None`
    '''
    try:
        ##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------
        jobDescription = "Unknown"
        experience_required = "Unknown"
        found_masters = 0
        desc_el = try_find_by_classes(driver, ["jobs-box__html-content", "jobs-description__content", "jobs-description", "jobs-box--fade-in"])
        if not desc_el:
            for d_xp in [
                "//section[contains(., 'About the job')]",
                "//div[contains(@class, 'jobs-description')]",
                "//div[@id='job-details']",
                "//article",
                "//div[contains(@class, 'job-details')]",
                "//section[contains(@class, 'description')]"
            ]:
                try:
                    el = driver.find_element(By.XPATH, d_xp)
                    if el and el.text.strip():
                        desc_el = el
                        break
                except Exception:
                    pass
        if desc_el:
            jobDescription = desc_el.text
        else:
            try:
                fb = find_by_class(driver, "jobs-box__html-content", 2.0)
                if fb:
                    jobDescription = fb.text
            except Exception:
                pass
        jobDescriptionLow = jobDescription.lower()
        skip = False
        skipReason = None
        skipMessage = None
        for word in bad_words:
            if word.lower() in jobDescriptionLow:
                skipMessage = f'\n{jobDescription}\n\nContains bad word "{word}". Skipping this job!\n'
                skipReason = "Found a Bad Word in About Job"
                skip = True
                break
        if not skip and security_clearance == False and ('polygraph' in jobDescriptionLow or 'clearance' in jobDescriptionLow or 'secret' in jobDescriptionLow):
            skipMessage = f'\n{jobDescription}\n\nFound "Clearance" or "Polygraph". Skipping this job!\n'
            skipReason = "Asking for Security clearance"
            skip = True
        if not skip:
            if did_masters and 'master' in jobDescriptionLow:
                print_lg(f'Found the word "master" in \n{jobDescription}')
                found_masters = 2
            experience_required = extract_years_of_experience(jobDescription)
            if current_experience > -1 and experience_required > current_experience + found_masters:
                skipMessage = f'\n{jobDescription}\n\nExperience required {experience_required} > Current Experience {current_experience + found_masters}. Skipping this job!\n'
                skipReason = "Required experience is high"
                skip = True

        if not skip and not title_allowed:
            if intelligent_resume_matching:
                is_match, match_reason = check_intelligent_resume_match(job_title, jobDescription)
                if is_match:
                    print_lg(f"✓ Job passed resume matching despite the title: {match_reason}")
                else:
                    skip = True
                    skipReason = "Title not aligned with resume"
                    skipMessage = (
                        f'\n{jobDescription}\n\n'
                        f'Title screen reason: {title_reason}\n'
                        f'Resume match result: {match_reason}\n'
                        'Skipping this job!\n'
                    )
            else:
                skip = True
                skipReason = "Title not in allowed list"
                skipMessage = (
                    f'\n{jobDescription}\n\n'
                    f'Title screen reason: {title_reason}\n'
                    'Skipping this job!\n'
                )
                
    except Exception as e:
        if jobDescription == "Unknown":    print_lg("Unable to extract job description!")
        else:
            experience_required = "Error in extraction"
            print_lg("Unable to extract years of experience required!")
            # print_lg(e)
    return jobDescription, experience_required, skip, skipReason, skipMessage
        


# Function to upload resume
def upload_resume(modal: WebElement, resume: str) -> tuple[bool, str]:
    try:
        modal.find_element(By.NAME, "file").send_keys(os.path.abspath(resume))
        return True, os.path.basename(default_resume_path)
    except: return False, "Previous resume"

# Function to answer common questions for Easy Apply
def answer_common_questions(label: str, answer: str) -> str:
    if 'sponsorship' in label or 'visa' in label: answer = require_visa
    return answer


def is_placeholder_answer(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in {"", "na", "n/a", "none", "null"}


def answer_resume_specific_question(
    label: str,
    question_type: Literal['text', 'textarea'] = 'text',
) -> str:
    label = label.lower()

    if 'cgpa' in label or 'gpa' in label:
        return cgpa

    if any(keyword in label for keyword in ['achievement', 'accomplishment', 'award', 'hackathon', 'rank']):
        return notable_achievements

    if any(keyword in label for keyword in ['about yourself', 'tell us about yourself', 'about you']):
        return linkedin_summary if question_type == 'textarea' else linkedin_headline

    if any(keyword in label for keyword in ['why do you want', 'why are you interested', 'why should we hire']):
        return linkedin_summary if question_type == 'textarea' else linkedin_headline

    if 'cover' in label:
        return cover_letter

    return ""


def answer_experience_question(label: str) -> str:
    label = label.lower()
    skill_question_markers = [
        'experience with',
        'experience in',
        'work experience do you have with',
        'years of experience with',
        'hands-on experience in',
    ]
    if not any(marker in label for marker in skill_question_markers):
        return years_of_experience

    resume_skill_hints = {
        keyword.lower() for keyword in STRONG_MATCH_KEYWORDS + SUPPORTING_MATCH_KEYWORDS
    }
    resume_skill_hints.update({
        'git',
        'rest',
        'representational state transfer',
        'api',
        'python',
        'java',
        'javascript',
        'typescript',
        'fastapi',
        'flask',
        'postgresql',
        'redis',
        'docker',
        'kubernetes',
        'aws',
        'machine learning',
        'computer vision',
        'llm',
        'rag',
        'gcp',
        'google cloud',
        'cloud',
    })

    for skill in resume_skill_hints:
        if skill in label:
            return years_of_experience
    return ""


def clean_question_text(raw: str) -> str:
    """Strips error messages, character counters, asterisks, and extra whitespace."""
    if not raw:
        return ""
    t = re.sub(r'[\*\r\n]+', ' ', raw).strip()
    # Remove validation messages
    t = re.sub(r'(?i)\b(invalid input|this field is required|please enter a valid number|required)\b', '', t).strip()
    # Remove character counters like 0/20, 1/20, 0/1,440
    t = re.sub(r'\s*\d+\s*/\s*[\d,]+\s*$', '', t).strip()
    t = re.sub(r'\s{2,}', ' ', t).strip()
    return t


def extract_question_label(element: WebElement, default: str = "Unknown") -> str:
    """Extracts a clean label/title for a given form element or container."""
    try:
        # 1. aria-label on the element
        aria = element.get_attribute("aria-label")
        if aria and len(aria.strip()) > 1:
            clean = clean_question_text(aria)
            if clean:
                return clean

        # 2. aria-labelledby
        aria_by = element.get_attribute("aria-labelledby")
        if aria_by:
            for aid in aria_by.split():
                try:
                    el = element.find_element(By.XPATH, f"//*[@id='{aid}']")
                    clean = clean_question_text(el.text)
                    if clean:
                        return clean
                except Exception:
                    pass

        # 3. Label with for="id"
        el_id = element.get_attribute("id")
        if el_id:
            try:
                for_lbl = driver.find_element(By.XPATH, f"//label[@for='{el_id}']")
                clean = clean_question_text(for_lbl.text)
                if clean:
                    return clean
            except Exception:
                pass

        # 4. Nested labels/legends/headings
        nested = element.find_elements(By.XPATH, ".//label | .//legend | .//span[contains(@class, 'title') or contains(@class, 'label') or contains(@class, 't-14')]")
        for lbl in nested:
            clean = clean_question_text(lbl.text)
            if clean and len(clean) > 2:
                return clean

        # 5. Preceding label in DOM
        try:
            prec_lbl = element.find_element(By.XPATH, "./preceding::label[1]")
            clean = clean_question_text(prec_lbl.text)
            if clean:
                return clean
        except Exception:
            pass

        # 6. Fallback: text of container
        txt = element.text.strip()
        if txt:
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            for line in lines:
                clean = clean_question_text(line)
                if clean and len(clean) > 2:
                    return clean
    except Exception:
        pass
    return default


def safe_fill_input(driver: WebDriver, element: WebElement, value: str):
    """Fills an input or textarea and triggers React synthetic events for state synchronization."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        sleep(0.1)
    except Exception:
        pass
    try:
        element.click()
    except Exception:
        pass
    try:
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.BACKSPACE)
    except Exception:
        try:
            element.clear()
        except Exception:
            pass
    try:
        element.send_keys(str(value))
    except Exception:
        pass
    # Force React to register change and remove "Invalid input" errors
    try:
        driver.execute_script("""
            var el = arguments[0];
            var val = arguments[1];
            var prototype = Object.getPrototypeOf(el);
            var descriptor = Object.getOwnPropertyDescriptor(prototype, 'value');
            if (descriptor && descriptor.set) {
                descriptor.set.call(el, val);
            } else {
                el.value = val;
            }
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new Event('blur', { bubbles: true }));
        """, element, str(value))
    except Exception:
        pass


def wait_for_modal_ready(driver: WebDriver, timeout: float = 8.0) -> WebElement | None:
    """Waits for Easy Apply modal to finish loading GraphQL dynamic steps (spinners vanish, buttons ready)."""
    start = datetime.now()
    modal = None
    while (datetime.now() - start).total_seconds() < timeout:
        try:
            m = driver.find_element(By.XPATH, "//dialog[@open] | //div[contains(@class, 'jobs-easy-apply-modal')] | //div[@role='dialog']")
            if m and m.is_displayed():
                modal = m
                spinners = m.find_elements(By.XPATH, ".//*[@role='progressbar'] | .//*[@data-testid='loader'] | .//*[contains(@class, 'artdeco-loader')]")
                has_spinner = any(s.is_displayed() for s in spinners)

                buttons = m.find_elements(By.XPATH, ".//footer//button | .//button[contains(., 'Next') or contains(., 'Review') or contains(., 'Submit')]")
                has_buttons = any(b.is_displayed() for b in buttons)

                if not has_spinner and has_buttons:
                    return modal
        except Exception:
            pass
        sleep(0.05)
    return modal


def wait_for_submit_ready(driver: WebDriver, timeout: float = 6.0) -> WebElement | None:
    """Waits for the final review/submit page to be fully loaded (Submit application button visible)."""
    start = datetime.now()
    while (datetime.now() - start).total_seconds() < timeout:
        for sub_xpath in [
            "//dialog//footer//button[contains(., 'Submit application') or contains(@aria-label, 'Submit application') or .//span[normalize-space()='Submit application']]",
            "//button[contains(., 'Submit application') or contains(@aria-label, 'Submit application') or .//span[normalize-space()='Submit application']]",
        ]:
            try:
                for btn in driver.find_elements(By.XPATH, sub_xpath):
                    if btn.is_displayed():
                        try:
                            modal = driver.find_element(By.XPATH, "//dialog[@open] | //div[contains(@class, 'jobs-easy-apply-modal')] | //div[@role='dialog']")
                            return modal
                        except Exception:
                            return driver
            except Exception:
                pass
        sleep(0.05)
    return None



def find_and_click_next_or_review(driver: WebDriver, modal: WebElement) -> tuple[bool, str]:
    """Finds and clicks Next, Review, or Submit button within the Easy Apply modal footer immediately."""
    if not modal:
        modal = wait_for_modal_ready(driver, 4.0)
    if not modal:
        return False, "no_modal"

    candidate_xpaths = [
        ("review", ".//button[contains(., 'Review') or contains(@aria-label, 'Review') or .//span[normalize-space()='Review']]"),
        ("review", "//dialog//footer//button[contains(., 'Review') or .//span[normalize-space()='Review']]"),
        ("next", ".//button[contains(., 'Next') or contains(@aria-label, 'Continue to next step') or .//span[normalize-space()='Next']]"),
        ("next", "//dialog//footer//button[contains(., 'Next') or contains(@aria-label, 'Continue to next step') or .//span[normalize-space()='Next']]"),
        ("submit", ".//button[contains(., 'Submit application') or contains(@aria-label, 'Submit application') or .//span[normalize-space()='Submit application']]"),
        ("submit", "//dialog//footer//button[contains(., 'Submit application') or .//span[normalize-space()='Submit application']]"),
    ]

    for btn_type, xpath in candidate_xpaths:
        try:
            buttons = modal.find_elements(By.XPATH, xpath)
            if not buttons:
                buttons = driver.find_elements(By.XPATH, xpath)
            for btn in buttons:
                if btn.get_attribute("data-testid") == "pagination-controls-next-button-visible":
                    continue
                if btn.is_displayed():
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    except Exception:
                        pass
                    clicked = False
                    try:
                        btn.click()
                        clicked = True
                    except Exception:
                        try:
                            ActionChains(driver).move_to_element(btn).click().perform()
                            clicked = True
                        except Exception:
                            try:
                                driver.execute_script("arguments[0].click();", btn)
                                clicked = True
                            except Exception:
                                pass
                    if clicked:
                        print_lg(f"Clicked '{btn_type}' button in Easy Apply modal")
                        return True, btn_type
        except Exception:
            continue
    return False, "none"



def ask_llm(
    question: str,
    options: list[str] | None = None,
    question_type: Literal['text', 'textarea', 'single_select', 'multiple_select'] = 'text',
    job_description: str | None = None
) -> str:
    """Dispatches question answering to configured LLM (Gemini / OpenAI / DeepSeek)."""
    global aiClient, ai_provider, user_information_all, about_company_for_ai
    if not (use_AI and aiClient):
        return ""

    clean_q = clean_question_text(question)
    provider = (ai_provider or "").lower()

    try:
        ans = None
        if provider == "gemini":
            ans = gemini_answer_question(
                aiClient,
                question=clean_q,
                options=options,
                question_type=question_type,
                job_description=job_description,
                about_company=about_company_for_ai,
                user_information_all=user_information_all
            )
        elif provider == "openai":
            ans = ai_answer_question(
                aiClient,
                question=clean_q,
                options=options,
                question_type=question_type,
                job_description=job_description,
                about_company=about_company_for_ai,
                user_information_all=user_information_all
            )
        elif provider == "deepseek":
            ans = deepseek_answer_question(
                aiClient,
                question=clean_q,
                options=options,
                question_type=question_type,
                job_description=job_description,
                about_company=about_company_for_ai,
                user_information_all=user_information_all
            )

        if isinstance(ans, dict):
            ans = ans.get("answer", "") or ans.get("response", "") or str(ans)
        if ans is not None:
            ans = str(ans).strip()
            # Remove wrapping quotes
            if (ans.startswith('"') and ans.endswith('"')) or (ans.startswith("'") and ans.endswith("'")):
                ans = ans[1:-1].strip()
            # Remove markdown formatting
            ans = re.sub(r'^```[a-z]*\s*', '', ans, flags=re.I)
            ans = re.sub(r'\s*```$', '', ans).strip()
            return ans
    except Exception as e:
        print_lg(f"Error getting AI answer for '{clean_q}': {e}")

    return ""


# Function to answer the questions for Easy Apply
def answer_questions(modal: WebElement, questions_list: set, work_location: str, job_description: str | None = None) -> set:
    """
    Scans and answers all questions in the Easy Apply modal dialog.
    Supports native <select> dropdowns, custom comboboxes, radio groups, checkboxes, text/number inputs, and textareas.
    Uses rules for common personal info, and seamlessly invokes LLM for custom questions.
    """
    # 1. Discover all form containers using modern LinkedIn component attributes
    container_xpaths = [
        ".//div[@data-test-form-element]",
        ".//div[contains(@class, 'jobs-easy-apply-form-element')]",
        ".//div[contains(@class, 'fb-dash-form-element')]",
        ".//div[contains(@class, 'jobs-easy-apply-form-section__grouping')]",
        ".//div[@data-test-single-line-text-form-component]",
        ".//div[@data-test-text-entity-list-form-component]",
        ".//div[@data-test-form-builder-radio-button-form-component]",
        ".//div[@data-test-multiline-text-form-component]",
        ".//div[contains(@class, 'artdeco-text-input--container')]",
        ".//div[contains(@class, 'fb-form-element')]",
    ]

    all_questions = []
    seen_elements = set()
    for xpath in container_xpaths:
        try:
            for el in modal.find_elements(By.XPATH, xpath):
                try:
                    eid = el.id
                except Exception:
                    eid = id(el)
                if eid not in seen_elements:
                    seen_elements.add(eid)
                    all_questions.append(el)
        except Exception:
            pass

    # 2. Comprehensive fallback: scan for interactive controls directly to ensure nothing is missed
    direct_controls = modal.find_elements(
        By.XPATH,
        ".//select | .//fieldset | .//textarea | .//input[not(@type) or @type='text' or @type='number' or @type='tel' or @type='email' or @type='checkbox']"
    )
    for ctrl in direct_controls:
        try:
            inside_known = False
            for q in all_questions:
                try:
                    if q == ctrl:
                        inside_known = True
                        break
                except Exception:
                    pass
            if not inside_known:
                try:
                    cid = ctrl.id
                except Exception:
                    cid = id(ctrl)
                if cid not in seen_elements:
                    seen_elements.add(cid)
                    all_questions.append(ctrl)
        except Exception:
            pass

    handled_controls = set()

    for Question in all_questions:
        try:
            # ----------------- Check if it's a select Question -----------------
            select_el = None
            if Question.tag_name.lower() == "select":
                select_el = Question
            else:
                select_el = try_xp(Question, ".//select", False)

            if select_el:
                try:
                    ctrl_id = select_el.id
                except Exception:
                    ctrl_id = id(select_el)
                if ctrl_id in handled_controls:
                    continue
                handled_controls.add(ctrl_id)

                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", select_el)
                    sleep(0.1)
                except Exception:
                    pass

                label_org = extract_question_label(Question, "Select option")
                label = label_org.lower()
                sel_obj = Select(select_el)

                try:
                    selected_option = sel_obj.first_selected_option.text.strip()
                except Exception:
                    selected_option = ""

                options_text = [
                    opt.text.strip()
                    for opt in sel_obj.options
                    if opt.text.strip() and opt.text.strip().lower() not in ["select an option", "select", "choose an option", "none"]
                ]
                options_str = "".join([f' "{o}",' for o in options_text])
                prev_answer = selected_option

                needs_answer = overwrite_previous_answers or not selected_option or selected_option.lower() in ["select an option", "select", "choose an option"]

                if needs_answer and options_text:
                    answer = ""
                    # Fast paths
                    if 'email' in label:
                        answer = email or prev_answer
                    elif 'country code' in label or ('phone' in label and 'code' in label):
                        answer = "India (+91)"
                    elif 'gender' in label or 'sex' in label:
                        answer = gender
                    elif 'disability' in label:
                        answer = disability_status
                    elif 'proficiency' in label:
                        answer = 'Professional'
                    elif any(loc_word in label for loc_word in ['location', 'city', 'state', 'country']):
                        if 'country' in label:
                            answer = country
                        elif 'state' in label:
                            answer = state
                        elif 'city' in label:
                            answer = current_city if current_city else work_location
                        else:
                            answer = work_location
                    elif 'sponsorship' in label or 'require visa' in label:
                        answer = "No" if require_visa == "No" else "Yes"
                    elif 'authorized to work' in label or 'legally authorized' in label:
                        answer = "Yes"
                    else:
                        common = answer_common_questions(label, "")
                        if common:
                            answer = common

                    # If no fast-path match or not in options, USE LLM
                    has_matching = any(answer.lower() in opt.lower() or opt.lower() in answer.lower() for opt in options_text) if answer else False
                    if not has_matching and use_AI and aiClient:
                        try:
                            ai_choice = ask_llm(
                                question=label_org,
                                options=options_text,
                                question_type='single_select',
                                job_description=job_description
                            )
                            if ai_choice:
                                print_lg(f'AI selected dropdown option for "{label_org}": "{ai_choice}"')
                                answer = ai_choice
                        except Exception as e:
                            print_lg(f"AI dropdown selection failed: {e}")

                    # Select option in dropdown
                    found_opt = False
                    if answer:
                        for opt in sel_obj.options:
                            if opt.text.strip().lower() == answer.lower():
                                sel_obj.select_by_visible_text(opt.text)
                                answer = opt.text
                                found_opt = True
                                break
                        if not found_opt:
                            for opt in sel_obj.options:
                                opt_t = opt.text.strip()
                                if answer.lower() in opt_t.lower() or opt_t.lower() in answer.lower():
                                    sel_obj.select_by_visible_text(opt_t)
                                    answer = opt_t
                                    found_opt = True
                                    break

                    if not found_opt and len(sel_obj.options) > 1:
                        for i, opt in enumerate(sel_obj.options):
                            if opt.text.strip().lower() not in ["select an option", "select", "choose an option"]:
                                sel_obj.select_by_index(i)
                                answer = opt.text.strip()
                                found_opt = True
                                break
                        if not found_opt:
                            sel_obj.select_by_index(1)
                            answer = sel_obj.first_selected_option.text.strip()

                questions_list.add((f'{label_org} [ {options_str} ]', answer if needs_answer else prev_answer, "select", prev_answer))
                continue

            # ----------------- Check if it's a radio Question -----------------
            radio = None
            if Question.tag_name.lower() == "fieldset":
                radio = Question
            else:
                radio = try_xp(Question, ".//fieldset", False)

            if radio:
                try:
                    ctrl_id = radio.id
                except Exception:
                    ctrl_id = id(radio)
                if ctrl_id in handled_controls:
                    continue
                handled_controls.add(ctrl_id)

                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", radio)
                    sleep(0.1)
                except Exception:
                    pass

                label_org = extract_question_label(radio, "Radio Question")
                label = label_org.lower()

                radio_inputs = radio.find_elements(By.XPATH, ".//input[@type='radio']")
                options_info = []
                prev_answer = None

                for r_inp in radio_inputs:
                    r_id = r_inp.get_attribute("id")
                    lbl_el = None
                    if r_id:
                        try:
                            lbl_el = radio.find_element(By.XPATH, f".//label[@for='{r_id}']")
                        except Exception:
                            pass
                    if not lbl_el:
                        try:
                            lbl_el = r_inp.find_element(By.XPATH, "./following-sibling::label | ./ancestor::label")
                        except Exception:
                            pass
                    r_text = lbl_el.text.strip() if lbl_el else (r_inp.get_attribute("value") or "Unknown")
                    is_sel = r_inp.is_selected()
                    if is_sel:
                        prev_answer = r_text
                    options_info.append((r_inp, lbl_el, r_text, is_sel))

                needs_answer = overwrite_previous_answers or (prev_answer is None)

                if needs_answer and options_info:
                    answer = ""
                    option_texts = [info[2] for info in options_info]

                    # Fast paths
                    if 'citizenship' in label or 'employment eligibility' in label:
                        answer = us_citizenship
                    elif 'veteran' in label or 'protected' in label:
                        answer = veteran_status
                    elif 'disability' in label or 'handicapped' in label:
                        answer = disability_status
                    elif 'sponsorship' in label or 'require visa' in label:
                        answer = "No" if require_visa == "No" else "Yes"
                    elif 'authorized to work' in label or 'legally authorized' in label:
                        answer = "Yes"
                    elif 'background check' in label or 'drug test' in label:
                        answer = "Yes"
                    elif 'commute' in label or 'relocate' in label:
                        answer = "Yes"
                    elif 'completed' in label and 'bachelor' in label:
                        answer = "Yes"
                    else:
                        common = answer_common_questions(label, "")
                        if common:
                            answer = common

                    # If no match, USE LLM
                    has_matching = any(answer.lower() in opt.lower() or opt.lower() in answer.lower() for opt in option_texts) if answer else False
                    if not has_matching and use_AI and aiClient:
                        try:
                            ai_choice = ask_llm(
                                question=label_org,
                                options=option_texts,
                                question_type='single_select',
                                job_description=job_description
                            )
                            if ai_choice:
                                print_lg(f'AI selected radio option for "{label_org}": "{ai_choice}"')
                                answer = ai_choice
                        except Exception as e:
                            print_lg(f"AI radio selection failed: {e}")

                    # Click matching radio button
                    clicked = False
                    if answer:
                        for r_inp, lbl_el, r_text, _ in options_info:
                            if answer.lower() == r_text.lower() or answer.lower() in r_text.lower() or r_text.lower() in answer.lower():
                                target = lbl_el if lbl_el else r_inp
                                try:
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                                    target.click()
                                except Exception:
                                    driver.execute_script("arguments[0].click();", target)
                                answer = r_text
                                clicked = True
                                break

                    if not clicked and options_info:
                        target = options_info[0][1] if options_info[0][1] else options_info[0][0]
                        try:
                            target.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", target)
                        answer = options_info[0][2]

                questions_list.add((f'{label_org} [ {", ".join([i[2] for i in options_info])} ]', answer if needs_answer else prev_answer, "radio", prev_answer))
                continue

            # ----------------- Check if it's a textarea Question -----------------
            text_area = None
            if Question.tag_name.lower() == "textarea":
                text_area = Question
            else:
                text_area = try_xp(Question, ".//textarea", False)

            if text_area:
                try:
                    ctrl_id = text_area.id
                except Exception:
                    ctrl_id = id(text_area)
                if ctrl_id in handled_controls:
                    continue
                handled_controls.add(ctrl_id)

                label_org = extract_question_label(Question, "Textarea Question")
                label = label_org.lower()

                prev_answer = text_area.get_attribute("value") or ""
                if is_placeholder_answer(prev_answer):
                    prev_answer = ""

                needs_answer = overwrite_previous_answers or not prev_answer

                if needs_answer:
                    answer = ""
                    if 'summary' in label:
                        answer = linkedin_summary
                    elif 'cover' in label:
                        answer = cover_letter
                    else:
                        answer = answer_resume_specific_question(label_org, "textarea")

                    # If empty, USE LLM!
                    if not answer and use_AI and aiClient:
                        try:
                            ai_resp = ask_llm(
                                question=label_org,
                                question_type='textarea',
                                job_description=job_description
                            )
                            if ai_resp:
                                answer = ai_resp
                                print_lg(f'AI answered textarea question "{label_org}":\n{answer}')
                        except Exception as e:
                            print_lg(f"AI failed for textarea: {e}")

                    if not answer:
                        answer = linkedin_summary

                    safe_fill_input(driver, text_area, str(answer))

                questions_list.add((label, text_area.get_attribute("value"), "textarea", prev_answer))
                continue

            # ----------------- Check if it's a text / numeric input Question -----------------
            text = None
            if Question.tag_name.lower() == "input" and (Question.get_attribute("type") or "text").lower() not in ["checkbox", "radio", "hidden", "submit", "button", "file"]:
                text = Question
            else:
                text = try_xp(Question, ".//input[not(@type) or @type='text' or @type='number' or @type='tel' or @type='email']", False)

            if text:
                try:
                    ctrl_id = text.id
                except Exception:
                    ctrl_id = id(text)
                if ctrl_id in handled_controls:
                    continue
                handled_controls.add(ctrl_id)

                label_org = extract_question_label(Question, "Text Question")
                label = label_org.lower()

                prev_answer = text.get_attribute("value") or ""
                if is_placeholder_answer(prev_answer):
                    prev_answer = ""

                needs_answer = overwrite_previous_answers or not prev_answer

                if needs_answer:
                    answer = ""
                    do_actions = False

                    # 1. Exact fast paths
                    if 'phone' in label or 'mobile' in label:
                        answer = phone_number
                    elif 'street' in label:
                        answer = street
                    elif 'city' in label or 'location' in label or 'address' in label:
                        answer = current_city if current_city else work_location
                        do_actions = True
                    elif 'signature' in label or ('full' in label and 'name' in label):
                        answer = full_name
                    elif 'first' in label and 'name' in label and 'last' not in label:
                        answer = first_name
                    elif 'middle' in label and 'name' in label and 'last' not in label:
                        answer = middle_name
                    elif 'last' in label and 'name' in label and 'first' not in label:
                        answer = last_name
                    elif 'employer' in label or ('company' in label and ('current' in label or 'recent' in label)):
                        answer = recent_employer
                    elif 'linkedin' in label:
                        answer = linkedIn
                    elif 'website' in label or 'portfolio' in label or 'blog' in label:
                        answer = website
                    elif 'state' in label or 'province' in label:
                        answer = state
                    elif 'zip' in label or 'postal' in label or 'code' in label:
                        answer = zipcode
                    elif 'country' in label:
                        answer = country
                    elif 'notice' in label:
                        if 'month' in label:
                            answer = notice_period_months
                        elif 'week' in label:
                            answer = notice_period_weeks
                        else:
                            answer = notice_period
                    elif 'salary' in label or 'ctc' in label or 'compensation' in label or 'pay' in label:
                        if 'current' in label or 'present' in label:
                            if 'month' in label:
                                answer = current_ctc_monthly
                            elif 'lakh' in label:
                                answer = current_ctc_lakhs
                            else:
                                answer = current_ctc
                        else:
                            if 'month' in label:
                                answer = desired_salary_monthly
                            elif 'lakh' in label:
                                answer = desired_salary_lakhs
                            else:
                                answer = desired_salary
                    elif 'scale of 1-10' in label:
                        answer = confidence_level
                    elif 'headline' in label:
                        answer = linkedin_headline
                    elif ('hear' in label or 'come across' in label) and 'this' in label:
                        answer = "LinkedIn"
                    else:
                        answer = answer_common_questions(label, "")

                    # 2. Experience questions
                    if ('experience' in label or 'years' in label) and not answer:
                        matched_exp = answer_experience_question(label)
                        if matched_exp and matched_exp != "":
                            answer = matched_exp
                        else:
                            # Use LLM to accurately extract experience number from profile
                            if use_AI and aiClient:
                                try:
                                    ai_resp = ask_llm(
                                        question=label_org,
                                        question_type='text',
                                        job_description=job_description
                                    )
                                    m_num = re.search(r'\b\d+(\.\d+)?\b', ai_resp)
                                    if m_num:
                                        answer = m_num.group(0)
                                        print_lg(f'AI answered experience question "{label_org}": {answer}')
                                    elif ai_resp:
                                        answer = ai_resp
                                except Exception as e:
                                    print_lg(f"AI failed for experience question: {e}")

                    # 3. Resume-specific custom questions
                    if not answer:
                        answer = answer_resume_specific_question(label_org, "text")

                    # 4. Fallback for any other unanswered field: USE LLM!
                    if not answer and use_AI and aiClient:
                        try:
                            ai_resp = ask_llm(
                                question=label_org,
                                question_type='text',
                                job_description=job_description
                            )
                            if ai_resp:
                                answer = ai_resp
                                print_lg(f'AI answered text question "{label_org}": {answer}')
                        except Exception as e:
                            print_lg(f"AI failed for text question: {e}")

                    # 5. Final fallback
                    if not answer:
                        answer = years_of_experience

                    safe_fill_input(driver, text, str(answer))

                    if do_actions:
                        try:
                            sleep(0.5)
                            actions.send_keys(Keys.ARROW_DOWN).send_keys(Keys.ENTER).perform()
                        except Exception:
                            pass

                questions_list.add((label, text.get_attribute("value"), "text", prev_answer))
                continue

            # ----------------- Check if it's a checkbox Question -----------------
            checkbox = None
            if Question.tag_name.lower() == "input" and (Question.get_attribute("type") or "").lower() == "checkbox":
                checkbox = Question
            else:
                checkbox = try_xp(Question, ".//input[@type='checkbox']", False)

            if checkbox:
                try:
                    ctrl_id = checkbox.id
                except Exception:
                    ctrl_id = id(checkbox)
                if ctrl_id in handled_controls:
                    continue
                handled_controls.add(ctrl_id)

                label_org = extract_question_label(Question, "Checkbox")
                label = label_org.lower()
                prev_answer = checkbox.is_selected()
                checked = prev_answer

                if not prev_answer:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                        checkbox.click()
                        checked = True
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", checkbox)
                            checked = True
                        except Exception:
                            pass

                questions_list.add((label, checked, "checkbox", prev_answer))
                continue

        except Exception as q_err:
            print_lg(f"Error handling form element: {q_err}")

    # Select today's date if date picker is active
    try_xp(driver, "//button[contains(@aria-label, 'This is today')]")

    return questions_list





def external_apply(pagination_element: WebElement, job_id: str, job_link: str, resume: str, date_listed, application_link: str, screenshot_name: str) -> tuple[bool, str, int]:
    '''
    Function to open new tab and save external job application links
    '''
    global tabs_count, dailyEasyApplyLimitReached
    if easy_apply_only:
        try:
            if "exceeded the daily application limit" in driver.find_element(By.CLASS_NAME, "artdeco-inline-feedback__message").text: dailyEasyApplyLimitReached = True
        except: pass
        print_lg("Easy apply failed I guess!")
        if pagination_element != None: return True, application_link, tabs_count
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3')]"))).click() # './/button[contains(span, "Apply") and not(span[contains(@class, "disabled")])]'
        wait_span_click(driver, "Continue", 1, True, False)
        windows = driver.window_handles
        tabs_count = len(windows)
        driver.switch_to.window(windows[-1])
        application_link = driver.current_url
        print_lg('Got the external application link "{}"'.format(application_link))
        if close_tabs and driver.current_window_handle != linkedIn_tab: driver.close()
        driver.switch_to.window(linkedIn_tab)
        return False, application_link, tabs_count
    except Exception as e:
        # print_lg(e)
        print_lg("Failed to apply!")
        failed_job(job_id, job_link, resume, date_listed, "Probably didn't find Apply button or unable to switch tabs.", e, application_link, screenshot_name)
        global failed_count
        failed_count += 1
        return True, application_link, tabs_count



def follow_company(modal: WebDriver = driver) -> None:
    '''
    Function to follow or un-follow easy applied companies based on `follow_companies`.
    Default setting is follow_companies = False (uncheck the follow box).
    '''
    global follow_companies
    try:
        want_follow = bool(follow_companies)
        
        # 1. Multi-strategy JavaScript uncheck: searches all inputs, labels, and artdeco containers
        js_uncheck = """
            var wantFollow = arguments[0];
            var res = { status: 'not_found' };

            // Priority 0: Modern LinkedIn div[role="checkbox"] container
            var roleCheckbox = document.querySelector('div[role="checkbox"][aria-label*="Follow" i], [role="checkbox"][aria-label*="follow" i]');
            if (roleCheckbox) {
                targetLbl = roleCheckbox;
                targetInp = roleCheckbox.querySelector('input[type="checkbox"]');
            }

            // Find all potential checkboxes
            if (!targetInp || !targetLbl) {
                var allInps = document.querySelectorAll('input[type="checkbox"]');
                for (var i = 0; i < allInps.length; i++) {
                    var inp = allInps[i];
                    var id = (inp.id || '').toLowerCase();
                    var name = (inp.name || '').toLowerCase();
                    if (id.includes('follow') || name.includes('follow')) {
                        targetInp = inp;
                        if (inp.id) {
                            targetLbl = document.querySelector('label[for="' + inp.id + '"]');
                        }
                        break;
                    }
                }
            // Search by label/span text
            if (!targetInp || !targetLbl) {
                var allEls = document.querySelectorAll('label, div.artdeco-checkbox, div[role="checkbox"], span');
                for (var j = 0; j < allEls.length; j++) {
                    var el = allEls[j];
                    var txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                    if (txt.includes('follow') && (txt.includes('stay up to date') || txt.includes('page') || txt.includes('updates'))) {
                        if (el.tagName.toLowerCase() === 'label') {
                            targetLbl = el;
                        } else {
                            targetLbl = el.querySelector('label') || el;
                        }
                        if (!targetInp) {
                            var forId = targetLbl ? targetLbl.getAttribute('for') : null;
                            if (forId) targetInp = document.getElementById(forId);
                            if (!targetInp) targetInp = el.querySelector('input[type="checkbox"]') || (el.parentElement ? el.parentElement.querySelector('input[type="checkbox"]') : null);
                        }
                        break;
                    }
                }
            }

            if (targetInp || targetLbl) {
                var isChecked = targetInp ? targetInp.checked : true;
                if (targetLbl && !targetInp) {
                    var aria = targetLbl.getAttribute('aria-checked');
                    if (aria === 'false') isChecked = false;
                }

                if (isChecked !== wantFollow) {
                    var clickTarget = targetLbl || targetInp;
                    clickTarget.scrollIntoView({block: 'center'});
                    clickTarget.click();

                    // If native input still hasn't flipped, click native input directly
                    if (targetInp && targetInp.checked !== wantFollow) {
                        targetInp.click();
                    }

                    // Strict enforcement: if we want it unchecked and it's still checked, force uncheck
                    if (!wantFollow && targetInp && targetInp.checked) {
                        targetInp.checked = false;
                        targetInp.dispatchEvent(new Event('input', { bubbles: true }));
                        targetInp.dispatchEvent(new Event('change', { bubbles: true }));
                    }

                    res.status = 'toggled';
                    res.before = isChecked;
                    res.after = targetInp ? targetInp.checked : !wantFollow;
                    return res;
                } else {
                    res.status = 'already_' + (wantFollow ? 'checked' : 'unchecked');
                    return res;
                }
            }

            return res;
        """
        result = driver.execute_script(js_uncheck, want_follow)
        if isinstance(result, dict):
            status = result.get('status', '')
            if status == 'toggled':
                print_lg(f"Successfully unchecked 'Follow company' checkbox (was checked, now unchecked).")
                return
            elif status == 'already_unchecked':
                print_lg("'Follow company' checkbox is already unchecked.")
                return
            else:
                print_lg(f"Follow company checkbox status: {status}")

        # 2. Selenium fallback search
        root = modal if modal else driver
        for lx in [
            ".//label[contains(., 'Follow') and (contains(., 'stay up to date') or contains(., 'page'))]",
            "//dialog//label[contains(., 'Follow') and (contains(., 'stay up to date') or contains(., 'page'))]",
            ".//label[contains(@for, 'follow-company')]",
            "//dialog//label[contains(@for, 'follow-company')]",
            "//label[contains(., 'Follow')]",
        ]:
            try:
                for lbl in root.find_elements(By.XPATH, lx):
                    if lbl.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", lbl)
                        lbl.click()
                        print_lg(f"Clicked follow company label via Selenium fallback ({lx})")
                        return
            except Exception:
                pass
    except Exception as e:
        print_lg("Failed to update follow companies checkbox!", e)


    


#< Failed attempts logging
def failed_job(job_id: str, job_link: str, resume: str, date_listed, error: str, exception: Exception, application_link: str, screenshot_name: str) -> None:
    '''
    Function to update failed jobs list in excel
    '''
    try:
        with open(failed_file_name, 'a', newline='', encoding='utf-8') as file:
            fieldnames = ['Job ID', 'Job Link', 'Resume Tried', 'Date listed', 'Date Tried', 'Assumed Reason', 'Stack Trace', 'External Job link', 'Screenshot Name']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':truncate_for_csv(job_id), 'Job Link':truncate_for_csv(job_link), 'Resume Tried':truncate_for_csv(resume), 'Date listed':truncate_for_csv(date_listed), 'Date Tried':datetime.now(), 'Assumed Reason':truncate_for_csv(error), 'Stack Trace':truncate_for_csv(exception), 'External Job link':truncate_for_csv(application_link), 'Screenshot Name':truncate_for_csv(screenshot_name)})
            file.close()
    except Exception as e:
        print_lg("Failed to update failed jobs list!", e)
        pyautogui.alert("Failed to update the excel of failed jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")


def screenshot(driver: WebDriver, job_id: str, failedAt: str) -> str:
    '''
    Function to to take screenshot for debugging
    - Returns screenshot name as String
    '''
    screenshot_name = "{} - {} - {}.png".format( job_id, failedAt, str(datetime.now()) )
    path = logs_folder_path+"/screenshots/"+screenshot_name.replace(":",".")
    # special_chars = {'*', '"', '\\', '<', '>', ':', '|', '?'}
    # for char in special_chars:  path = path.replace(char, '-')
    driver.save_screenshot(path.replace("//","/"))
    return screenshot_name
#>



def submitted_jobs(job_id: str, title: str, company: str, work_location: str, work_style: str, description: str, experience_required: int | Literal['Unknown', 'Error in extraction'], 
                   skills: list[str] | Literal['In Development'], hr_name: str | Literal['Unknown'], hr_link: str | Literal['Unknown'], resume: str, 
                   reposted: bool, date_listed: datetime | Literal['Unknown'], date_applied:  datetime | Literal['Pending'], job_link: str, application_link: str, 
                   questions_list: set | None, connect_request: Literal['In Development']) -> None:
    '''
    Function to create or update the Applied jobs CSV file, once the application is submitted successfully
    '''
    try:
        with open(file_name, mode='a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'About Job', 'Experience required', 'Skills required', 'HR Name', 'HR Link', 'Resume', 'Re-posted', 'Date Posted', 'Date Applied', 'Job Link', 'External Job link', 'Questions Found', 'Connect Request']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':truncate_for_csv(job_id), 'Title':truncate_for_csv(title), 'Company':truncate_for_csv(company), 'Work Location':truncate_for_csv(work_location), 'Work Style':truncate_for_csv(work_style), 
                            'About Job':truncate_for_csv(description), 'Experience required': truncate_for_csv(experience_required), 'Skills required':truncate_for_csv(skills), 
                                'HR Name':truncate_for_csv(hr_name), 'HR Link':truncate_for_csv(hr_link), 'Resume':truncate_for_csv(resume), 'Re-posted':truncate_for_csv(reposted), 
                                'Date Posted':truncate_for_csv(date_listed), 'Date Applied':truncate_for_csv(date_applied), 'Job Link':truncate_for_csv(job_link), 
                                'External Job link':truncate_for_csv(application_link), 'Questions Found':truncate_for_csv(questions_list), 'Connect Request':truncate_for_csv(connect_request)})
        csv_file.close()
    except Exception as e:
        print_lg("Failed to update submitted jobs list!", e)
        pyautogui.alert("Failed to update the excel of applied jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")




def discard_job() -> None:
    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        sleep(0.3)
    except Exception:
        pass
    for btn_xpath in [
        "//button[normalize-space()='Discard' or contains(., 'Discard')]",
        "//button[contains(@aria-label, 'Dismiss')]",
    ]:
        try:
            for b in driver.find_elements(By.XPATH, btn_xpath):
                if b.is_displayed():
                    b.click()
                    sleep(0.3)
                    break
        except Exception:
            pass
    dismiss_feedback_modal()


# Function to apply to jobs
def apply_to_jobs(search_terms: list[str]) -> None:
    applied_jobs = get_applied_job_ids()
    rejected_jobs = set()
    blacklisted_companies = set()
    global current_city, failed_count, skip_count, easy_applied_count, external_jobs_count, tabs_count, pause_before_submit, pause_at_failed_question, useNewResume, dailyEasyApplyLimitReached
    current_city = current_city.strip()

    if randomize_search_order:  shuffle(search_terms)
    for searchTerm in search_terms:
        # Build search URL with all user filters encoded as parameters (server-side filter application)
        search_url = build_linkedin_search_url(searchTerm)
        driver.get(search_url)
        print_lg("\n________________________________________________________________________________________________________________________\n")
        print_lg(f'\n>>>> Now searching for "{searchTerm}" <<<<\n\n')
        print_lg(f'Search URL with filters: {search_url}')

        try:
            # Confirm window is alive and page body is present
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            sleep(1.5)
            dismiss_feedback_modal()
            apply_filters()
            dismiss_feedback_modal()
        except (NoSuchWindowException, WebDriverException) as e:
            print_lg("Browser window closed or session is invalid. Ending application process.", e)
            raise e

        # Dump left rail HTML for inspection
        try:
            left_rail_el = driver.find_element(By.XPATH, "//div[contains(@class, 'scaffold-layout__list')] | //div[contains(@class, 'jobs-search-results-list')] | //main")
            dom_html = left_rail_el.get_attribute("outerHTML")
            dom_file = os.path.join(logs_folder_path, "left_rail_dom.html").replace("\\", "/")
            with open(dom_file, "w", encoding="utf-8") as f:
                f.write(dom_html)
            print_lg(f"Saved left rail DOM to {dom_file} ({len(dom_html)} chars)")
        except Exception as e:
            pass

        current_count = 0
        try:
            while current_count < switch_number:
                dismiss_feedback_modal()
                # Wait up to 12 seconds for genuine job cards to render in the DOM
                job_listings = []
                for attempt in range(12):
                    dismiss_feedback_modal()
                    raw_listings = []
                    for selector in [
                        (By.XPATH, "//div[@role='button' and starts-with(@componentkey, 'job-card-component-ref-')]"),
                        (By.XPATH, "//div[starts-with(@componentkey, 'job-card-component-ref-')]"),
                        (By.CSS_SELECTOR, "div[role='button'][componentkey^='job-card-component-ref-']"),
                        (By.CSS_SELECTOR, "div[componentkey^='job-card-component-ref-']"),
                        (By.XPATH, "//div[contains(@class, 'scaffold-layout__list')]//div[contains(@class, 'job-card-job-posting-card-wrapper')]"),
                        (By.XPATH, "//div[contains(@class, 'scaffold-layout__list')]//div[contains(@class, 'job-card-container')]"),
                        (By.XPATH, "//div[contains(@class, 'scaffold-layout__list')]//div[@data-job-id]"),
                        (By.XPATH, "//div[contains(@class, 'scaffold-layout__list')]//div[@data-view-name='job-card']"),
                        (By.XPATH, "//div[contains(@class, 'scaffold-layout__list')]//li"),
                        (By.XPATH, "//div[contains(@class, 'jobs-search-results-list')]//li"),
                        (By.XPATH, "//div[contains(@class, 'jobs-search-results-list')]//div[contains(@class, 'job-card')]"),
                        (By.XPATH, "//ul[contains(@class, 'scaffold-layout__list-container')]/li"),
                        (By.XPATH, "//li[@data-occludable-job-id]"),
                        (By.XPATH, "//li[contains(@class, 'jobs-search-results__list-item')]"),
                        (By.XPATH, "//li[contains(@class, 'scaffold-layout__list-item')]"),
                        (By.XPATH, "//div[contains(@class, 'scaffold-layout__list') or contains(@class, 'jobs-search-results')]//a[contains(@href, '/jobs/view/')]"),
                        (By.XPATH, "//a[contains(@href, '/jobs/view/')]"),
                    ]:
                        try:
                            elements = driver.find_elements(*selector)
                            if elements:
                                raw_listings = elements
                                break
                        except Exception:
                            continue

                    if raw_listings:
                        seen_keys = set()
                        for j in raw_listings:
                            try:
                                text = j.text.strip()
                                lines = [l.strip() for l in text.split("\n") if l.strip() and l.strip() != '·']
                                raw_title = lines[0] if lines else ""
                                # Filter out generic UI buttons/artifacts like More, Dismiss, Cancel, Feedback
                                if raw_title.lower() in ('more', 'see more', 'dismiss', 'close', 'cancel', 'send', 'feedback', 'are these results helpful?'):
                                    continue

                                ck = j.get_dom_attribute('componentkey') or ""
                                m_ck = re.search(r'ref-(\d+)', ck)
                                if m_ck:
                                    j_id = m_ck.group(1)
                                else:
                                    j_id = j.get_attribute('data-job-id') or j.get_attribute('data-occludable-job-id')

                                if not j_id:
                                    href = j.get_attribute('href') or ""
                                    m = re.search(r'/jobs/view/(\d+)', href)
                                    if m:
                                        j_id = m.group(1)
                                    else:
                                        try:
                                            link_el = j.find_element(By.XPATH, ".//a[contains(@href, '/jobs/view/')]")
                                            href2 = link_el.get_attribute('href') or ""
                                            m2 = re.search(r'/jobs/view/(\d+)', href2)
                                            if m2:
                                                j_id = m2.group(1)
                                        except Exception:
                                            pass

                                # Valid card must have at least 2 lines (title and company) or a genuine job ID
                                if len(lines) >= 2 or (j_id and len(raw_title) >= 3):
                                    key = j_id or (lines[0] + "::" + lines[1] if len(lines) >= 2 else None)
                                    if key and key not in seen_keys:
                                        seen_keys.add(key)
                                        job_listings.append(j)
                            except Exception:
                                continue

                    if job_listings:
                        break

                    # After 2 seconds without cards, try a subtle scroll to trigger SPA lazy rendering
                    if attempt == 2 or attempt == 5:
                        try:
                            driver.execute_script("window.scrollBy(0, 150);")
                            sleep(0.5)
                            driver.execute_script("window.scrollBy(0, -150);")
                        except Exception:
                            pass
                    sleep(1.0)

                pagination_element, current_page = get_page_info()
                print_lg(f"Found {len(job_listings)} job listing(s) on current page (Page {current_page}).")  

                if not job_listings:
                    # Save diagnostic screenshot and details
                    try:
                        diag_name = f"no_jobs_{re.sub(r'[^a-zA-Z0-9]', '_', searchTerm)}_{int(datetime.now().timestamp())}.png"
                        diag_path = os.path.join(logs_folder_path, "screenshots", diag_name).replace("\\", "/")
                        os.makedirs(os.path.dirname(diag_path), exist_ok=True)
                        driver.save_screenshot(diag_path)
                        print_lg(f"Saved diagnostic screenshot: {diag_path}")
                        print_lg(f"Loaded URL: {driver.current_url}")
                        print_lg(f"Page Title: {driver.title}")
                    except Exception as diag_e:
                        print_lg(f"Diagnostic error: {diag_e}")  

            
                for job in job_listings:
                    try:
                        if keep_screen_awake: pyautogui.press('shiftright')
                        if current_count >= switch_number: break
                        print_lg("\n-@-\n")

                        (
                            job_id,
                            title,
                            company,
                            work_location,
                            work_style,
                            skip,
                            title_allowed,
                            title_reason,
                        ) = get_job_main_details(job, blacklisted_companies, rejected_jobs)
                        
                        if skip: continue
                        # Redundant fail safe check for applied jobs!
                        try:
                            if job_id in applied_jobs or find_by_class(driver, "jobs-s-apply__application-link", 2):
                                print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
                                continue
                        except Exception as e:
                            print_lg(f'Trying to Apply to "{title} | {company}" job. Job ID: {job_id}')

                        job_link = "https://www.linkedin.com/jobs/view/"+job_id
                        application_link = "Easy Applied"
                        date_applied = "Pending"
                        hr_link = "Unknown"
                        hr_name = "Unknown"
                        connect_request = "In Development" # Still in development
                        date_listed = "Unknown"
                        skills = "Needs an AI" # Still in development
                        resume = "Pending"
                        reposted = False
                        questions_list = None
                        screenshot_name = "Not Available"
                        jobs_top_card = None

                        try:
                            rejected_jobs, blacklisted_companies, jobs_top_card = check_blacklist(rejected_jobs,job_id,company,blacklisted_companies)
                        except ValueError as e:
                            print_lg(e, 'Skipping this job!\n')
                            failed_job(job_id, job_link, resume, date_listed, "Found Blacklisted words in About Company", e, "Skipped", screenshot_name)
                            skip_count += 1
                            continue
                        except Exception as e:
                            print_lg("Failed to scroll to About Company!")
                            # print_lg(e)



                        # Hiring Manager info
                        try:
                            hr_info_card = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, "hirer-card__hirer-information")))
                            hr_link = hr_info_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                            hr_name = hr_info_card.find_element(By.TAG_NAME, "span").text
                            # if connect_hr:
                            #     driver.switch_to.new_window('tab')
                            #     driver.get(hr_link)
                            #     wait_span_click("More")
                            #     wait_span_click("Connect")
                            #     wait_span_click("Add a note")
                            #     message_box = driver.find_element(By.XPATH, "//textarea")
                            #     message_box.send_keys(connect_request_message)
                            #     if close_tabs: driver.close()
                            #     driver.switch_to.window(linkedIn_tab) 
                            # def message_hr(hr_info_card):
                            #     if not hr_info_card: return False
                            #     hr_info_card.find_element(By.XPATH, ".//span[normalize-space()='Message']").click()
                            #     message_box = driver.find_element(By.XPATH, "//div[@aria-label='Write a message…']")
                            #     message_box.send_keys()
                            #     try_xp(driver, "//button[normalize-space()='Send']")        
                        except Exception as e:
                            print_lg(f'HR info was not given for "{title}" with Job ID: {job_id}!')
                            # print_lg(e)


                        # Calculation of date posted
                        try:
                            time_el = None
                            if jobs_top_card is None:
                                jobs_top_card = try_find_by_classes(
                                    driver,
                                    [
                                        "job-details-jobs-unified-top-card__primary-description-container",
                                        "job-details-jobs-unified-top-card__primary-description",
                                        "jobs-unified-top-card__primary-description",
                                        "jobs-details__main-content",
                                    ],
                                )
                            if jobs_top_card:
                                try:
                                    time_el = jobs_top_card.find_element(By.XPATH, './/span[contains(normalize-space(), " ago")]')
                                except Exception:
                                    pass
                            if not time_el:
                                try:
                                    time_el = driver.find_element(By.XPATH, '//span[contains(normalize-space(), " ago")] | //span[contains(normalize-space(), "Posted ")]')
                                except Exception:
                                    pass
                            if time_el:
                                time_posted_text = time_el.text
                                print("Time Posted: " + time_posted_text)
                                if "Reposted" in time_posted_text:
                                    reposted = True
                                    time_posted_text = time_posted_text.replace("Reposted", "")
                                date_listed = calculate_date_posted(time_posted_text.strip())
                        except Exception as e:
                            print_lg("Failed to calculate the date posted!", e)


                        description, experience_required, skip, reason, message = get_job_description(
                            title,
                            title_allowed,
                            title_reason,
                        )
                        if skip:
                            print_lg(message)
                            failed_job(job_id, job_link, resume, date_listed, reason, message, "Skipped", screenshot_name)
                            rejected_jobs.add(job_id)
                            skip_count += 1
                            continue

                        


                        # Check for LinkedIn fast-pace / rate limit warning banner
                        try:
                            error_banners = driver.find_elements(By.XPATH, "//div[contains(@class, 'artdeco-inline-feedback--error')] | //p[contains(., 'fast pace')] | //span[contains(., 'fast pace')] | //div[contains(., 'safeguard against automated')]")
                            for eb in error_banners:
                                eb_text = eb.text.lower()
                                if "fast pace" in eb_text or "paused easy apply" in eb_text or "safeguard against automated" in eb_text or "inauthentic" in eb_text:
                                    print_lg("\n" + "!"*75)
                                    print_lg("🚨 [RATE LIMIT DETECTED] LinkedIn has temporarily paused Easy Apply (fast pace safeguard).")
                                    print_lg("To protect your account from restriction, pausing bot execution.")
                                    print_lg("LinkedIn cooldown period is usually 1-2 hours. Please try again later.")
                                    print_lg("!"*75 + "\n")
                                    dailyEasyApplyLimitReached = True
                                    return
                        except Exception:
                            pass

                        uploaded = False
                        # Case 1: Easy Apply Button (matches both new and old LinkedIn UI)
                        easy_btn = None
                        for ea_xpath in [
                            "//button[@aria-label='Easy Apply to this job' or contains(@aria-label, 'Easy Apply to')]",
                            "//button[contains(@class, 'jobs-apply-button')]",
                            "//div[contains(@class, 'jobs-details') or contains(@class, 'scaffold-layout__detail')]//button[contains(., 'Easy Apply')]",
                            "//button[contains(., 'Easy Apply') and not(contains(@aria-label, 'filter')) and not(ancestor::nav)]",
                        ]:
                            try:
                                btn_cand = driver.find_element(By.XPATH, ea_xpath)
                                if btn_cand and btn_cand.is_displayed():
                                    easy_btn = btn_cand
                                    break
                            except Exception:
                                pass

                        if easy_btn:
                            try: 
                                try:
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easy_btn)
                                    driver.execute_script("arguments[0].click();", easy_btn)
                                except Exception:
                                    easy_btn.click()

                                modal = wait_for_modal_ready(driver, 8.0)
                                if not modal:
                                    for _ in range(8):
                                        try:
                                            m_cand = driver.find_element(By.XPATH, "//dialog | //div[contains(@class, 'jobs-easy-apply-modal')] | //div[@role='dialog']")
                                            if m_cand and m_cand.is_displayed():
                                                modal = m_cand
                                                break
                                        except Exception:
                                            pass
                                        sleep(0.1)

                                if not modal:
                                    raise Exception("Could not find Easy Apply modal dialog after clicking apply button")

                                errored = ""
                                try:
                                    resume = "Previous resume"
                                    questions_list = set()
                                    next_counter = 0
                                    while next_counter < 15:
                                        next_counter += 1

                                        questions_list = answer_questions(modal, questions_list, work_location, job_description=description)
                                        if useNewResume and not uploaded:
                                            uploaded, resume = upload_resume(modal, default_resume_path)

                                        clicked, btn_type = find_and_click_next_or_review(driver, modal)
                                        if not clicked:
                                            break
                                        if btn_type in ["review", "submit"]:
                                            break

                                        # Fast-wait for next step modal to be ready (50ms polling)
                                        modal = wait_for_modal_ready(driver, 6.0)
                                        if not modal:
                                            break

                                    if next_counter >= 15:
                                        if pause_at_failed_question and not auto_submit:
                                            screenshot(driver, job_id, "Needed manual intervention for failed question")
                                            pyautogui.alert("Couldn't answer one or more questions.\nPlease click \"Continue\" once done.\nDO NOT CLICK Back, Next or Review button in LinkedIn.\n\n\n\n\nYou can turn off \"Pause at failed question\" setting in config.py", "Help Needed", "Continue")
                                        else:
                                            if questions_list: print_lg("Stuck for one or some of the following questions...", questions_list)
                                            screenshot_name = screenshot(driver, job_id, "Failed at questions")
                                            errored = "stuck"
                                            raise Exception("Seems like stuck in a continuous loop of next, probably because of new questions.")

                                except NoSuchElementException: errored = "nose"
                                finally:
                                    if questions_list and errored != "stuck": 
                                        print_lg("Answered the following questions...", questions_list)
                                        print("\n\n" + "\n".join(str(question) for question in questions_list) + "\n\n")
                                    # Wait for the Review / Submit screen to be fully loaded!
                                    modal = wait_for_submit_ready(driver, 6.0) or wait_for_modal_ready(driver, 6.0) or modal
                                    try:
                                        follow_company(modal or driver)
                                    except Exception as e:
                                        print_lg("Error updating follow company checkbox:", e)
                                    cur_pause_before_submit = pause_before_submit and not auto_submit
                                    if errored != "stuck" and cur_pause_before_submit:
                                        decision = pyautogui.confirm('1. Please verify your information.\n2. If you edited something, please return to this final screen.\n3. DO NOT CLICK "Submit Application".\n\n\n\n\nYou can turn off "Pause before submit" setting in config.py\nTo TEMPORARILY disable pausing, click "Disable Pause"', "Confirm your information",["Disable Pause", "Discard Application", "Submit Application"])
                                        if decision == "Discard Application": raise Exception("Job application discarded by user!")
                                        pause_before_submit = False if "Disable Pause" == decision else True
                                    try:
                                        follow_company(modal or driver)
                                    except Exception:
                                        pass
                                    submit_clicked = False
                                    for sub_xpath in [
                                        ".//button[contains(., 'Submit application') or contains(@aria-label, 'Submit application') or .//span[normalize-space()='Submit application']]",
                                        "//dialog//footer//button[contains(., 'Submit application') or contains(@aria-label, 'Submit application') or .//span[normalize-space()='Submit application']]",
                                        "//button[contains(., 'Submit application') or contains(@aria-label, 'Submit application')]",
                                    ]:
                                        try:
                                            sub_btn = (modal or driver).find_element(By.XPATH, sub_xpath)
                                            if sub_btn and sub_btn.is_displayed():
                                                try:
                                                    driver.execute_script("arguments[0].click();", sub_btn)
                                                except Exception:
                                                    sub_btn.click()
                                                submit_clicked = True
                                                break
                                        except Exception:
                                            pass

                                    if submit_clicked or wait_span_click(driver, "Submit application", 2, scrollTop=True): 
                                        date_applied = datetime.now()
                                        print_lg(f"Successfully applied to '{title} | {company}'!")
                                        easy_applied_count += 1
                                        current_count += 1
                                        sleep(1.5)
                                        if not wait_span_click(driver, "Done", 2):
                                            try:
                                                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                                            except Exception:
                                                pass
                                    elif errored != "stuck" and cur_pause_before_submit and "Yes" in pyautogui.confirm("You submitted the application, didn't you 😒?", "Failed to find Submit Application!", ["Yes", "No"]):
                                        date_applied = datetime.now()
                                        wait_span_click(driver, "Done", 2)
                                        easy_applied_count += 1
                                        current_count += 1
                                    else:
                                        print_lg("Since, Submit Application failed, discarding the job application...")
                                        if errored == "nose": raise Exception("Failed to click Submit application 😑")

                            except Exception as e:
                                print_lg("Failed to Easy apply!")
                                critical_error_log("Somewhere in Easy Apply process", e)
                                failed_job(job_id, job_link, resume, date_listed, "Problem in Easy Applying", e, application_link, screenshot_name)
                                failed_count += 1
                                discard_job()
                                continue
                        else:
                            # Case 2: Apply externally
                            skip, application_link, tabs_count = external_apply(pagination_element, job_id, job_link, resume, date_listed, application_link, screenshot_name)
                            if dailyEasyApplyLimitReached:
                                print_lg("\n###############  Daily application limit for Easy Apply is reached!  ###############\n")
                                return
                            if skip: continue

                        submitted_jobs(job_id, title, company, work_location, work_style, description, experience_required, skills, hr_name, hr_link, resume, reposted, date_listed, date_applied, job_link, application_link, questions_list, connect_request)
                        if uploaded:   useNewResume = False

                        print_lg(f'Successfully saved "{title} | {company}" job. Job ID: {job_id} info')

                        # Safe, human-like randomized delay between applications
                        base_delay = delay_between_applications if (isinstance(delay_between_applications, int) and delay_between_applications >= 15) else 35
                        actual_delay = randint(int(base_delay * 0.85), int(base_delay * 1.25))
                        print_lg(f"Waiting for {actual_delay} seconds (safe human delay) before next application...")
                        sleep(actual_delay)
                        current_count += 1
                        if application_link == "Easy Applied": easy_applied_count += 1
                        else:   external_jobs_count += 1
                        applied_jobs.add(job_id)
                    except StaleElementReferenceException:
                        print_lg(f"StaleElementReferenceException occurred for job. Skipping to next job...")
                        continue
                    except Exception as e:
                        print_lg(f"Unexpected error for job: {str(e)[:100]}")
                        continue



                # Switching to next page
                if not job_listings:
                    print_lg(f"No job listings found for '{searchTerm}'. Moving to next search term.")
                    break

                page_switched = False
                try:
                    next_page_btn = driver.find_element(By.XPATH, f"//button[@aria-label='Page {current_page+1}']")
                    scroll_to_view(driver, next_page_btn)
                    next_page_btn.click()
                    page_switched = True
                except Exception:
                    try:
                        next_btn = driver.find_element(By.XPATH, "//button[@aria-label='Next' and not(@disabled)]")
                        scroll_to_view(driver, next_btn)
                        next_btn.click()
                        page_switched = True
                    except Exception:
                        pass

                if page_switched:
                    print_lg(f"\n>-> Successfully navigated to Page {current_page+1} \n")
                    buffer(click_gap)
                else:
                    print_lg(f"Reached the end of pagination for '{searchTerm}'.")
                    break

        except (NoSuchWindowException, WebDriverException) as e:
            print_lg("Browser window closed or session is invalid. Ending application process.", e)
            raise e # Re-raise to be caught by main
        except Exception as e:
            print_lg("Failed to find Job listings!")
            critical_error_log("In Applier", e)
            try:
                print_lg(driver.page_source, pretty=True)
            except Exception as page_source_error:
                print_lg(f"Failed to get page source, browser might have crashed. {page_source_error}")
            # print_lg(e)

        
def run(total_runs: int) -> int:
    if dailyEasyApplyLimitReached:
        return total_runs
    print_lg("\n########################################################################################################################\n")
    print_lg(f"Date and Time: {datetime.now()}")
    print_lg(f"Cycle number: {total_runs}")
    print_lg(f"Currently looking for jobs posted within '{date_posted}' and sorting them by '{sort_by}'")
    apply_to_jobs(search_terms)
    print_lg("########################################################################################################################\n")
    if not dailyEasyApplyLimitReached:
        print_lg(f"Cycle completed. Waiting for {cycle_delay} seconds before next cycle...")
        sleep(cycle_delay)
    buffer(1)
    return total_runs + 1



chatGPT_tab = False
linkedIn_tab = False

def main() -> None:
    try:
        global linkedIn_tab, tabs_count, useNewResume, aiClient
        alert_title = "Error Occurred. Closing Browser!"
        total_runs = 1        
        validate_config()
        
        if not os.path.exists(default_resume_path):
            pyautogui.alert(text='Your default resume "{}" is missing! Please update it\'s folder path "default_resume_path" in config.py\n\nOR\n\nAdd a resume with exact name and path (check for spelling mistakes including cases).\n\n\nFor now the bot will continue using your previous upload from LinkedIn!'.format(default_resume_path), title="Missing Resume", button="OK")
            useNewResume = False
        
        # Check LinkedIn login status
        tabs_count = len(driver.window_handles)
        driver.get("https://www.linkedin.com/feed/")
        sleep(2)
        if not is_logged_in_LN():
            login_LN()
        else:
            print_lg("Already logged in to LinkedIn via saved profile!")
        
        linkedIn_tab = driver.current_window_handle

        # # Login to ChatGPT in a new tab for resume customization
        # if use_resume_generator:
        #     try:
        #         driver.switch_to.new_window('tab')
        #         driver.get("https://chat.openai.com/")
        #         if not is_logged_in_GPT(): login_GPT()
        #         open_resume_chat()
        #         global chatGPT_tab
        #         chatGPT_tab = driver.current_window_handle
        #     except Exception as e:
        #         print_lg("Opening OpenAI chatGPT tab failed!")
        if use_AI:
            if ai_provider == "openai":
                aiClient = ai_create_openai_client()
            ##> ------ Yang Li : MARKYangL - Feature ------
            # Create DeepSeek client
            elif ai_provider == "deepseek":
                aiClient = deepseek_create_client()
            elif ai_provider == "gemini":
                aiClient = gemini_create_client()
            ##<

            try:
                about_company_for_ai = " ".join([word for word in (first_name+" "+last_name).split() if len(word) > 3])
                print_lg(f"Extracted about company info for AI: '{about_company_for_ai}'")
            except Exception as e:
                print_lg("Failed to extract about company info!", e)
        
        # Start applying to jobs
        driver.switch_to.window(linkedIn_tab)
        total_runs = run(total_runs)
        while(run_non_stop):
            if cycle_date_posted:
                date_options = ["Any time", "Past month", "Past week", "Past 24 hours"]
                global date_posted
                date_posted = date_options[date_options.index(date_posted)+1 if date_options.index(date_posted)+1 > len(date_options) else -1] if stop_date_cycle_at_24hr else date_options[0 if date_options.index(date_posted)+1 >= len(date_options) else date_options.index(date_posted)+1]
            if alternate_sortby:
                global sort_by
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
                total_runs = run(total_runs)
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
            total_runs = run(total_runs)
            if dailyEasyApplyLimitReached:
                break
        

    except (NoSuchWindowException, WebDriverException) as e:
        print_lg("Browser window closed or session is invalid. Exiting.", e)
    except Exception as e:
        critical_error_log("In Applier Main", e)
        pyautogui.alert(e,alert_title)
    finally:
        print_lg("\n\nTotal runs:                     {}".format(total_runs))
        print_lg("Jobs Easy Applied:              {}".format(easy_applied_count))
        print_lg("External job links collected:   {}".format(external_jobs_count))
        print_lg("                              ----------")
        print_lg("Total applied or collected:     {}".format(easy_applied_count + external_jobs_count))
        print_lg("\nFailed jobs:                    {}".format(failed_count))
        print_lg("Irrelevant jobs skipped:        {}\n".format(skip_count))
        if randomly_answered_questions: print_lg("\n\nQuestions randomly answered:\n  {}  \n\n".format(";\n".join(str(question) for question in randomly_answered_questions)))
        quote = choice([
            "You're one step closer than before.", 
            "All the best with your future interviews.", 
            "Keep up with the progress. You got this.", 
            "If you're tired, learn to take rest but never give up.",
            "Success is not final, failure is not fatal: It is the courage to continue that counts. - Winston Churchill",
            "Believe in yourself and all that you are. Know that there is something inside you that is greater than any obstacle. - Christian D. Larson",
            "Every job is a self-portrait of the person who does it. Autograph your work with excellence.",
            "The only way to do great work is to love what you do. If you haven't found it yet, keep looking. Don't settle. - Steve Jobs",
            "Opportunities don't happen, you create them. - Chris Grosser",
            "The road to success and the road to failure are almost exactly the same. The difference is perseverance.",
            "Obstacles are those frightful things you see when you take your eyes off your goal. - Henry Ford",
            "The only limit to our realization of tomorrow will be our doubts of today. - Franklin D. Roosevelt"
            ])
        msg = f"\n{quote}\n\n\nBest regards,\nSeraj Khan\nhttps://www.linkedin.com/in/its-seraj/\n\n"
        pyautogui.alert(msg, "Exiting..")
        print_lg(msg,"Closing the browser...")
        if tabs_count >= 10:
            msg = "NOTE: IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM!\n\nOr it's highly likely that application will just open browser and not do anything next time!" 
            pyautogui.alert(msg,"Info")
            print_lg("\n"+msg)
        ##> ------ Yang Li : MARKYangL - Feature ------
        if use_AI and aiClient:
            try:
                if ai_provider.lower() == "openai":
                    ai_close_openai_client(aiClient)
                elif ai_provider.lower() == "deepseek":
                    ai_close_openai_client(aiClient)
                elif ai_provider.lower() == "gemini":
                    pass # Gemini client does not need to be closed
                print_lg(f"Closed {ai_provider} AI client.")
            except Exception as e:
                print_lg("Failed to close AI client:", e)
        ##<
        try:
            if driver:
                driver.quit()
        except WebDriverException as e:
            print_lg("Browser already closed.", e)
        except Exception as e: 
            critical_error_log("When quitting...", e)


if __name__ == "__main__":
    main()
