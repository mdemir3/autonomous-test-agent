import os
import sys

from behave import given, when, then
from playwright.sync_api import sync_playwright, expect

_out = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _out not in sys.path:
    sys.path.insert(0, _out)
from practice_test_login_locators import LoginPageLocators as L


def before_scenario(context, scenario):
    context._playwright = sync_playwright().start()
    context.browser = context._playwright.chromium.launch(headless=True)
    context.page = context.browser.new_page()


def after_scenario(context, scenario):
    context.browser.close()
    context._playwright.stop()

@given('the user is on the practice test login page')
def step_open_page(context):
    context.page.goto('https://practicetestautomation.com/practice-test-login/')

@when('I enter "{username}" as the username and "{password}" as the password')
def step_enter_credentials(context, username, password):
    context.page.fill(L.USERNAME_FIELD, username)
    context.page.fill(L.PASSWORD_FIELD, password)

@then('the user is successfully logged in')
def step_login_success(context):
    expect(context.page).to_contain_text("Logged In Successfully")

@then('an error message indicating that the username or password is incorrect is displayed')
def step_invalid_credentials(context):
    expect(context.page).to_contain_text("Invalid username or password")