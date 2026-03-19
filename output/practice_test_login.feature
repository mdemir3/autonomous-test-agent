Feature: Practice Test Login
  As a user
  I want to log in on the practice test login page
  So that I can access protected content

  Background:
    Given the user is on the practice test login page

  @positive @smoke
  Scenario: Successful Login
    When I enter "student" as the username and "Password123" as the password
    Then the user is successfully logged in

  @negative
  Scenario Outline: Invalid username
    When I enter "<username>" as the username and "Password123" as the password
    Then an error message indicating that the username or password is incorrect is displayed

    Examples:
      | username          |
      | invalid_username  |
      | empty_username    |
      | student test      |
      | student!@#        |

  @edge_case
  Scenario Outline: Invalid password
    When I enter "student" as the username and "<password>" as the password
    Then an error message indicating that the username or password is incorrect is displayed

    Examples:
      | password          |
      | invalid_password  |
      | empty_password    |