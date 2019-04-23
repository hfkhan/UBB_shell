from __future__ import division
from pynsim import Engine

class SupplyRouting(Engine):
    """ This engine routs water through the UBB system. Currently routing is done for reservoirs and junction nodes (i.e.
    non-demand nodes. Return flows are not accounted for in this version (but should be in future versions, when we have
    a better idea of demand node (agri, urban) return flows. This routing engine may be replaced by an optimization based
    engine. The routing is done for each timestep (i.e. a month)'.

    The following steps take place in this version of the engine:
    i) Each node is ranked according to how many nodes are upstream of it. The most upstream nodes have rank of 1, and so on
    ii) Starting from the highest ranked (rank = 1) nodes, the water is routed ('pushed') through the system. The water
    release decision depends on the type of node, and its associated decision rule.
        If it's a reservoir, a mass balance is performed to obtain releases from the reservoir. The reservoirs make their
        water release decisions based on a defined release schedule. We currently do not have information for this, so
        I have made up some synthetic data on target releases. The reservoirs try to satisfy these targets while being
        constrained by minimum and maximum storage.
    For both junctions and reservoirs, the flow can be directed downstream in two ways. The default is to split the
    flow equally among all downstream links. Another way is to provide specific allocations (either in form of a percentage
    or absolute volume of flows for each of the downstream links).

    """

    name = "Supply based flow routing."

    def run(self):

        alldepths = []
        for n in self.target.nodes:
            alldepths.append(n.get_depth())
        deepest = max(alldepths)

        for rank in range(1,deepest+1):
            appnodes = []
            for n in self.target.nodes:
                if n.get_depth() == rank and n.node_type in ['jnc', 'res']:
                    appnodes.append(n)

            for node in appnodes:
                if node.node_type == 'jnc':
                    node.allocate()

                if node.node_type == 'res':
                    #node.res_mass_balance()
                    node.all_inflow = sum([l.flow for l in node.in_links]) + node.surf_inflow

                    #Set initial storage for this simulation time step
                    if len(node._history['S']) == 0:
                        init_stor = node.init_stor
                    else:
                        init_stor = node._history['S'][-1]

                    node.actual_release = node.release_schedule[self.target.network.current_timestep_idx]

                    node.S = init_stor + node.all_inflow - node.actual_release

                    maxFlag = (node.S - node.max_stor) > 0.1
                    minFlag = (node.min_stor - node.S) > 0.1

                    #while any(maxFlag) or any(minFlag): #FOR NOW WE ARE REMOVING THIS FLAG BECAUSE WE'RE NOT SURE IF THE SYNTHETIC VALUES MAKE SENSE
                    if maxFlag:
                        excess_stor = node.S - node.max_stor
                        node.actual_release += excess_stor

                    elif minFlag:
                        deficit_stor = node.S - node.min_stor
                        node.actual_release += deficit_stor

                    # Update storages
                    node.S = init_stor + node.all_inflow - node.actual_release

                        #############################################################################################

                    #node.res_allocate()
                    allocation_avail = node.actual_release

                    if node.allocation is not None:
                        if type(node.allocation_priority) == tuple:
                            for i, link in enumerate(node.allocation_priority):
                                allocation = node.allocation[i]
                                alloc_vol = node.set_outflow(link, allocation)
                                allocation_avail = allocation_avail - alloc_vol
                        else:
                            link = node.allocation_priority
                            allocation = node.allocation
                            alloc_vol = node.set_outflow(link, allocation)
                            allocation_avail = allocation_avail - alloc_vol

                    if allocation_avail < 0:
                        raise Exception("Node %s cannot satisfy allocation." % (node.name))

                    if len(node.out_links) > 0:
                        # Split the remaining water equally between remaining links
                        link_alloc = 1/len(node.out_links)
                        for seq in node.out_links:
                            supply = node.actual_release * link_alloc
                            if seq.end_node.node_type == 'farm':
                                seq.flow = min(seq.end_node.demand, supply)
                            else:
                                seq.flow = supply

