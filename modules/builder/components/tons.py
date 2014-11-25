"""Management for adding, removing and getting tons in Links and ODs."""


class BaseTons(object):

    def __init__(self):
        self.tons = {"original": None, "derived": None}


class OdTons(BaseTons):

    """Keeps information about tons in an OD pair.

    OdTons object knows the original transport mode of the tons in an OD pair.
    It can add and remove tons keeping track of its original transport mode.

    Data is stored in a dictionary that has the follwing structure:

    self.tons = {"original": 150000,
                 "derived":  20000}
    """

    # PUBLIC
    # getters
    def get_original_ton(self):
        """Get tons that are originally transported by the transport mode."""
        return self.tons["original"]

    def get_derived_ton(self):
        """Get tons that are derived from other freight transport mode."""
        return self.tons["derived"]

    def get_ton(self, mode=None):
        """Get tons of od pair.

        Args:
            mode: Mode of tons to be returned (original, derived or none for
                total tons)."""

        if mode:
            ton = self.tons[mode]

        else:
            ton = self.get_original_ton() + self.get_derived_ton()

        return ton

    # add and derive methods
    def add_original_ton(self, ton):
        """Add original tons to OD pair."""
        self._add_ton(ton, "original")

    def derive_ton(self, other, coeff=1.0):
        """Derive tons to another freight transport mode.

        It derives tons to an OD pair object coming from another transport mode
        but with the same id. Only original tons of the od pair are subject to
        derivation coefficient (coeff), while previously derivated tons are
        just returned completely

        Args:
            other: OD object from another transport mode that will receive
                derived tons from self OD object.
            coeff (opt): Coefficient of tons that will be derived. The default
                is to derive all tons (1.0)

        Raise:
            DerivationError: Trying to derive tons to an other od pair with
                different id will raise an error. Derivation must occur with an
                od pair with the same origin and destination (ie, same id)
        """

        # check od pairs have same id and category
        msg = "OD pairs are different: {} != {}".format(self.get_id(),
                                                        other.get_id())
        assert (self.get_id() == other.get_id() and
                self.get_category() == other.get_category()), msg

        # calculate original tons from both od pairs
        self_original_ton = self.get_original_ton() + other.get_derived_ton()

        # calculate tons should be derived
        ton_should_be_derived = self_original_ton * coeff
        ton_already_derived = other.get_derived_ton()
        ton_to_derive = ton_should_be_derived - ton_already_derived

        # get tons to be returned (derived from "other" previously)
        ton_to_return = self.get_derived_ton()

        # remove tons from self od pair
        self._remove_original_ton(ton_to_derive)
        self._remove_derived_ton(ton_to_return)

        # add tons to other od pair
        other._add_derived_ton(ton_to_derive)
        other.add_original_ton(ton_to_return)

        return (ton_to_derive, ton_to_return)

    # PRIVATE
    # add methods
    def _add_ton(self, ton, mode):
        """Add tons to od pair.

        Args:
            ton: Tons to be added.
            mode: Mode (original or derived) to wich adding tons."""

        if not self.get_ton(mode):
            self.tons[mode] = ton

        else:
            self.tons[mode] += ton

    def _add_derived_ton(self, ton):
        """Add derived tons to OD pair."""
        self._add_ton(ton, "derived")

    # remove methods
    def _remove_ton(self, ton, mode):
        """Remove tons from OD pair.

        Args:
            ton: Tons to be removed.
            mode: Mode (original or derived) from where to remove tons."""

        msg = "Can't remove more " + mode + " tons than existent ones: " + \
            str(ton) + " > " + str(self.get_original_ton())
        assert ton <= self.get_ton(mode), msg

        self.tons[mode] -= ton

    def _remove_derived_ton(self, ton):
        """Remove derived tons from OD pair."""
        self._remove_ton(ton, "derived")

    def _remove_original_ton(self, ton):
        """Remove original tons from OD pair."""
        self._remove_ton(ton, "original")


class LinkTons(BaseTons):

    """Keeps information about tons in a Link.

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

    # PUBLIC
    # getters
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

    # add methods
    def add_original_ton(self, ton, categories, id_ods):
        """Add original tons to the link."""
        self._add_ton(ton, categories, id_ods, "original")

    def add_derived_ton(self, ton, categories, id_ods):
        """Add derived tons to the link."""
        self._add_ton(ton, categories, id_ods, "derived")

    # remove methods
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

    # other methods
    def clean_insignificant_ton_values(self, significance):
        """Checks stored values are significant."""

        for value in self._iter_values():
            if value < significance:
                value = 0.0

    # PRIVATE
    def _iter_values(self):
        """Iterate all values."""

        for mode in self.tons.values():
            for category in mode.values():
                for value in category.values():
                    yield value

    def _safe_dict_keys(self, category, id_od, mode):
        """Create necessary dicts to ensure all keys can be called."""

        if (mode not in self.tons) or (not self.tons[mode]):
            self.tons[mode] = {}

        if category not in self.tons[mode]:
            self.tons[mode][category] = {}

        if id_od not in self.tons[mode][category]:
            self.tons[mode][category][id_od] = 0.0

    # add and remove methods
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
