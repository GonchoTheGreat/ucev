"""
-- NEWEN Operation Model -- (OCM-lab)
Developers: Cordova Samuel, Verastegui Felipe

This module defines the hidraulic connectivity between hidraulic centrals
and irrigations enforcements
"""

from __future__ import division
import pyomo.environ
from pyomo.environ import *
import pandas as pd
import os

#Filtro para identificar centrales hidraulicas, aguas arriba y aguas abajo
def filt_gen_hydro(model,g):
    return model.technology[g] == 'hydro'


#Se define una funcion que aumenta un AbstractModel
def build_model(model):

    # Sets
    model.HYDRO = Set()
    model.GEN_HYDRO = Set(initialize=model.GEN,filter=filt_gen_hydro)

    # Variables
    model.QTurb  = Var(model.HYDRO, model.TIMEPOINT,domain=NonNegativeReals)
    model.QSpill = Var(model.HYDRO, model.TIMEPOINT,domain=NonNegativeReals)

    # Parametros adicionales
    model.hydrotype = Param(model.HYDRO)
    model.hydroeff = Param(model.HYDRO,domain=NonNegativeReals)
    model.turbto = Param(model.HYDRO)
    model.spillto = Param(model.HYDRO)
    model.inflow = Param(model.HYDRO,domain=NonNegativeReals) #Extender a [t]
    #por convenios (extender model.TIMEPOINT) -- DEBUGD --
    model.qmax = Param(model.HYDRO,domain=NonNegativeReals)
    model.qmin = Param(model.HYDRO,domain=NonNegativeReals)
    model.spillmax = Param(model.HYDRO,domain=NonNegativeReals)
    model.spillmin = Param(model.HYDRO,domain=NonNegativeReals)
    model.qdem = Param(model.HYDRO,domain=NonNegativeReals)

    #Subsets necesarios para indexar sumatorias o restricciones
    model.UPFLOW_TURB = Set(
        model.HYDRO,
        initialize=lambda m, hdn: set(
            hup for hup in m.HYDRO if m.turbto[hup] == hdn))

    model.UPFLOW_SPILL = Set(
        model.HYDRO,
        initialize=lambda m, hdn: set(
            hup for hup in m.HYDRO if m.spillto[hup] == hdn))

    #Restricciones
    def hydro_balance_rule(m,h,t):
        return (
            m.inflow[h] + sum(m.QTurb[hturb,t] for hturb in m.UPFLOW_TURB[h])
            + sum(m.QSpill[hspill,t] for hspill in m.UPFLOW_SPILL[h])
            == m.QTurb[h,t] + m.QSpill[h,t]
        )
    model.HydroBalance = Constraint(model.HYDRO,model.TIMEPOINT,
        rule=hydro_balance_rule)

    def hydro_efficiency(m,g,t):
        return(m.QTurb[g,t]*m.hydroeff[g] == m.GenPg[g,t])
    model.HydroEfficiency = Constraint(model.GEN_HYDRO,model.TIMEPOINT,
        rule=hydro_efficiency)

    def qmax_rule(m,h,t):
        return(m.QTurb[h,t] <= m.qmax[h])
    model.QMaxConstraint = Constraint(model.HYDRO,model.TIMEPOINT,
        rule=qmax_rule)

    def spillmax_rule(m,h,t):
        return(m.QSpill[h,t] <= m.spillmax[h])
    model.SpillMaxContraint = Constraint(model.HYDRO,model.TIMEPOINT,
        rule=spillmax_rule)

    def qmin_rule(m,h,t):
        return(m.qmin[h] <= m.QTurb[h,t])
    model.QMinConstraint = Constraint(model.HYDRO,model.TIMEPOINT,
        rule=qmin_rule)

    def spillmin_rule(m,h,t):
        return(m.spillmin[h] <= m.QTurb[h,t])
    model.SpillMinConstraint = Constraint(model.HYDRO,model.TIMEPOINT,
        rule=spillmin_rule)

    def qdem_rule(m,h,t):
        return(m.QTurb[h,t] >= m.qdem[h])
    model.QDemConstraint = Constraint(model.HYDRO,model.TIMEPOINT,
        rule=qdem_rule)

    return model

#Se define una funcion que carga datos en un DataPortal.
def load_data(model, data, inputs_dir):

    data.load(filename=os.path.join(inputs_dir,'hydro_conectivity.csv'),
              param=(model.hydrotype,model.hydroeff, model.turbto,
                    model.spillto, model.inflow, model.qmax, model.qmin,
                    model.spillmax, model.spillmin, model.qdem),
                    index=model.HYDRO)

    return data

#Se define una funcion para generar outputs en base a los resultados.
def export_results(instance,output_dir,flag_concat,concat_dir):

    HYDRO_TURB = pd.DataFrame(data=[[instance.QTurb[h,t].value for h in instance.HYDRO] for t in instance.TIMEPOINT],
                                columns=instance.HYDRO, index=instance.TIMEPOINT)
    HYDRO_SPILL = pd.DataFrame(data=[[instance.QSpill[h,t].value for h in instance.HYDRO] for t in instance.TIMEPOINT],
                                columns=instance.HYDRO, index=instance.TIMEPOINT)

    #Se exportan los archivos. Si el path no esta, se crea
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    HYDRO_TURB.to_csv(os.path.join(output_dir,'hydro_turb.csv'))
    HYDRO_SPILL.to_csv(os.path.join(output_dir,'hydro_spill.csv'))
