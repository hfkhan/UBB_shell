## ENTIRE RUN FILE FOR THE PUNE PROTOTYPE


__author__ = 'hassaankhan'
import time
import pandas as pd
import numpy as np
import logging
import shapefile
log = logging.getLogger(__name__)
from __future__ import division

from pynsim import Network
from pynsim import Simulator
from dateutil.relativedelta import relativedelta
import datetime

from pune_components.nodes.network_nodes import Pune_Reservoir, FarmAgent, Junction, WTP, WWTP
from pune_components.links.links import River, Canal, Pipeline
from pune_components.institutions.institutions import MKVDC, PMC, WUA, WRD, AllNodesOfType
import pune_engines
##############################################

model_inputs_xlsx = pd.ExcelFile("C:\Users\hfkhan\Desktop\PycharmProjects\Pune\data\model_setup.xlsx")
simulation_inputs = model_inputs_xlsx.parse("simulation")
network_inputs = model_inputs_xlsx.parse("network")
engines_inputs = model_inputs_xlsx.parse("engines")

res_inputs = pd.ExcelFile("data/reservoirs.xlsx")
res_char = res_inputs.parse('res_char')

farmerdata = pd.ExcelFile("data/farmers.xlsx").parse()
cropdata = pd.ExcelFile("data/crops.xlsx").parse()

##############################################

############################################################################################################
# SIMULATOR
############################################################################################################
start_time = time.time()

# Setup Simulation
pune_simulation = Simulator()

number_of_years = simulation_inputs[simulation_inputs.simulation_name == 'prototype']['number_of_years'].values[0]
start_month = simulation_inputs[simulation_inputs.simulation_name == 'prototype']['start_month'].values[0]

num_months = 12 * number_of_years - 1
one_month = relativedelta(months=1)

timesteps = [datetime.datetime.strptime(start_month, '%b %Y')]

for m in range(num_months):
    new_timestep = timesteps[-1] + one_month
    timesteps.append(new_timestep)


pune_simulation.set_timesteps(timesteps)

############################################################################################################
# NETWORK
############################################################################################################
network_name = 'prototype network'
network = Network(name=network_name)

global network_nodes
global network_links

# Read in network nodes from shapefile
network_nodes_obj = shapefile.Reader('C:\Users\hfkhan\Desktop\PycharmProjects\Pune\data\shapefiles\prototype_nodes_ubb').shapeRecords()

network_nodes = []
count = 0
for i in network_nodes_obj:
    node_name = i.record[0]
    type = i.record[3]

    if type == 'res':
        network_nodes.append(Pune_Reservoir(x=i.shape.points[0][0], y=i.shape.points[0][1], name=node_name))
    if type == 'jnc':
        network_nodes.append(Junction(x=i.shape.points[0][0], y=i.shape.points[0][1], name=node_name))
    if type == 'farm':
        network_nodes.append(FarmAgent(x=i.shape.points[0][0], y=i.shape.points[0][1], name=node_name))
    if type == 'tp':
        network_nodes.append(WTP(x=i.shape.points[0][0], y=i.shape.points[0][1], name=node_name))
    if type == 'wwtp':
        network_nodes.append(WWTP(x=i.shape.points[0][0], y=i.shape.points[0][1], name=node_name))

    network_nodes[count].node_type = i.record[3]
    network_nodes[count].institution_names = ['mkvdc']

    count = count + 1

# Read in network links from shapefile
network_links_obj = shapefile.Reader('C:\Users\hfkhan\Desktop\PycharmProjects\Pune\data\shapefiles\prototype_links_ubb').shapeRecords()
network_links = []
count = 0
for i in network_links_obj:
    link_name = i.record[4]
    link_type = i.record[5]
    link_start = i.record[6]
    link_end = i.record[7]
    for start in network_nodes:
        for end in network_nodes:
            if start.name == link_start and end.name == link_end:
                if link_type == 'river':
                    templink = River(start_node=start, end_node=end, name=link_name)
                    templink.linktype = 'River'
                    network_links.append(templink)

                if link_type == 'pipeline':
                    templink = Pipeline(start_node=start, end_node=end, name=link_name)
                    templink.linktype = 'Pipeline'
                    network_links.append(templink)

                if link_type == 'canal':
                    templink = Canal(start_node=start, end_node=end, name=link_name)
                    templink.linktype = 'Irr Canals'
                    network_links.append(templink)

    network_links[count].institution_names = 'mkvdc' #FOR NOW, ASSUMING ALL THE NODES/LINKS ARE OPERATED BY MKVDC
    count = count + 1

network.add_nodes(*network_nodes)
network.add_links(*network_links)

### Read in reservoir characteristics
allres = ["R" + str(i).zfill(2) for i in xrange(1,56)]
allfarms = ["T" + str(i).zfill(2) for i in xrange(1,45)]

#res_char.iloc[:,1]

for p in allres:
    s_node = network.get_node(p)
    myrec = res_char.loc[res_char['Res_ID'] == p]

    s_node.min_stor = myrec.min_stor.values[0]
    s_node.max_stor = myrec.max_stor.values[0]
    s_node.init_stor = myrec.init_stor.values[0]
    s_node.release_schedule = myrec.iloc[:,5:17].values.tolist()[0]

for f in allfarms:
    f_node = network.get_node(f)
    sel_f = farmerdata.loc[farmerdata['agent']== f]
    f_node.area = sel_f.area.values[0] #area in hectares (randomly assigned)
    f_node.crop = sel_f.crop.values[0]
    f_node.y = sel_f.cyield.values[0] # yield in kg/hectares

network.cropdata = cropdata

pune_simulation.network = network

############################################################################################################
# INSTITUTIONS
############################################################################################################

# INSTITUTION SETUP #
institution_list =[]

institution_list.extend([MKVDC(name="mkvdc"), PMC(name="pmc"), WRD(name="wrd")])
institution_list.extend([WUA(name = "wua_pune"), WUA(name = "wua_solapur")])

all_nodes_of_type_institutions = []
all_nodes_of_type_institutions.append(AllNodesOfType('all_farms', 'FarmAgent', pune_simulation.network))
all_nodes_of_type_institutions.append(AllNodesOfType('all_reservoirs', 'Pune_Reservoir', pune_simulation.network))


pune_simulation.network.add_institutions(*institution_list)
pune_simulation.network.add_institutions(*all_nodes_of_type_institutions)

#add nodes/links to associated institutions
for n in pune_simulation.network.nodes:
    n.add_to_institutions(n.institution_names, pune_simulation.network)  # add nodes to designated institutions

for l in pune_simulation.network.links:
    l.add_to_institutions(l.institution_names, pune_simulation.network)  # add links to designated institutions

############################################################################################################
# ENGINES
############################################################################################################

no_of_engines = engines_inputs[(engines_inputs.simulation_name == 'prototype')].shape[0]

for e in range(no_of_engines):
    engine_class = engines_inputs[(engines_inputs.simulation_name == 'prototype') &
                                  (engines_inputs.order == e + 1)]['engine_class'].values[0]
    engine_target = engines_inputs[(engines_inputs.simulation_name == 'prototype') &
                                   (engines_inputs.order == e + 1)]['engine_target'].values[0]

    EngineClass = getattr(pune_engines, engine_class)

    target = pune_simulation.network.get_institution(engine_target)

    new_engine = EngineClass(target)
    pune_simulation.add_engine(new_engine)

##############################################################################################################################
##############################################################################################################################

pune_simulation.start()

end_time = time.time()
sim_time = end_time-start_time
print "Simulation took:  %s" % sim_time

