from contextlib import closing
from selenium.webdriver import Firefox
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchWindowException
from selenium.common.exceptions import InvalidSessionIdException

import re
import time
import pickle
from aco import ACO, Graph

def unpickle_iter(file):
    try:
        while True:
             yield pickle.load(file)
    except EOFError:
        raise StopIteration

EPSILON = 1e-2
ETERNITY = 1e6
NUMBER_OF_OPTIMIZING_TRIES = 100

eniro = "https://kartor.eniro.se/?&mode=route"

adresses = []

file = open("adresses.txt", mode="r", encoding="utf-8")

print("\nChecking up:")

# Get adresses from file
for line in file.readlines():
    adresses.append(line.rstrip())
    print(line.rstrip())
    
# Get cached distances from file cache
print("\nLoading cache")
distCache = {}
try:
	distCache = pickle.load( open("distDict.cache", "rb"))
except:
	print("No cache file distDict.cache found")

print(distCache)

duration = []
prog = re.compile("\s[a-z]{3}", flags=re.IGNORECASE)

sleeptime = 2

print("\nOpening web browser")
# use firefox to get page with javascript generated content
try:
    with closing(Firefox()) as browser:
        browser.get(eniro)

        # Get distances between all adresses with eniro
        for n in range(len(adresses)):
            duration.append([])
            for m in range(len(adresses)):

                if n == m:
                    duration[-1].append( EPSILON )
                    continue
                # Check if adress combination already in cache
                elif adresses[n] in distCache:
                    if adresses[m] in distCache[adresses[n]]:
                        duration[-1].append( distCache[ adresses[n] ][ adresses[m] ] )
                        continue
                    else:
                        pass
                else:
                    pass

                WebDriverWait(browser, timeout=20).until(
                    lambda x: x.find_element_by_name("from"))
                form_from = browser.find_element_by_name("from")
                form_from.clear()
                form_from.send_keys(adresses[n] + "\n")

                WebDriverWait(browser, timeout=20).until(
                    lambda x: x.find_element_by_name("to"))
                form_to = browser.find_element_by_name("to")
                form_to.clear()
                form_to.send_keys(adresses[m] + "\n")

                # Press TAB
                form_to.send_keys(u'\ue004')

                # WebDriverWait(browser, timeout=20).until(
                #     lambda x: x.find_element_by_class_name("e-do-route"))
                # button = browser.find_element_by_class_name("e-do-route")
                #
                # button.click()

                time.sleep(sleeptime)

                # wait for the page to load
                WebDriverWait(browser, timeout=20).until(
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

                print("Adding duration:", int(duration[-1][-1]), "minutes from", adresses[n], "to", adresses[m])

                if adresses[n] in distCache:
                    distCache[adresses[n]][adresses[m]] = duration[-1][-1]
                else:
                    distCache[adresses[n]] = {adresses[m] : duration[-1][-1]}

                pickle.dump(distCache, open("distDict.cache", "wb"))

        # Print cache
        for i in range(len(adresses)):
            for j in range(len(adresses)):
                print({ adresses[i] : { adresses[j] : duration[i][j] } })

        # Find optimal path
        minCost = None
        minPath = None

        for i in range(NUMBER_OF_OPTIMIZING_TRIES):
            print("Optimizing path", i+1, "of", NUMBER_OF_OPTIMIZING_TRIES)
            # Find shortest path with AntColonyOptimizer
            aco = ACO(ant_count=10, generations=100, alpha=1.0, beta=10.0, rho=0.5, q=10, strategy=2, loop=True)
            graph = Graph(duration, len(adresses))
            path, cost = aco.solve(graph)

            if(minCost is None or cost < minCost):
                minCost = cost
                minPath = path

                print('Total duration: {}, path: {}\n'.format(int(minCost), minPath))

        # Print path
        print("\nPath:")
        for n in minPath:
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
            via.send_keys(adresses[minPath[n]] + "\n")
            n+=1

        WebDriverWait(browser, timeout=10).until(
            lambda x: x.find_element_by_class_name("e-do-route"))
        button = browser.find_element_by_class_name("e-do-route")

        button.click()

        # Wait untill browser is closed
        try:
            print("\nClose browser to close script")
            while True:
                browser.find_element_by_class_name("e-do-route")
                time.sleep(1)
        except Exception as e:
            print("\nUser closed browser - Quitting script")
except NoSuchWindowException:
    pass
except InvalidSessionIdException:
    pass