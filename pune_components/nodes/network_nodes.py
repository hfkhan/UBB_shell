__author__ = 'hassaankhan'

from pynsim import Node
from copy import copy


class PuneNode(Node):
    """The Pune node class.
    parent class that provides common methods for nodes in the Pune model.
    **Properties**:

        |  *institution_names* (list) - list of institutions associated with node

    """
    description = "Common Methods for Pune Nodes"

    def __init__(self, name, **kwargs):
        super(PuneNode, self).__init__(name, **kwargs)
        self.institution_names = []

    def add_to_institutions(self, institution_list, n):
        """Add node to institutions.

        **Arguments**:

        |  *institution_list* (list) - list of institutions associated with node
        |  *n* (pynsim network) - network

        """
        for institution in n.institutions:
            for inst_name in institution_list:
                if institution.name.lower() == inst_name.lower():
                    institution.add_node(self)

    def get_depth(self, count=1):
        """calculates how far away this node is from the most upstream node."""

        if len(self.upstream_nodes) > 0:
            level = max([n.get_depth(count=count) for n in self.upstream_nodes])
        else:
            level = 0

        return count + level

class Junction(PuneNode):
    """ The junction node is used only to rout water through the system, and if needed, add
    water into the system through the hydrologic model. It does not have any water consumption. Water
    is routed to downstream links in two ways: the default is to split the flow equally among all downstream links.
    Alternatively, for each downstream link, a specified volume of percentage of flow can be provided for the link.

    """

    def __init__(self, name, **kwargs):
        super(Junction, self).__init__(name, **kwargs)
        self.inflow = 0
        self.allocation_priority = None #This specifies the downstream links that need to be prioritised
        self.allocation_type = None #Specifies whether the assigned downstream demand is in volume or percentage
        self.allocation = None #Specifies for each of prioritised downstream links, what the required demands are.

    _properties = {'inflow': None}


    def allocate(self):
        """
            The default behaviour if there are no rules specified is to
            split the allocation equally. Any links not specified as priority
            links get the leftover water equally.
        """
        self.inflow = self.inflow + sum([l.flow for l in self.in_links])

        self.non_priority_links = copy(self.out_links)
        allocation_avail = copy(self.inflow)

        if self.allocation is not None:
            # Allocation priority can either be a tuple of links or a link.
            if type(self.allocation_priority) == tuple:
                for i, link in enumerate(self.allocation_priority):
                    allocation = self.allocation[i]
                    alloc_vol = self.set_outflow(link, allocation)
                    allocation_avail = allocation_avail - alloc_vol
            else:
                link = self.allocation_priority
                allocation = self.allocation
                alloc_vol = self.set_outflow(link, allocation)
                allocation_avail = allocation_avail - alloc_vol

        if allocation_avail < 0:
            raise Exception("Node %s cannot satisfy allocation." % (self.name))

        if len(self.non_priority_links) > 0:
            # Split the remaining water equally between remaining links
            link_alloc = 1/len(self.non_priority_links)
            for seq in self.non_priority_links:
                supply = allocation_avail * link_alloc
                if seq.end_node.node_type == 'farm':
                    seq.flow = min(seq.end_node.demand, supply)
                else:
                    seq.flow = supply

    def set_outflow(self, link, allocation):
        if link not in self.non_priority_links:
            raise Exception("Link %s in the allocation priority not "
                            "connected to node %s" % (link.name, self.name))

        if self.allocation_type == 'pct':
            alloc_volume = self.inflow * (allocation / 100.0)
        else:
            alloc_volume = allocation

        if link.end_node.component_type == 'farm':
            farm = link.end_node
            alloc_volume = min(farm.demand, alloc_volume)

        link.flow = alloc_volume

        self.non_priority_links.remove(link)

        return alloc_volume

class Pune_Reservoir(PuneNode):
    """
        Currently, the UBB network includes 55 reservoirs.
        The decision rules for the reservoirs are defined in the watmanag engine currently.
    """
    def __init__(self, name, **kwargs):
        super(Pune_Reservoir, self).__init__(name, **kwargs)
        self.surf_inflow = None
        self.all_inflow = 0
        self.allocation_priority = None #This specifies the downstream links that need to be prioritised
        self.allocation_type = None #Specifies whether the assigned downstream demand is in volume or percentage
        self.allocation = None #Specifies for each of prioritised downstream links, what the required demands are.
        self.max_stor = 0
        self.min_stor = 0
        self.init_stor = 0
        self.release_schedule = None
        self.actual_release = 0
        self.S = 0
    _properties = {'S': None,
                   'actual_release': None,
                   'all_inflow': None,
                   }



class FarmAgent(PuneNode):
    """This class will represent farmers in the UBB. In the initial conceptualization, farmer agents are defined based on
    their water supply, size of land holding, and location (talukas). In future versions, this should be changed
    The farmer node should have access to rainfall, surface water, and groundwater. Return flow back into the system
    should also be incorporated in this agent. Ju Young and Taher at IIASA will develop this agent.
    """

    def __init__(self, name, **kwargs):
        super(FarmAgent, self).__init__(name, **kwargs)
        self.name = name
        self.demand = 1000  # hypothetical demand
        self.area = 0
        self.crop = None
        self.y = 0
        self.gw_pumping = None
        self.gw_head = None
        self.pump_energy = None
        self.canal_avail = None
        self.prec_avail = None
    _properties = {'gw_pumping': None,
                   'gw_head': None,
                   'pump_energy': None,
                   'canal_avail' : None,
                   'prec_avail': None
                   }

class WWTP(PuneNode):
    """A WWTP node is representative of a wastewater treatment plant.

    **Properties**:

        |  *influent* (int) - monthly influent into wastewater treatment plant [m3]
        |  *effluent* (int) - monthly effluent from wastewater treatment plant [m3]
    """
    pass

class WTP(PuneNode):
    """A WTP node is representative of a water treatment plant. It represents water flows to a municipal water org."""
    pass
class UrbanHH(PuneNode):
    """Urban households receiving water from municipal organizations (e.g. PMC, PCMC, SMC)."""
    pass

class UrbanCO(PuneNode):
    """Urban commercial users receiving water from municipal organizations (e.g. PMC, PCMC, SMC)."""
    pass

class UrbanIND(PuneNode):
    """Industries within the cities receiving water from municipal organizations (e.g. PMC, PCMC, SMC)."""
    pass

class RuralHH(PuneNode):
    """This class will represent the rural households that obtain water from ZP's or through pumping their own
    groundwater. This node should have groundwater access. UFZ will develop this agent.
    """
    pass

