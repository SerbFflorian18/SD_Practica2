import pickle


class StorageService:
    def __init__(self):
        # Data base object
        self.database = dict()
        try:
            # Try restoring data from the file
            self.restore()
        except FileNotFoundError:
            pass

    # Save key and value in the database
    def save(self, key, value):
        try:
            self.database[key] = value
            # Save the data to the file
            self.dump()
            success = True
        except:
            success = False
        
        return success

    # Get the value of the key
    def fetch(self, key):

        try:
            data = self.database[key]
            found = True
        except:
            data = None
            found = False

        return found, data

    # Save The data in a file
    def dump(self):
        with open("storage.pickle", "wb") as f:
            pickle.dump(self.database, f)

    # Read data from the file
    def restore(self):
        with open("storage.pickle", "rb") as f:
            loaded = pickle.load(f)
            self.database = loaded



