from behave import given, when, then
from playwright.sync_api import sync_playwright

import sys
sys.path.append('../')
from output.locators import LoginPageLocators as L

def before_scenario(context, scenario):
    playwright = sync_playwright().start()
    context.browser = playwright.chromium.launch(headless=False)
    context.page = context.browser.new_page()

def after_scenario(context, scenario):
    context.browser.close()

@given('the user is on the login page')
def step_open_login_page(context):
    context.page.goto("https://yourapp.com/login")

@given('the user enters valid username "{username}"')
def step_enter_username(context, username):
    context.page.fill(L.USERNAME_FIELD, username)

@when('the user clicks the login button')
def step_click_login_button(context):
    context.page.click(L.LOGIN_BUTTON)

@then('the user should be redirected to the dashboard')
def step_redirect_to_dashboard(context):
    context.page.expect_url("https://yourapp.com/dashboard")

@then('an error message "{error}" should be displayed')
def step_error_message_displayed(context, error):
    assert context.page.locator(".error-message").text_content() == error

@given('the user leaves the "Username Field" blank')
def step_leave_username_blank(context):
    context.page.fill(L.USERNAME_FIELD, "")

@when('the user enters valid password "{password}"')
def step_enter_valid_password(context, password):
    context.page.fill(L.PASSWORD_FIELD, password)

@then('an error message should be displayed indicating invalid username')
def step_error_message_invalid_username(context):
    assert context.page.locator(".error-message").text_content() == "Username is required"

@given('the user enters valid username "{username}"')
def step_enter_valid_username(context, username):
    context.page.fill(L.USERNAME_FIELD, username)

@when('the user leaves the "Password Field" blank')
def step_leave_password_blank(context):
    context.page.fill(L.PASSWORD_FIELD, "")

@then('an error message should be displayed indicating invalid password')
def step_error_message_invalid_password(context):
    assert context.page.locator(".error-message").text_content() == "Password is required"

@given('the user enters username "{username}" with special characters')
def step_enter_username_with_special_characters(context, username):
    context.page.fill(L.USERNAME_FIELD, username)

@when('the user enters password "{password}" with special characters')
def step_enter_password_with_special_characters(context, password):
    context.page.fill(L.PASSWORD_FIELD, password)

@then('the user should be redirected to the dashboard')
def step_redirect_to_dashboard_with_special_characters(context):
    context.page.expect_url("https://yourapp.com/dashboard")

@given('the user enters long username "{username}"')
def step_enter_long_username(context, username):
    context.page.fill(L.USERNAME_FIELD, username)

@when('the user enters password "{password}"')
def step_enter_password(context, password):
    context.page.fill(L.PASSWORD_FIELD, password)

@then('the user should be redirected to the dashboard')
def step_redirect_to_dashboard_with_long_username(context):
    context.page.expect_url("https://yourapp.com/dashboard")

@given('the user enters valid username "{username}"')
def step_enter_valid_username_again(context, username):
    context.page.fill(L.USERNAME_FIELD, username)

@when('the user enters long password "{password}"')
def step_enter_long_password(context, password):
    context.page.fill(L.PASSWORD_FIELD, password)

@then('the user should be redirected to the dashboard')
def step_redirect_to_dashboard_with_long_password(context):
    context.page.expect_url("https://yourapp.com/dashboard")