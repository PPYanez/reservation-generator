from datetime import datetime
import faker
import functools
import json
import random

ancillaries = [
    {'precio': 10000, 'ssr': "BGH"},
    {'precio': 30000, 'ssr': "BGR"},
    {'precio': 5000, 'ssr': "STDF"},
    {'precio': 2000, 'ssr': "PAXS"},
    {'precio': 40000, 'ssr': "PTCR"},
    {'precio': 40000, 'ssr': "AVIH"},
    {'precio': 35000, 'ssr': "SPML"},
    {'precio': 15000, 'ssr': "LNGE"},
    {'precio': 20000, 'ssr': "WIFI"}
]

def findAncillaryBySsr(ssr):
    for ancillary in ancillaries:
        if ancillary['ssr'] == ssr:
            return ancillary

    return None

def calculateFlightPrice(flight):
    departureString = f"{flight['fecha']} {flight['hora_salida']}:00"
    departureObject = datetime.strptime(departureString, '%d/%m/%y %H:%M:%S')

    returnString = f"{flight['fecha']} {flight['hora_llegada']}:00"
    returnObject = datetime.strptime(returnString, '%d/%m/%y %H:%M:%S')

    timeDifference = returnObject - departureObject
    minutesDifference = (timeDifference).total_seconds()/60

    return int(minutesDifference)*590

def findFlightBack(routeDict, departureFlight):
    # Find a route that goes from the destination of the departure flight to the origin of the departure flight
    # return a flight if it's date is later than the departure flight's
    routeBack = f'{departureFlight["destino"]}, {departureFlight["origen"]}'
    if routeBack in routeDict:
        for flight in routeDict[routeBack]:
            departureDateStamp = datetime.strptime(departureFlight['fecha'], '%d/%m/%y')
            returnDateStamp = datetime.strptime(flight['fecha'], '%d/%m/%y')

            if returnDateStamp > departureDateStamp:
                return flight

def generateReservations():
    # Obtain all flights from vuelos.json
    flightList = []
    with open('vuelos.json') as infile:
        data = json.load(infile)
        for flight in data:
            flightList.append(flight)

    # Group flights by route, a route is a pair of origen, destino
    routeDict = {}
    for flight in flightList:
        route = f'{flight["origen"]}, {flight["destino"]}'

        if route not in routeDict:
            routeDict[route] = [flight]
        else:
            routeDict[route].append(flight)

    # Generate len(routeDict) reservations, one for every possible route
    reservationList = []

    for route in routeDict.keys():
        # Sort flights by fecha
        routeDict[route].sort(key=lambda x: x['fecha'])

        # If there is more than 1 flight in the route, choose the earliest flight to have more probabilities
        # of having a flight back
        departureFlight = routeDict[route][0]
        if 'avion' in departureFlight:
            del departureFlight['avion']
            del departureFlight['ancillaries']

        # Find a flight that goes from the destination of the departure flight to the origin of the departure flight
        vuelos = {}
        vuelos['vuelos'] = []
        vuelos['vuelos'].append(departureFlight)

        if findFlightBack(routeDict, departureFlight) != None:
            returnFlight = findFlightBack(routeDict, departureFlight)
            
            if 'avion' in returnFlight:
                del returnFlight['avion']
                del returnFlight['ancillaries']

            vuelos['vuelos'].append(returnFlight)

        # Generate a random number of passengers between 1 and 3 using random library
        numPassengers = random.randint(1, 3)

        # For every passenger, generate first name, last name, age, ancillaries and balance
        passengers = []
        fake = faker.Faker()

        for i in range(numPassengers):
            ancillariesIdaQty = random.randint(1, 4)
            ancillariesIda = random.sample(ancillaries, ancillariesIdaQty)
            for j in range(len(ancillariesIda)):
                ancillariesIda[j] = {
                    'ssr': ancillariesIda[j]['ssr'],
                    'cantidad': random.randint(1, 3)
                }

            ida = {
                'ida': ancillariesIda
            }

            vuelta = {}
            if len(vuelos['vuelos']) > 1:
                ancillariesVueltaQty = random.randint(1, 4)
                ancillariesVuelta = random.sample(ancillaries, ancillariesVueltaQty)

                for j in range(len(ancillariesVuelta)):
                    ancillariesVuelta[j] = {
                        'ssr': ancillariesVuelta[j]['ssr'],
                        'cantidad': random.randint(1, 3)
                    }
                vuelta = {
                    'vuelta': ancillariesVuelta
                }

            if vuelta == {}:
                balances = {
                    "ancillaries_ida": sum(
                        a['cantidad'] * findAncillaryBySsr(a['ssr'])['precio'] for a in ancillariesIda
                    ),
                    "vuelo_ida": calculateFlightPrice(vuelos['vuelos'][0])
                }

                passengers.append({
                    'nombre': fake.first_name(),
                    'apellido': fake.last_name(),
                    'edad': random.randint(18, 60),
                    'ancillaries': [ida],
                    'balances': balances
                })
            else:
                balances = {
                    "ancillaries_ida": sum(
                        a['cantidad'] * findAncillaryBySsr(a['ssr'])['precio'] for a in ancillariesIda
                    ),
                    "vuelo_ida": calculateFlightPrice(vuelos['vuelos'][0]),
                    "ancillaries_vuelta": sum(
                        a['cantidad'] * findAncillaryBySsr(a['ssr'])['precio'] for a in ancillariesVuelta
                    ),
                    "vuelo_vuelta": calculateFlightPrice(vuelos['vuelos'][1]),
                }

                passengers.append({
                    'nombre': fake.first_name(),
                    'apellido': fake.last_name(),
                    'edad': random.randint(18, 60),
                    'ancillaries': [ida, vuelta],
                    'balances': balances
                })

        reservation = {
            'vuelos': vuelos['vuelos'],
            'pasajeros': passengers
        }

        reservationList.append(reservation)

    return reservationList

reservationList = generateReservations()

with open("reservas.json", "w") as outfile:
    outfile.write("[\n")

    for idx, reservation in enumerate(reservationList):
        outfile.write(json.dumps(reservation, indent=4))

        if idx < len(reservationList) - 1:
            outfile.write(",\n")
    
    outfile.write("\n]")