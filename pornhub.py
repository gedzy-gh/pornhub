import argparse
import getpass
import os
from pickle import load, dump, UnpicklingError
from random import choice
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import WebDriverException, \
    TimeoutException, NoSuchElementException, MoveTargetOutOfBoundsException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


# Our Pornhub Class!
class Pornhub:
    # Our File Handler
    class __File:

        def __init__(self, file_name):
            self.__path = os.path.dirname(os.path.abspath(__file__)) + '/' + file_name
            self.contents = []

        # Our file path
        def path(self):
            return self.__path

        # Is the file empty?
        def empty(self):
            if os.stat(self.__path).st_size == 0:
                return True
            else:
                return False

        # Does the file exist?
        def exist(self):
            return os.path.isfile(self.__path)

        # If the file doesn't exist try a create a file and write to it
        def touch(self):
            if not self.exist():
                with open(self.__path, 'w') as file:
                    if self.contents:
                        file.write('{data}\n'.format(data=self.contents))

        # Write data at the end of a file
        def append(self):
            with open(self.__path, 'a') as file:
                if self.contents:
                    for item in self.contents:
                        file.write('{data}\n'.format(data=item))

        # Has the same user been seen before?
        def seen(self):

            # Items that have already been seen
            has_seen = []

            # Will check if two items match, if it does add it to the seen list
            with open(self.__path, 'r') as file:
                lines = file.read().splitlines()
                for item in self.contents:
                    for line in lines:
                        if item == line:
                            has_seen.append(line)

            # Remove repeats from list
            has_seen = list(set(has_seen))

            # From our list remove items that have been seen
            try:
                for item in has_seen:
                    self.contents.remove(item)
            except IndexError:
                pass

            # Append items to file that previously weren't seen
            self.append()

            return self.contents

        # Selects a random line in a file using choice
        def random_line(self):
            with open(self.__path, 'r') as file:
                lines = choice(file.read().splitlines())
                if len(lines) != 0:
                    return lines
                else:
                    return ''

        # If something went wrong, try and delete the file
        def __exit__(self):
            if self.exist() and self.empty():
                try:
                    os.remove(self.__path)
                except OSError:
                    pass

    # Our class for using selenium to automate actions
    class __Selenium:

        def __init__(self, wait=4, pause=2):
            self.browser = webdriver.Firefox(service_log_path=os.devnull)
            self.wait = WebDriverWait(self.browser, wait)
            self.pause = pause

    # Any path that we want, could be a file path or a css selector path from our selected website
    class __Path:

        def __init__(self):
            self.url_root = 'https://www.pornhubpremium.com/'
            self.url_premium = self.url_root + 'premium/login'
            self.url_users = self.url_root + 'users/'

            self.url_search = self.url_root + 'user/search?ageControl=1&username=&avatar=1&' \
                                              'online=1&verified=1&city=&videos=1&photos=1&gender=0&orientation=0&' \
                                              'relation=0&country=&o=newest&age1=18&age2=50&page='

            self.file_cookie = 'cookie.pkl'
            self.file_users = 'users.txt'
            self.file_words = 'words.txt'

            self.id_username = 'username'
            self.id_password = 'password'
            self.id_login = 'submitLogin'

            self.text_invalid = 'Invalid username/password!'
            self.text_blocked = 'Your account has been blocked for one hour. Please try again later or'

            self.class_username = 'usernameLink'

            self.stream_none = '.blockedUserText'
            self.stream_post = '.post > div:nth-child(1)'
            self.stream_only = 'div.modal-close'
            self.stream_private = '.privateStream > div:nth-child(2) > div:nth-child(1)'

            self.text_stream_only = 'is able to post on this stream.'

            self.css_error = '#errors'
            self.ccs_cookie = '#acceptCookie'
            self.css_post_url = '.block'
            self.css_post_icon = '.post > div:nth-child(1)'
            self.css_post_message = '.sceditor-container > iframe:nth-child(2)'
            self.css_post_button = '#postToStream'

    def __init__(self):
        self.file = Pornhub.__File
        self.selenium = Pornhub.__Selenium(3, 1)
        self.path = Pornhub.__Path()

        # Get url and load page
        url = self.path.url_premium
        self.selenium.browser.get(url)

    # Use cookie file for authentication if exist
    def has_cookie(self):

        file = self.file(self.path.file_cookie)

        try:
            with open(file.path(), 'rb') as file:
                for cookie in load(file):
                    self.selenium.browser.add_cookie(cookie)
            return True
        except FileNotFoundError:
            return False

    # Using the pickle import, save the cookie file from selenium
    def make_cookie(self):

        file = self.file(self.path.file_cookie)

        # Using pickle to dump cookies to a file
        try:
            dump(self.selenium.browser.get_cookies(), open(file.path(), 'wb'))
        except UnpicklingError:
            pass

    # Automate logging in to pornhub.com (2FA must be off!)
    def login(self, username, password):

        # Input username into field
        path = self.path.id_username
        field = self.selenium.browser.find_element_by_id(path)
        field.send_keys(username)
        sleep(self.selenium.pause)

        # Input password into field
        path = self.path.id_password
        field = self.selenium.browser.find_element_by_id(path)
        field.send_keys(password)
        sleep(self.selenium.pause)

        # Wait until the login button is clickable to perform login
        path = self.path.id_login
        button = self.selenium.wait.until(ec.element_to_be_clickable((By.ID, path)))
        button.click()
        sleep(self.selenium.pause)

        # Check if a class selector path exists
        def exists(css_path):
            try:
                element = self.selenium.browser.find_element_by_css_selector(css_path).text
            except NoSuchElementException:
                return None
            return element

        # Input password into field
        path = self.path.css_error
        reason = exists(path)
        if reason:
            print(str(reason))
            self.browser_close()
            exit(1)

        # Wait until the URL has changed
        try:
            path = self.selenium.browser.current_url
            self.selenium.wait.until(ec.url_changes(path))
        except TimeoutException:
            sleep(self.selenium.pause)

        # Accept any cookies
        path = self.path.ccs_cookie
        self.selenium.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, path))).click()
        sleep(self.selenium.pause)

    # Get any recent online users and write them to a file
    def recent_online_users(self, page):

        # Pornhub advanced search page, can be changed to suit different search criteria
        try:
            path = self.path.url_search + str(page)
            self.selenium.browser.get(path)
        except WebDriverException:
            pass

        # Find href's under class name 'usernameLink'
        path = self.path.class_username
        elements = self.selenium.browser.find_elements_by_class_name(path)
        sleep(self.selenium.pause)

        # Append them to a list called 'attributes'
        tag = 'href'
        attributes = [item.get_attribute(tag) for item in elements]

        # Create a file
        path = self.path.file_users
        file = self.file(path)

        # Filter the list to sort out valid users
        links = list(filter(lambda x: x is not None, attributes))
        file.users = list(filter(lambda x: len(str(x)) > 2, links))
        file.users = list(set(file.users))
        file.users = list(filter(lambda x: 'users' in str(x), file.users))
        file.users = sorted(list(map(lambda x: x.rsplit('/', 1)[1], file.users)))

        # Make file if not exist
        file.touch()

        # Next data to be written to file
        file.contents = file.users
        file.users = file.seen()

        return file.users

    # Automate posting comments to users streams
    def post_comment(self, username):

        # Visit and load url
        try:
            path = self.path.url_users + username
            self.selenium.browser.get(path)
        except WebDriverException:
            pass

        # Create a file for words list
        path = self.path.file_words
        file = self.file(path)

        # Our default comment
        comment = 'Amazing page {x}!'.format(x=username)

        # If the file exist
        if file.exist():

            # Using choice, randomly select a line from out file
            line = file.random_line()

            # If the line isn't empty
            if line:

                # Our default comment will change to a new comment
                comment = line

                # If {x} in string add their username to our default comment
                if '{x}' in line:
                    comment = comment.format(x=username)

        else:
            # If it doesn't exist, create a file and add one comment
            file.contents = 'Amazing page {x}!'
            file.touch()

        # Check if a css selector path exists
        def exists(css_selector_path):
            try:
                self.selenium.browser.find_element_by_css_selector(css_selector_path)
            except NoSuchElementException:
                return False
            return True

        # Check if a css selector path exists and returns text contents
        def text(css_selector_path, word):
            try:
                element = self.selenium.browser.find_element_by_css_selector(css_selector_path).text
                if word in element:
                    return True
                else:
                    return False
            except NoSuchElementException:
                return False

        # Checks are needed to be done in order to post a comment to the users stream
        stream_none = exists(self.path.stream_none)
        stream_only = text(self.path.stream_only, self.path.text_stream_only)
        stream_private = exists(self.path.stream_private)
        stream_post = exists(self.path.stream_post)

        if stream_none:
            print('%s has no stream!' % username)
        elif stream_only:
            print('%s can only post to their stream!' % username)
        elif stream_private:
            print('%s has a private stream!' % username)
        elif not stream_post:
            print('%s has no post option on their stream!' % username)
        elif stream_post:
            print('%s has a public stream!' % username)

            # Using Selenium and ActionChains to automate posting a comment to the users stream
            try:

                path = self.path.css_post_url
                if exists(path):
                    url = self.selenium.browser.find_element_by_css_selector(path)
                    actions = ActionChains(self.selenium.browser).move_to_element(url)
                    sleep(self.selenium.pause)
                    actions.click()
                    actions.perform()

                path = self.path.css_post_icon
                if exists(path):
                    icon = self.selenium.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, path)))
                    sleep(self.selenium.pause)
                    icon.click()

                path = self.path.css_post_message
                if exists(path):
                    message = self.selenium.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, path)))
                    actions = ActionChains(self.selenium.browser).click(message)
                    actions.send_keys(comment)
                    actions.perform()
                    sleep(self.selenium.pause)

                path = self.path.css_post_button
                if exists(path):
                    self.selenium.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, path))).click()
                    sleep(self.selenium.pause)

            except MoveTargetOutOfBoundsException as e:
                print('')
                print(e)
                exit(1)

    # Future development?
    def add_as_friend(self, username):
        pass

    # Exit the browser and script
    def browser_close(self):
        self.selenium.browser.quit()
        exit(0)


def main():

    # Used to hide user/password input in console
    def login():
        u, p = getpass.getpass(prompt='Username: ', stream=None), getpass.getpass(prompt='Password: ', stream=None)
        return u, p

    # Our created class to be used to automate actions
    pornhub = Pornhub()

    print('')

    # If we haven't logged on before we need to login
    if not pornhub.has_cookie():

        # Using import arg parser to to parse commands in console
        parser = argparse.ArgumentParser(description='Login to pornhub.com and automate actions!')
        parser.add_argument('-login', action='store_true', help='Enter your credentials to login')
        parser.set_defaults(func=login())

        args = parser.parse_args()

        # Check if we have any empty args
        for i in args.func:
            if not i:
                print('Args cannot be empty!')
                exit(1)

        # Try and login to pornhub and save our cookie!
        pornhub.login(args.func[0], args.func[1])
        pornhub.make_cookie()

    # Used to control script
    failed_count, page_count, break_count = 0, 1, 10

    # Adjust how long script runs for by loop
    while 1:

        print('')

        # Get unseen users that are online
        users = pornhub.recent_online_users(page_count)

        # Count items in list
        count = len(users)

        # Print to console
        if count > 0:

            if count == 1:
                print('Found %i user on page %i' % (count, page_count))
            else:
                print('Found %i users on page %i' % (count, page_count))
        else:
            print('Found %i users on page %i' % (count, page_count))
            page_count += 1

            # If failed wait some time for more users to come online
            if page_count > 10:
                page_count = 0
                failed_count += 1
                sleep(60 * failed_count)

        # Give up, if we can't get anywhere
        if failed_count == break_count:
            break

        print('')

        # Post random comment to users page
        for user in users:
            pornhub.post_comment(user)

    # Exit the browser
    pornhub.browser_close()


if __name__ == '__main__':
    main()
