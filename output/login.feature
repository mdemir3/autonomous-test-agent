Feature: Login Feature
  As a user
  I want to log in with valid credentials
  So that I can access the application

Background:
  Given the user is on the login page

@positive
Scenario: Successful login with valid credentials
  Given the user enters valid username "student"
  And the user enters valid password "Password123"
  When the user clicks the login button
  Then the user should be redirected to the dashboard
  And the welcome message should be displayed

@negative
Scenario Outline: Login fails with invalid credentials
  Given the user enters username "<username>"
  And the user enters password "<password>"
  When the user clicks the login button
  Then an error message "<error>" should be displayed

Examples:
  | username      | password      | error                    |
  | invalid_user  | secret_sauce  | Username is incorrect    |
  | standard_user | wrong_pass    | Password is incorrect    |
  |               |               | Username is required     |

@edge_case
Scenario: Unsuccessful login with empty username
  Given the user leaves the "Username Field" blank
  And the user enters valid password "Password123"
  When the user clicks the login button
  Then an error message should be displayed indicating invalid username

@edge_case
Scenario: Unsuccessful login with empty password
  Given the user enters valid username "student"
  And the user leaves the "Password Field" blank
  When the user clicks the login button
  Then an error message should be displayed indicating invalid password

@negative
Scenario: Unsuccessful login with invalid username
  Given the user enters invalid username "invalid_user"
  And the user enters valid password "Password123"
  When the user clicks the login button
  Then an error message should be displayed indicating invalid username

@negative
Scenario: Unsuccessful login with invalid password
  Given the user enters valid username "student"
  And the user enters invalid password "wrong_pass"
  When the user clicks the login button
  Then an error message should be displayed indicating invalid password

@edge_case
Scenario: Successful login with special characters in username
  Given the user enters username "special_chars_user" with special characters
  And the user enters valid password "Password123"
  When the user clicks the login button
  Then the user should be redirected to the dashboard

@edge_case
Scenario: Successful login with special characters in password
  Given the user enters valid username "student"
  And the user enters password "special_chars_password" with special characters
  When the user clicks the login button
  Then the user should be redirected to the dashboard

@edge_case
Scenario: Successful login with long username
  Given the user enters long username "long_username_string"
  And the user enters valid password "Password123"
  When the user clicks the login button
  Then the user should be redirected to the dashboard

@edge_case
Scenario: Successful login with long password
  Given the user enters valid username "student"
  And the user enters long password "long_password_string"
  When the user clicks the login button
  Then the user should be redirected to the dashboard