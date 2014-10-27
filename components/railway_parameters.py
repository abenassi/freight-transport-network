class Parameter():

    NF = "{:,.1f}"

    def __init__(self, id_param, value, desc=None):
        self.id = id_param
        self.desc = desc
        self.value = None

        # if value is passed, convert to float
        if value:
            self.value = float(value)

    def __repr__(self):

        if self.value:
            value = self.NF.format(self.value)
        else:
            value = str(None)

        return "Parameter: " + str(self.id).ljust(28) + \
               "Value: " + value.ljust(11) + \
               "Description: " + str(self.desc)