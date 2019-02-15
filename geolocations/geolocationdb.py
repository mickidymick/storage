import time
import shelve
import threading

from streetaddress import StreetAddress

import geopy.geocoders
import geopy.exc

class GeolocationDB:
    def __init__(self, filename):
        self.db = shelve.open(filename, "c")

        self.api = geopy.geocoders.Nominatim(
            user_agent = "curent-utk",
            country_bias = "USA"
        )

        self.dt = float('-inf')
        self.mut = threading.Lock()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.db.close()

    def __getitem__(self, key):
        if type(key) is StreetAddress:
            dbquery = {}

            if key.house_number is not None and key.street is not None:
                dbquery["street"] = key.house_number + " " + key.street

            if key.city is not None:
                dbquery["city"] = key.city

            if key.state is not None:
                dbquery["state"] = key.state

            if key.zip_code is not None:
                dbquery["postalcode"] = key.zip_code

            assert len(dbquery) > 0

            dbkey = str(key)
        elif type(key) is str:
            dbquery = key
            dbkey = key
        else:
            raise TypeError

        if dbkey not in self.db:
            with self.mut:
                # Nominatim allows _at most_ one thread making one request per second
                # <https://operations.osmfoundation.org/policies/nominatim/>
                dt = time.perf_counter()

                if dt - self.dt < 1.1:
                    time.sleep(1.1 - dt + self.dt)

                self.dt = dt

                try:
                    request = self.api.geocode(query, geometry = "geojson")
                except geopy.exc.GeopyError:
                    return None

                if request is None:
                    return None

                self.db[dbkey] = request.raw

        return self.db[dbkey]