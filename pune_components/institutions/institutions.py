__author__ = 'hassaankhan'

from pynsim import Institution

class PuneInstitution(Institution):
    description = "Common Methods for Pune Institutions"

    def __init__(self, name, **kwargs):
        super(PuneInstitution, self).__init__(name, **kwargs)

#########

class AllNodesOfType(PuneInstitution):
    description = "Institution containing all nodes of a component type in the network"

    def __init__(self, name, component_type, network, **kwargs):
        super(AllNodesOfType, self).__init__(name, **kwargs)
        for n in network.nodes:
            if n.component_type == component_type:
                self.add_nodes(n)
        self.timestep = 0

    def setup(self, timestamp):
        self.timestep = self.timestep + 1


##########################
class PMC(PuneInstitution):
    description = "Water Supply for Pune"

    def setup(self, timestep):
        pass


class PCMC(PuneInstitution):
    description = "Water Supply Pimpri-Chinchwad"

    def setup(self, timestep):
        pass

class MIDC(PuneInstitution):
    description = "Water Supply for MIDC"

    def setup(self, timestep):
        pass


class WUA(PuneInstitution):
    """We are currently not sure how and if WUAs operate. If they are functional, this instituion will feature the decision
    rules regarding allocation between farmers and making demands of the Water Resources Department
    """
    description = "Water User Association"

    def setup(self, timestep):
        pass

class ZP(PuneInstitution):
    description = "Water supply for rural households"

    def setup(self, timestep):
        pass

class MKVDC(PuneInstitution):
    """This institution operates reservoirs in the UBB. We currently do not have decision rules for the reservoirs, so in
    this model template, the target releases for each reservoir are set synthetically. If more data is received, then
    this institution would contain the reservoir operation decisions. This will likely have to be optimization based.
    """
    name = "Authority in charge of operating reservoirs"

    def setup(self, timestamp):
        pass



class WRD(PuneInstitution):
    """This institution sets the allocations for each of the three important sectors: domestic, agriculture, industrial.
    In future versions, this would be the instituion where allocation targets are determined and communicated to the MKVDC
    """
    name = "Government department in charge of allocating water across sectors"

    def setup(self, timestamp):
        pass