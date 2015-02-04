class BaseNetworkCost(object):

    def __init__(self, rn):
        self.rn = rn
        self.total_ton_km = self.rn.ton_km

    def _market_to_shadow_prices(self, market_cost):
        """Convert market cost to shadow cost."""

        rpc = self.rn.params[self.MARKET_TO_SHADOW].value
        shadow_cost = market_cost * rpc

        return shadow_cost

    def _capital_recovery_factor(self, int_rate, use_life):
        """Calculate capital recovery factor."""

        a = int_rate * pow(1 + int_rate, use_life)
        b = pow(1 + int_rate, use_life) - 1

        return a / b


# ***   RAILWAY cost subclasses   *** #
class RailwayMobilityCost(BaseNetworkCost):

    MARKET_TO_SHADOW = "mobility_cost_rpc"

    def _cost_eac_ton_km(self, eac, units):
        """Calculate eac by ton_km for a number of units."""

        # calculate year cost
        year_eac = eac * units

        # calculate cost per ton_km
        if self.total_ton_km > 0.1:
            eac_ton_km = year_eac / self.total_ton_km

        else:
            eac_ton_km = 0.0

        return eac_ton_km

    def _cost_eac_wagon(self):
        """Calculate eac by ton_km of wagons."""

        # assign parameters to short variables
        wagon_price = self.rn.params["wagon_price"].value
        int_rate = self.rn.params["interest_rate"].value
        use_life = self.rn.params["useful_life_wagon"].value
        num_wagons = self.rn.wagons.get_units_needed_by_time()

        # calculate capital recovery factor and equivalent annual cost
        crf = self._capital_recovery_factor(int_rate, use_life)
        wagon_eac = wagon_price * crf

        # convert market cost to shadow cost
        market_cost = self._cost_eac_ton_km(wagon_eac, num_wagons)
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost

    def _cost_eac_locom(self):
        """Calculate eac by ton_km of locomotives."""

        # assign parameters to short variables
        locom_price = self.rn.params["locomotive_price"].value
        int_rate = self.rn.params["interest_rate"].value
        use_life = self.rn.params["useful_life_locom"].value
        num_locoms = self.rn.locoms.get_units_needed_by_time()

        # calculate capital recovery factor and equivalent annual cost
        crf = self._capital_recovery_factor(int_rate, use_life)
        locom_eac = locom_price * crf

        # convert market cost to shadow cost
        market_cost = self._cost_eac_ton_km(locom_eac, num_locoms)
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost

    def _cost_fuel_and_lub(self):
        """Calculate cost of fuel and lubricant by ton_km."""

        # assign parameters to short variables
        fuel_by_km = self.rn.params["fuel_cost_by_km"].value
        loc_running = self.rn.locoms.get_running_time()
        speed = self.rn.params["speed"].value
        lub_fuel_ratio = self.rn.params["lubricants_fuel_ratio"].value

        # calculate fuel_ton_km cost
        if self.total_ton_km > 0.1:
            fuel_ton_km = fuel_by_km * loc_running * speed / self.total_ton_km

        else:
            fuel_ton_km = 0.0

        # calculate lubricant ton km cost
        lub_ton_km = fuel_ton_km * lub_fuel_ratio

        # convert market cost to shadow cost
        market_cost = fuel_ton_km + lub_ton_km
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost

    def _cost_mobility_maintenance(self):
        """Calcualate cost of locomotives and wagons maintenance by ton_km."""

        if self.total_ton_km > 0.1:

            # calculate locmotives maintenance by ton_km
            locom_maintenance = self.rn.params["maintenance_by_locomotive"].value * \
                self.rn.locoms.get_units_needed_by_time() / self.total_ton_km

            # calculate wagon maintenance by ton_km
            wagon_maintenance = self.rn.params["maintenance_by_wagon"].value * \
                self.rn.wagons.get_units_needed_by_time() / self.total_ton_km

        else:
            locom_maintenance = 0.0
            wagon_maintenance = 0.0

        # convert market cost to shadow cost
        market_cost = locom_maintenance + wagon_maintenance
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost

    def _cost_manpower(self):
        """Calculate cost of manpower on board of train."""

        # assign parameters to short variables
        manpower_cost_by_hour = self.rn.params["manpower_cost_by_hour"].value
        manpower_by_loc = self.rn.params["manpower_by_loc"].value

        cost_by_hour = manpower_cost_by_hour * manpower_by_loc

        # calculate locomotive hours with manpower on the train
        operation_hours = self.rn.locoms.get_operation_time()

        if self.total_ton_km > 0.1:
            manpower_cost = cost_by_hour * operation_hours / self.total_ton_km

        else:
            manpower_cost = 0.0

        # convert market cost to shadow cost
        market_cost = manpower_cost
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost


class RailwayInfrastructureCost(BaseNetworkCost):

    MARKET_TO_SHADOW = "infrast_cost_rpc"

    def _cost_turnout(self, gross_tk, dist):
        """Calculate equivalent annual cost of turnouts."""

        # calculate number of turnouts needed
        num_turnouts = self._calc_number_of_turnouts(gross_tk, dist)

        # calculate wages cost to maintain turnouts
        wages_by_turnout = self.rn.params["yearly_wages_by_turnout"].value
        total_wages_cost = num_turnouts * wages_by_turnout

        # calculate eac of turnout tracks
        density = gross_tk / dist
        total_eac_cost = num_turnouts * self._cost_eac_track(density, 1.0,
                                                            True)

        # convert market cost to shadow cost
        market_cost = total_wages_cost + total_eac_cost
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost

    def _calc_number_of_turnouts(self, gross_tk, dist):
        """Calculate number of turnouts needed in a certain track."""

        # store parameters in short-name variables
        max_turnout_distance = self.rn.params["turnout_freq"].value
        max_turnout_density = self.rn.params["turnout_freq_max_density"].value
        t_distance = max_turnout_distance

        # calculate density
        density = gross_tk / dist

        if not density < max_turnout_density:
            t_distance = max_turnout_distance / (density / max_turnout_density)

        num_turnouts = dist / t_distance

        return num_turnouts

    def _cost_eac_track(self, gross_tk, dist, main_track):
        """Calculate equivalent annual cost of track.

        If its a main track, calculate EAC cost of track. If its a secondary
        track, there is no eac cost of track."""

        # check if is a main track
        if main_track:
            eac = self._cost_eac_main_track(gross_tk, dist)

        else:
            eac = self._cost_eac_secondary_track(gross_tk, dist)

        # convert market cost to shadow cost
        market_cost = eac
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost

    def _cost_infrast_maint(self, gross_tk, dist):
        """Calculate cost of maintaining infrastructure."""

        # track maintenance cost calculation
        a_track = self.rn.params["coef_a_track_maint_cost"].value
        b_track = self.rn.params["coef_b_track_maint_cost"].value
        track_maint = ((gross_tk / dist) ** a_track) * b_track * gross_tk

        # no track maintenance cost calculation
        a_notrack = self.rn.params["coef_a_notrack_maint_cost"].value
        b_notrack = self.rn.params["coef_b_notrack_maint_cost"].value
        no_track_maint = ((gross_tk / dist) ** a_notrack) * \
            b_notrack * gross_tk

        # convert market cost to shadow cost
        market_cost = track_maint + no_track_maint
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost

    def _cost_eac_main_track(self, gross_tk, dist):

        # store parameters in short-name variables
        a_eac = self.rn.params["coef_a_track_cost"].value
        b_eac = self.rn.params["coef_b_track_cost"].value
        use_life = self.rn.params["useful_life_track"].value
        max_gross_tk = self.rn.params[
            "gross_tk_in_hq_track_lifetime"].value
        int_rate = self.rn.params["interest_rate"].value
        max_cost_track = self.rn.params["high_quality_track_price"].value

        # calculate gross tk in max possible useful life years
        gross_tk_in_use_life = use_life * gross_tk / dist

        # use estimated function if gross_tk expected is less than maximum
        if gross_tk_in_use_life < max_gross_tk:
            cost_track = a_eac + b_eac * gross_tk_in_use_life

        # otherwise, use high quality track price and recalculate use_life
        else:
            cost_track = max_cost_track
            use_life = max_gross_tk / (gross_tk / dist)

        # calculate eac by year
        crf = self._capital_recovery_factor(int_rate, use_life)
        eac = cost_track * crf * dist

        return eac

    def _cost_eac_secondary_track(self, gross_tk, dist):

        # store parameters in short-name variables
        min_cost_track = self.rn.params["low_quality_track_price"].value
        use_life = self.rn.params["useful_life_track"].value
        int_rate = self.rn.params["interest_rate"].value
        gross_main_min_dens = self.rn.params["gross_main_min_density"].value

        # calculate eac by year
        crf = self._capital_recovery_factor(int_rate, use_life)
        eac = min_cost_track * crf * dist

        # adjust eac cost for densities below minimum
        gross_density = gross_tk / dist
        adj_coeff = gross_density / gross_main_min_dens

        eac = eac * adj_coeff

        return eac


class RailwayTimeCost(BaseNetworkCost):

    MARKET_TO_SHADOW = "time_cost_rpc"

    def _cost_deposit(self):
        """Calculate cost of freight deposit while waiting a train service."""

        # get parameters into short name variables
        cost_day_ton = self.rn.params["deposit_cost_per_day_ton"].value

        # calculate deposit cost for each od pair
        total_deposit_cost = 0.0
        for od in self.rn.iter_od_pairs():

            if (od.tons.get() > 0 and od.tons.category != 1 and
                    od.get_lowest_link_scale()):

                # calculate days of deposit
                lowest_link_scale = od.get_lowest_link_scale() / 2
                days_of_deposit = self._calc_deposit_days(lowest_link_scale)

                # calculate od deposit cost
                od.cost.deposit = (cost_day_ton * days_of_deposit *
                                   od.tons.get())

                total_deposit_cost += od.cost.deposit

        if self.total_ton_km > 0.1:

            # total deposit cost is returned in ton-km
            deposit_cost = total_deposit_cost / self.total_ton_km

        else:
            deposit_cost = 0.0

        # convert market cost to shadow cost
        market_cost = deposit_cost
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost

    def _cost_immobilized_value(self):
        """Calculate immobilizing value cost during deposit and travel time."""

        cost_ton_day = self.rn.params["cost_of_immobilized_ton"].value

        # calculate immobilized time for each od pair
        total_immo_ton_days = 0.0
        for od in self.rn.iter_od_pairs():

            if (od.tons.get() > 0 and od.tons.category != 1 and
                    od.get_lowest_link_scale()):

                # calculate days of deposit
                lowest_link_scale = od.get_lowest_link_scale() / 2
                days_of_deposit = self._calc_deposit_days(lowest_link_scale)

                # calculate days of travel
                days_of_travel = self._calc_travel_days(od)

                # total immobilized days and ton-days for od pair
                immobilized_days = days_of_deposit + days_of_travel
                immobilized_ton_days = immobilized_days * od.tons.get()

                total_immo_ton_days += immobilized_ton_days
                od.cost.immo_value = immobilized_ton_days * cost_ton_day

        total_cost_immo_value = total_immo_ton_days * cost_ton_day

        if self.total_ton_km > 0.1:

            # total cost of immobilized value is returned in ton-km
            immobilized_value_cost = total_cost_immo_value / self.total_ton_km

        else:
            immobilized_value_cost = 0.0

        # convert market cost to shadow cost
        market_cost = immobilized_value_cost
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost

    def _cost_short_freight(self):
        """Calculate cost of transport from door to train station."""

        short_freight_cost_ton = self.rn.params["short_freight_to_train"].value

        # calculate short freight cost for each od pair
        total_short_freight_cost = 0.0
        for od in self.rn.iter_od_pairs():
            if od.tons.category != 1:
                short_freight_cost = short_freight_cost_ton * od.tons.get() * 2
                total_short_freight_cost += short_freight_cost
                od.cost.short_freight = short_freight_cost

        if self.total_ton_km > 0.1:

            # total cost of short freight is returned in ton-km
            short_freight_cost_tk = total_short_freight_cost / self.total_ton_km

        else:
            short_freight_cost_tk = 0.0

        # convert market cost to shadow cost
        market_cost = short_freight_cost_tk
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost

    def _calc_deposit_days(self, lowest_link_scale):
        """Calculate deposit days to hold a load while waiting a train."""

        # get parameters into short name variables
        locomotive_load = (self.rn.params["locomotive_capacity"].value /
                           self.rn.params["loading_ratio"].value)
        min_weekly_train_freq = self.rn.params["min_weekly_freq"].value

        # calculate how many trains per week will be at that scale
        weekly_train_freq = (lowest_link_scale / locomotive_load) / (365 / 7)
        weekly_train_freq = max(weekly_train_freq, min_weekly_train_freq)

        # calculate average days of deposit waiting the train
        average_days_waiting = 1 / weekly_train_freq * 7 / 2

        # calculate deposit days at origin and destination
        total_deposit_days = average_days_waiting * 2

        return total_deposit_days

    def _calc_travel_days(self, od):
        """Calculate travel time of an od pair."""

        # get parameters into short name variables
        truck_to_train_time = self.rn.params["ratio_truck_to_train_travel_time"].value
        speed = self.rn.params["speed"].value
        turnout_time = self.rn.params["turnout_time"].value
        regroup_time = self.rn.params["regroup_time"].value

        # calculate days of train running
        running_days = od.dist / speed / 24

        # calculate days of train stopped in turnouts
        num_turnouts = self.rn.get_turnouts(od.links, od.gauge)
        idle_turnout_days = num_turnouts * turnout_time / 24

        # calculate days of train stopped at regrouping tasks
        if self.rn.od_can_be_regrouped(od):
            num_regroups = self.rn.get_regroups(od.links, od.gauge)
            idle_regroup_days = num_regroups * regroup_time / 24
        else:
            num_regroups = 0

        total_days = running_days + idle_turnout_days + idle_regroup_days

        return total_days * truck_to_train_time


class RailwayNetworkCost(BaseNetworkCost):

    def cost_mobility(self):
        """Calculate each type of mobility cost."""
        RV = {}

        # init object to cost mobility
        rmc = RailwayMobilityCost(self.rn)

        # fill RV with moblity costs per ton-km
        RV["eac_wagon"] = rmc._cost_eac_wagon()
        RV["eac_locom"] = rmc._cost_eac_locom()
        RV["fuel_and_lub"] = rmc._cost_fuel_and_lub()
        RV["maintenance"] = rmc._cost_mobility_maintenance()
        RV["manpower"] = rmc._cost_manpower()

        # sum all costs and add it to total mobility
        RV["total_mobility"] = sum(RV.values())

        return RV

    def cost_infrast(self):
        """Calculate each type of infrastructure cost."""

        # initialize return value
        RV = {}
        RV["eac_turnout"] = 0.0
        RV["eac_track"] = 0.0
        RV["maintenance"] = 0.0

        # init object to cost infrastructure
        ric = RailwayInfrastructureCost(self.rn)

        # calculate gross ton_km and infrastructure cost for each link
        for link in self.rn.iter_links():

            # check if there is load on that link
            if link.tons.get() > 0.0:

                # calculate gross ton-km carried by the link
                gross_tk = link.gross_ton_km

                # ask to the railway network if this is a main track
                main_track = self.rn.is_main_track(gross_tk, link.dist)

                # store the result to the link
                link.main_track = main_track

                # calculate costs of link infrastructure
                eac_turnout = ric._cost_turnout(gross_tk, link.dist)
                eac_track = ric._cost_eac_track(gross_tk, link.dist,
                                                main_track)
                maintenance = ric._cost_infrast_maint(gross_tk,
                                                      link.dist)

                # update RV cost category with traffic of the link
                RV["eac_turnout"] += eac_turnout
                RV["eac_track"] += eac_track
                RV["maintenance"] += maintenance

                # write costs to link object
                link.eac_turnout = eac_turnout
                link.eac_track = eac_track
                link.maintenance = maintenance

            # set all costs in the link to zero
            else:
                link.eac_turnout = 0.0
                link.eac_track = 0.0
                link.maintenance = 0.0

        # divide all costs to express them in terms of ton-km
        for infrast_cost in RV:
            if ric.total_ton_km > 0.1:
                RV[infrast_cost] = RV[infrast_cost] / self.total_ton_km
            else:
                RV[infrast_cost] = 0.0

        # sum all costs and add it to total mobility
        RV["total_infrastructure"] = sum(RV.values())

        return RV

    def cost_time(self):
        """Calculate each type of time related cost."""
        RV = {}

        # init object to cost time
        rtc = RailwayTimeCost(self.rn)

        # fill RV with moblity costs per ton-km
        RV["deposit"] = rtc._cost_deposit()
        RV["immobilized_value"] = rtc._cost_immobilized_value()
        RV["short_freight"] = rtc._cost_short_freight()

        # sum all costs and add it to total mobility
        RV["total_time"] = sum(RV.values())

        return RV


# ***   ROADWAY cost subclasses   *** #
class RoadwayMobilityCost(BaseNetworkCost):

    MARKET_TO_SHADOW = "mobility_cost_rpc"

    def _cost_mobility(self):
        """Calculate cost of truck mobility."""

        mobility_cost_tk = self.rn.params["mobility_cost_tk"].value
        mobility_cost = self.rn.ton_km * mobility_cost_tk

        # convert market cost to shadow cost
        market_cost = mobility_cost / self.total_ton_km
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost


class RoadwayInfrastructureCost(BaseNetworkCost):

    MARKET_TO_SHADOW = "infrast_cost_rpc"

    def _cost_eac_track(self, ton, dist):
        """Calculate equivalent annual cost of track."""

        a_eac = self.rn.params["coef_a_infrast_cost"].value
        b_eac = self.rn.params["coef_b_infrast_cost"].value

        eac = b_eac * (ton ** a_eac)

        # convert market cost to shadow cost
        market_cost = eac * dist
        shadow_cost = self._market_to_shadow_prices(market_cost)

        return shadow_cost


class RoadwayNetworkCost(BaseNetworkCost):

    def cost_mobility(self):
        """Calculate each type of mobility cost."""
        RV = {}

        # init object to cost mobility
        rmc = RoadwayMobilityCost(self.rn)

        # sum all costs and add it to total mobility
        RV["total_mobility"] = rmc._cost_mobility()

        return RV

    def cost_infrast(self):
        """Calculate each type of infrastructure cost."""
        RV = {}
        RV["eac_track"] = 0

        # init object to cost mobility
        ric = RoadwayInfrastructureCost(self.rn)

        # calculate gross ton_km and infrastructure cost for each link
        for link in self.rn.iter_links():

            # check if there is load on that link
            if link.tons.get() > 0:

                # calculate costs of link infrastructure
                eac_track = ric._cost_eac_track(link.tons.get(),
                                                link.dist)

                # update RV cost category with traffic of the link
                RV["eac_track"] += eac_track

                # write costs to link object
                link.eac_track = eac_track

        # divide all costs to express them in terms of ton-km
        for infrast_cost in RV:
            RV[infrast_cost] = RV[infrast_cost] / ric.total_ton_km

        # sum all costs and add it to total mobility
        RV["total_infrastructure"] = sum(RV.values())

        return RV
