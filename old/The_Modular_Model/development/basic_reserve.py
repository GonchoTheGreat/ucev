""" The birth of NEWEN Operation: BASIC RESERVE MARKET FOR UNIT COMMITMENT"""

from __future__ import division
import pyomo.environ
from pyomo.opt import SolverFactory, SolverStatus
from pyomo.environ import *
import pandas as pd
import os
from timeit import default_timer as timer

""" 
This module defines a basic spinning reserve.
"""

#Se define una funcion que aumenta un AbstractModel
def build_model(model):
    
    #Variables de reserva basica para cada generador
    model.GenBasicReserve = Var(model.GEN, model.TIMEPOINT, 
                                domain=NonNegativeReals)
    
    #Requerimientos de reserva
    model.zonereservedemand = Param(model.LOADZONES, model.TIMEPOINT, 
                                    within=NonNegativeReals)

    #Balance de reserva
    def zone_reserve_balance_rule(m, lz, t):
        return (sum(m.GenBasicReserve[gen,t] for gen in m.GENS_IN_ZONE[lz]) == m.zonereservedemand[lz,t])
    model.Zone_Reserve_Balance = Constraint(model.LOADZONES, model.TIMEPOINT, 
                                            rule=zone_reserve_balance_rule)
    
    #Cota superior de reserva por generador
    def gen_max_reserve_rule(m, gen, t):
        if gen in m.VARIABLE_GENS:
            #Generadores variables no pueden dar reserva
            return (m.GenBasicReserve[gen,t] <=0)
        else:
            #Solo generadores firmes en giro pueden dar reserva.
            return (m.GenPg[gen,t] + m.GenBasicReserve[gen,t] <= m.GenCommit[gen,t]*m.genpmax[gen])
    model.Gen_Max_Reserve = Constraint(model.GEN, model.TIMEPOINT, rule=gen_max_reserve_rule)

    return model

#Se define una funcion que carga datos en un DataPortal.
def load_data(model, data):
    
    inputs_dir = 'uc_inputs'

    data.load(filename=os.path.join(inputs_dir,'zone_reserve_demand.csv'),
          param=model.zonereservedemand,
          format='transposed_array')
        
    return data

#Se define una funcion para generar outputs en base a los resultados.
def export_results(instance):
    
    GEN_BASIC_RESERVE = pd.DataFrame(data=[[instance.GenBasicReserve[gen,t].value for gen in instance.GEN] for t in instance.TIMEPOINT], 
                              columns=instance.GEN, index=instance.TIMEPOINT)
    
    results_dir = 'uc_outputs'
    
    if not os.path.isdir(results_dir):
        os.makedirs(results_dir)
        
    GEN_BASIC_RESERVE.to_csv(os.path.join(results_dir,'gen_basic_reserve.tab'),sep='\t')
    return