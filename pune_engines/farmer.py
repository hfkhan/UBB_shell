from pynsim import Engine
import pandas as pd


class FarmerDecision(Engine):
    """
    This simple farmer decision model is being created to test the addition of groundwater nodes to specific agents,
    and to allow the linkage of groundwater heads/pumping with the hydrologic model developed by IIASA. In this simple model,
    farmers will make a decision about the quantity of groundwater to pump based on rainfall, surface water availability (canals) and
    crop water requirements. Farmers have prescribed land use. I'm assuming a static yield. This decision to pump groundwater will be based on the
    cost of pumping which will be determined using groundwater head. This groundwater pumping decision will then be
    fed to the hydrologic model.

    The synthetic inputs needed for this model include:
    Static: For each farmer agent: land area, type of crop and yield; For each crop: crop water requirement and crop price
    Dynamic: depth to groundwater table (dwt), effective precipitation (m)

    Units
    area in hectares (randomly assigned)
    yield in kg/hectares (randomly assigned)
    cwr in mm (https://aphrdi.ap.gov.in/documents/Trainings@APHRDI/AEEs/syllabus/Crop%20Water%20Requirement.pdf)
        assume (unrealistically) crop water requirements is uniformly distributed across the year
    depth to water table (dtw) in m
    Peff in m
    """

    name = "Farmer Decision module"
    target = None

    def run(self):
        # for each target node in each time step,
        #   read in the groundwater head
        #   read in effective precip
        #   obtain the cropped area and type of crop
        #   calculate total crop water requirement
        #   determine surface water availability
        #   determine groundwater pumping needed
        #   determine energy req

        farm_heads = pd.ExcelFile("data\dwt.xlsx").parse()
        farm_prec = pd.ExcelFile("data\precip.xlsx").parse()

        for f in self.target.nodes:
            f.gw_head = farm_heads.loc[farm_heads['node'] == f.name].dwt.values[0]

            cwr = f.network.cropdata.loc[f.network.cropdata['crop'] == f.crop].cwr.values[0]*0.001 # convert to m

            area_m = f.area*10000 # convert from hectares to m2

            tot_cwr = area_m*cwr*0.000001 #in million cubic meters
            f.canal_avail = sum([l.flow for l in f.in_links]) #in million cubic meters
            f.prec_avail = 0.000001 * area_m * farm_prec.loc[farm_prec['agent'] == f.name].precip.values[0] #multiply by area to convert to volume in MCM
            total_surf = f.canal_avail + f.prec_avail

            f.gw_pumping = max(0, tot_cwr - total_surf) #million cubic meters
            # https://www.cottoninfo.com.au/sites/default/files/documents/Fundamentals%20EnergyFS_A_3a.pdf
            f.pump_energy = 2725* f.gw_pumping * f.gw_head #(kWh) #coefficient for million m3

            f.demand = f.gw_pumping



