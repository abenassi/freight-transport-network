class Parameter():

    NF = "{:,.1f}"

    def __init__(self, id_param, value, desc=None):
        self.id = id_param
        self.value = value
        self.desc = desc

        # if value is passed, convert to float
        if value:
            self.value = float(value)

    def __repr__(self):

        return "Parameter: " + str(self.id).ljust(28) + \
               "Value: " + str(self.value).ljust(11) + \
               "Description: " + str(self.desc)
