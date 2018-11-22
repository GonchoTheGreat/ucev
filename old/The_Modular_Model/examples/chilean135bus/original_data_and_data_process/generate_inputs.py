import pandas as pd
import os

BAR_DAT = pd.read_csv('BarDatParOpt.csv')
LIN_DAT = pd.read_csv('LinDatParOpt.csv')
DEM_IND = pd.read_csv('DemIndBloOpt_16_SIMP_SIC.csv')
CEN_DAT = pd.read_csv('CenTerPar_Exist+Const_SIC_Opt.csv')
CEN_EMB_DAT = pd.read_csv('cenembparOpt.csv')
CEN_PAS_DAT = pd.read_csv('cenpaspar_Exis+Const_Opt.csv')
CEN_SER_DAT = pd.read_csv('censerparOpt.csv')
CEN_WT_DAT = pd.concat([CEN_EMB_DAT,CEN_PAS_DAT,CEN_SER_DAT],ignore_index=True)

TIMEPOINT_DF = pd.DataFrame()
GEN_DF = pd.DataFrame()
LINE_DF = pd.DataFrame()
LOADZONE_DF = pd.DataFrame()
ZONEDEMAND_DF = pd.DataFrame()

VCFACTORS_DF = pd.DataFrame()
VWATERCOST_DF = pd.DataFrame()
ZONERSRVDEMAND_DF = pd.DataFrame()

        
LOADZONE_DF['LOADZONE'] = BAR_DAT['BarNom']
LOADZONE_DF['over_gen_cost'] = [5000 for lz in LOADZONE_DF['LOADZONE']]
LOADZONE_DF['load_shedding_cost']=[5000 for lz in LOADZONE_DF['LOADZONE']]

GEN_DF['GEN']= CEN_DAT['CenNom']
GEN_DF['no_load_cost']= [0 for gen in CEN_DAT['CenINum']]
GEN_DF['start_up_cost']= [20 for gen in CEN_DAT['CenINum']]
GEN_DF['shut_down_cost']= [20 for gen in CEN_DAT['CenINum']]
GEN_DF['variable_cost']= CEN_DAT['CenCosVar']/50
GEN_DF['min_down_time']= [2 for gen in CEN_DAT['CenINum']]
GEN_DF['min_up_time']= [2 for gen in CEN_DAT['CenINum']]
GEN_DF['gen_p_min']= CEN_DAT['CenPotMax']/10
GEN_DF['gen_p_max']= CEN_DAT['CenPotMax']
GEN_DF['ramp_up']= CEN_DAT['CenPotMax']/10
GEN_DF['ramp_down']= CEN_DAT['CenPotMax']/10
GEN_DF['start_up_ramp']= CEN_DAT['CenPotMax']/20
GEN_DF['shut_down_ramp']= CEN_DAT['CenPotMax']/7
GEN_DF['gen_zone']= CEN_DAT['CenBar']
GEN_DF['gen_is_variable']= [False for gen in CEN_DAT['CenINum']]
GEN_DF['fuel_cost_is_variable']= [False for gen in CEN_DAT['CenINum']]

LINE_DF['LINE']=LIN_DAT['LinNom']
LINE_DF['constant']=[100 for line in LINE_DF['LINE']]
LINE_DF['to_bus']=LIN_DAT['LinBarA']
LINE_DF['from_bus']=LIN_DAT['LinBarB']
LINE_DF['flow_limit']=LIN_DAT['LinPotMaxA->B']

TIMEPOINT_DF['TIMEPOINT']= range(1,25)

ZONEDEMAND_DF['T/ZONE']=TIMEPOINT_DF['TIMEPOINT']
for lz in LOADZONE_DF['LOADZONE']:
    ZONEDEMAND_DF[lz]=[50,60,50,40,30,40,50,60,50,40,30,0,30,40,50,60,50,40,30,0,30,40,50,60]


LOADZONE_DF.to_csv('load_zones.csv', sep=',', index=False)
GEN_DF.to_csv('gen.csv', sep=',', index=False)
LINE_DF.to_csv('line.csv', sep=',', index=False)
TIMEPOINT_DF.to_csv('timepoints.csv', sep=',', index=False)
ZONEDEMAND_DF.to_csv('zone_demand.csv', sep=',', index=False)
#VCFACTORS_DF.to_csv('variable_capacity_factors.csv', sep=',', index=False)
#VWATERCOST_DF.to_csv('variable_water_cost.csv', sep=',', index=False)
#ZONERSRVDEMAND_DF.to_csv('zone_reserve_demand.csv', sep=',', index=False)