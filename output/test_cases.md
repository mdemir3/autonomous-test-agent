TC_001: Valid Login Test Case
Title: Successful login with valid credentials
Preconditions: The user is not logged in, the username and password fields are empty
Test Steps:
1. Enter a valid username in the "Username Field"
2. Enter a valid password in the "Password Field"
3. Click the "Login Button"
Expected Result: The user is redirected to the dashboard page
Test Type: Positive

TC_002: Invalid Credentials Test Case
Title: Unsuccessful login with invalid credentials
Preconditions: The user is not logged in, the username and password fields are empty
Test Steps:
1. Enter an invalid username in the "Username Field"
2. Enter a valid password in the "Password Field"
3. Click the "Login Button"
Expected Result: An error message is displayed indicating invalid credentials
Test Type: Negative

TC_003: Empty Username Test Case
Title: Unsuccessful login with empty username
Preconditions: The user is not logged in, the username field is empty and password field has valid data
Test Steps:
1. Leave the "Username Field" blank
2. Enter a valid password in the "Password Field"
3. Click the "Login Button"
Expected Result: An error message is displayed indicating invalid username
Test Type: Edge Case

TC_004: Empty Password Test Case
Title: Unsuccessful login with empty password
Preconditions: The user is not logged in, the username field has valid data and password field is empty
Test Steps:
1. Enter a valid username in the "Username Field"
2. Leave the "Password Field" blank
3. Click the "Login Button"
Expected Result: An error message is displayed indicating invalid password
Test Type: Edge Case

TC_005: Invalid Username Test Case
Title: Unsuccessful login with invalid username
Preconditions: The user is not logged in, the username field has invalid data and password field has valid data
Test Steps:
1. Enter an invalid username in the "Username Field"
2. Enter a valid password in the "Password Field"
3. Click the "Login Button"
Expected Result: An error message is displayed indicating invalid username
Test Type: Negative

TC_006: Invalid Password Test Case
Title: Unsuccessful login with invalid password
Preconditions: The user is not logged in, the username field has valid data and password field has invalid data
Test Steps:
1. Enter a valid username in the "Username Field"
2. Enter an invalid password in the "Password Field"
3. Click the "Login Button"
Expected Result: An error message is displayed indicating invalid password
Test Type: Negative

TC_007: Special Characters in Username Test Case
Title: Successful login with special characters in username
Preconditions: The user is not logged in, the username field has special characters and password field has valid data
Test Steps:
1. Enter a username with special characters in the "Username Field"
2. Enter a valid password in the "Password Field"
3. Click the "Login Button"
Expected Result: The user is redirected to the dashboard page
Test Type: Edge Case

TC_008: Special Characters in Password Test Case
Title: Successful login with special characters in password
Preconditions: The user is not logged in, the username field has valid data and password field has special characters
Test Steps:
1. Enter a valid username in the "Username Field"
2. Enter a password with special characters in the "Password Field"
3. Click the "Login Button"
Expected Result: The user is redirected to the dashboard page
Test Type: Edge Case

TC_009: Long Username Test Case
Title: Successful login with long username
Preconditions: The user is not logged in, the username field has a long string and password field has valid data
Test Steps:
1. Enter a long username in the "Username Field"
2. Enter a valid password in the "Password Field"
3. Click the "Login Button"
Expected Result: The user is redirected to the dashboard page
Test Type: Edge Case

TC_010: Long Password Test Case
Title: Successful login with long password
Preconditions: The user is not logged in, the username field has valid data and password field has a long string
Test Steps:
1. Enter a valid username in the "Username Field"
2. Enter a long password in the "Password Field"
3. Click the "Login Button"
Expected Result: The user is redirected to the dashboard page
Test Type: Edge Case