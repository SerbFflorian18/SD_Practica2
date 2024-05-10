
class StorageService:
    def __init__(self):
        self.database = dict()

    # Save key and value in the database
    def save(self, key, value):
        try:
            self.database[key] = value
            success = True
        except:
            success=False
        
        return success

    # Get the value of the key
    def fetch(self, key):

        try:
            data = self.database[key]
            found=True
        except:
            data=None
            found=False

        return found, data

