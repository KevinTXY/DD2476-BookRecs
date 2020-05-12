import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# given the path of a link to a book, returns that book id
def getId(inp: str) -> str:
    for i in range(len(inp) - 1):
        if not inp[i].isnumeric():
            return inp[:i]
    return inp

# Instantiates a webdriver browser. Requires appropriate driver exe file
#browser = webdriver.Chrome('chromedriver.exe')  # Uncomment this and include chromedriver in directory to use chrome instead
browser = webdriver.Edge('msedgedriver.exe')  
users = open("users.txt", "w")

# change this to adjust results
userid = 7250

#only records users with this many books at a minimum read
minbooks = 20

# change this to adjust how many users are recorded
usersleft = 37

user = 1
while usersleft > 0:

    # load page
    browser.get(f"https://www.goodreads.com/review/list/{userid}?per_page=infinite&shelf=read&sort=rating&utf8=%E2%9C%93")
    time.sleep(1)

    # Check if private page or incorrect redirect
    if 'list' not in browser.current_url:
        userid += 1
        continue

    # Close login popup if it comes up
    try:
        browser.find_element_by_xpath("/html/body/div[3]/div/div/div[1]/button").click()
    except:
        pass

    # Scroll to bottom to load in all books
    last_height = browser.execute_script("return document.body.scrollHeight")
    while True:

        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        # Calculate new scroll height and compare with last scroll height.
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    

    tbody = browser.find_element_by_xpath("/html/body/div[2]/div[3]/div[1]/div[1]/div[3]/div[2]/div[2]/table/tbody")
    rows = tbody.find_elements_by_xpath('./tr')

    # ignore users with not enough books read
    if len(rows) < minbooks:
        userid += 1
        continue

    # Start recording book id's of user's read books
    print(f"New User ({user}): {len(rows)} books found")
    for row in rows:
        ft = row.find_element_by_css_selector("td[class='field title']")
        book = ft.find_element_by_tag_name('a').get_attribute('href')[36:]
        bkid = (getId(book))
        users.write(bkid)
        users.write("\n")

    # prepare for next user
    users.write("\n")
    userid += 1
    usersleft -= 1
    user += 1


users.close()


    
