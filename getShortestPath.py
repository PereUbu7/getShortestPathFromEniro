from contextlib import closing
from selenium.webdriver import Firefox # pip install selenium
from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.common.by import By
import re
import time
from aco import ACO, Graph

EPSILON = 1e-2
ETERNITY = 1e6

eniro = "https://kartor.eniro.se/?&mode=route"

adresses = []

file = open("adresses.txt", "r")

print("Checking up:")

for line in file.readlines():
    adresses.append(line.rstrip())
    print(line.rstrip())

duration = []
prog = re.compile("\s[a-z]{3}", flags=re.IGNORECASE)

sleeptime = 2

# use firefox to get page with javascript generated content
with closing(Firefox()) as browser:
    browser.get(eniro)

    # Get distances between all adresses with eniro
    for n in range(len(adresses)):
        duration.append([])
        for m in range(len(adresses)):

            if n == m:
                duration[-1].append( EPSILON )
                continue

            WebDriverWait(browser, timeout=10).until(
                lambda x: x.find_element_by_name("from"))
            form_from = browser.find_element_by_name("from")
            form_from.clear()
            form_from.send_keys(adresses[n] + "\n")

            WebDriverWait(browser, timeout=10).until(
                lambda x: x.find_element_by_name("to"))
            form_to = browser.find_element_by_name("to")
            form_to.clear()
            form_to.send_keys(adresses[m] + "\n")

            WebDriverWait(browser, timeout=10).until(
                lambda x: x.find_element_by_class_name("e-do-route"))
            button = browser.find_element_by_class_name("e-do-route")

            button.click()

            time.sleep(sleeptime)

            # wait for the page to load
            WebDriverWait(browser, timeout=10).until(
                lambda x: x.find_element_by_class_name("e-text-bold"))
            element = browser.find_element_by_class_name("e-text-bold")

            durationString = element.text

            result = re.split(prog, durationString)

            if len(result) == 2:
                duration[-1].append( int(result[0]) + EPSILON )
            elif len(result) == 3:
                duration[-1].append( int(result[0])*60 + int(result[1]) + EPSILON )
            else:
                duration[-1].append( ETERNITY )

            print("Duration:", int(duration[-1][-1]), "minutes from", adresses[n], "to", adresses[m])


    # Find shortest path with AntColonyOptimizer
    aco = ACO(ant_count=10, generations=100, alpha=1.0, beta=10.0, rho=0.5, q=10, strategy=2, loop=True)
    graph = Graph(duration, len(adresses))
    path, cost = aco.solve(graph)

    print('\nTotal duration: {}, path: {}'.format(int(cost), path))

    print("\nPath:")
    for n in path:
        print(adresses[n])

    # Display shortest path in eniro
    WebDriverWait(browser, timeout=10).until(
        lambda x: x.find_element_by_name("from"))
    form_from = browser.find_element_by_name("from")
    form_from.clear()
    form_from.send_keys(adresses[0] + "\n")

    WebDriverWait(browser, timeout=10).until(
        lambda x: x.find_element_by_name("to"))
    form_to = browser.find_element_by_name("to")
    form_to.clear()
    form_to.send_keys(adresses[0] + "\n")

    for n in range(len(adresses) - 1):
        WebDriverWait(browser, timeout=10).until(
            lambda x: x.find_element_by_class_name("e-add-via"))
        buttonAdd = browser.find_element_by_class_name("e-add-via")

        buttonAdd.click()

    WebDriverWait(browser, timeout=10).until(
        lambda x: x.find_element_by_name("to"))
    forms_via = browser.find_elements_by_name("via")

    n = 1
    for via in forms_via:
        via.clear()
        via.send_keys(adresses[n] + "\n")
        n+=1

    WebDriverWait(browser, timeout=10).until(
        lambda x: x.find_element_by_class_name("e-do-route"))
    button = browser.find_element_by_class_name("e-do-route")

    button.click()

    # Wait untill browser is closed
    try:
        while True:
            browser.find_element_by_class_name("e-do-route")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nUser closed browser - Quitting script")