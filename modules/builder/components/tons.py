class Tons(object):

    """Keeps information about tons.

    Tons object knows the category, original transport mode and current od
    pairs of all tons in its domain. It can add and remove tons keeping track
    of its caracteristics. It returns information about the amount of tons
    holded and its caracteristics.

    All data is stored in a dictionary of dictionaries where tons can be
    accessed using keys in this order: [mode][category][id_od]

    The dictionary has the follwing structure:

    self.tons = {"original": {"1": {"1-3": 100, "1-4": 150},
                              "2": {"3-5": 70}
                              },
                 "derived":  {"3": {"2-3": 10, "3-4": 300},
                              "5": {"5-7": 20}
                              }
                 }
    """

    def __init__(self):
        self.tons = {"original": {}, "derived": {}}

    # PUBLIC
    # add and remove methods
    def add_original_ton(self, ton, categories, id_ods):
        """Add original tons to the link."""
        self._add_ton(ton, categories, id_ods, "original")

    def add_derived_ton(self, ton, categories, id_ods):
        """Add derived tons to the link."""
        self._add_ton(ton, categories, id_ods, "derived")

    def remove_original_ton(self, ton, categories, id_ods):
        """Remove original tons from the link."""
        self._remove_ton(ton, categories, id_ods, "original")

    def remove_derived_ton(self, ton, categories, id_ods):
        """Remove derived tons from the link."""
        self._remove_ton(ton, categories, id_ods, "derived")

    def remove_ton(self, ton, categories, id_ods):
        """Remove tons from the link."""

        # remove tons from link
        if ton < self.get_derived_ton(categories, id_ods):
            self._remove_ton(ton, categories, id_ods, "derived")

        elif self.get_derived_ton(categories, id_ods) == 0.0:
            self._remove_ton(ton, categories, id_ods, "original")

        else:
            removing_orig_ton = ton - self.get_derived_ton(categories, id_ods)
            self._remove_all_ton(categories, id_ods, "derived")
            self._remove_ton(removing_orig_ton, categories, id_ods, "original")

    # get methods
    def get_ton(self, categories=None, id_ods=None, modes=None):
        """Return tons of the link, filtering by category, id_od and mode."""

        # convert no list parameters into lists
        if categories and (not type(categories) == list):
            categories = [categories]
        if id_ods and (not type(id_ods) == list):
            id_ods = [id_ods]
        if modes and (not type(modes) == list):
            modes = [modes]

        # initialize result in zero
        filtered_tons = 0.0

        # iter modes
        for iter_modes in self.tons.items():

            mode_id = iter_modes[0]
            mode_value = iter_modes[1]

            # iter categories of the mode, if corresponds
            if (not modes) or (mode_id in modes):

                # iter categories
                for iter_categories in mode_value.items():

                    categ_id = iter_categories[0]
                    categ_value = iter_categories[1]

                    # iter values of the category, if corresponds
                    if (not categories) or (categ_id in categories):

                        # iter values (which keys are id_ods)
                        for iter_values in categ_value.items():

                            value_id_od = iter_values[0]
                            value_tons = iter_values[1]

                            # add value, if id_od corresponds
                            if (not id_ods) or (value_id_od in id_ods):
                                filtered_tons += value_tons

        return filtered_tons

    def get_original_ton(self, categories=None, id_ods=None):
        """Returns tons of the original transport mode."""
        return self.get_ton(categories, id_ods, modes="original")

    def get_derived_ton(self, categories=None, id_ods=None):
        """Returns tons derived from another transport mode."""
        return self.get_ton(categories, id_ods, modes="derived")

    # other methods
    def clean_insignificant_ton_values(self, significance):
        """Checks stored values are significant."""

        for value in self._iter_values():
            if value < significance:
                value = 0.0

    # PRIVATE
    def _iter_values(self):

        for mode in self.tons.values():
            for category in mode.values():
                for value in category.values():
                    yield value

    def _add_ton(self, ton, category, id_od, mode):
        """Add ton to a mode-category-id_od value."""

        # ensure necessary dictionaries exist
        self._safe_dict_keys(category, id_od, mode)

        # add tons
        self.tons[mode][category][id_od] += ton

    def _remove_ton(self, ton, category, id_od, mode):
        """Remove ton of a mode-category-id_od value."""

        # ensure necessary dictionaries exist
        self._safe_dict_keys(category, id_od, mode)

        # get existing tons from wich to remove some or all
        existing_tons = self.tons[mode][category][id_od]

        # check for rounding issues if tons to remove are all of them
        if abs(ton - existing_tons) > 0.01:

            # assert that can remove that amount of tons
            msg = "Cannot remove more tons than existent ones." + \
                  "Tons to remove: " + str(ton) + \
                  " Existing tons: " + str(existing_tons)
            assert ton < existing_tons, msg

            # remove tons
            self.tons[mode][category][id_od] -= ton

        # when tons to remove are almost all (rounding), remove them all
        else:
            self._remove_all_ton(category, id_od, mode)

    def _remove_all_ton(self, category, id_od, mode):
        """Remove all tons of a mode-category-id_od value."""

        # ensure necessary dictionaries exist
        self._safe_dict_keys(category, id_od, mode)

        # delete item
        del(self.tons[mode][category][id_od])

    def _safe_dict_keys(self, category, id_od, mode):
        """Create necessary dicts to ensure all keys can be called."""

        if mode not in self.tons:
            self.tons[mode] = {}

        if category not in self.tons[mode]:
            self.tons[mode][category] = {}

        if id_od not in self.tons[mode][category]:
            self.tons[mode][category][id_od] = 0.0
