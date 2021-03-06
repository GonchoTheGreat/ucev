""" The birth of NEWEN Operation: UNIT COMMITMENT"""

from __future__ import division
import pyomo.environ
from pyomo.opt import SolverFactory, SolverStatus
from pyomo.environ import *
import pandas as pd
import os
from timeit import default_timer as timer

""" 
ISSUES:
1. RESERVE MARKET
2. BATTERIES

"""

model = AbstractModel()

model.LOADZONES = Set()
model.GEN = Set()
model.LINE = Set()
model.TIMEPOINT = Set()

model.noloadcost = Param(model.GEN)
model.startupcost = Param(model.GEN)
model.shutdowncost = Param(model.GEN)
model.variablecost = Param(model.GEN)
model.mindowntime = Param(model.GEN)
model.minuptime = Param(model.GEN)
model.genpmin = Param(model.GEN)
model.genpmax = Param(model.GEN)
model.rampup = Param(model.GEN)
model.rampdown = Param(model.GEN)
model.shutdownramp = Param(model.GEN)
model.startupramp = Param(model.GEN)
model.genzone = Param(model.GEN)
model.genisvariable = Param(model.GEN)
model.genuseswatercost = Param(model.GEN)
model.geninitstatus = Param(model.GEN, default=0, within=Binary)
model.geninitpg = Param(model.GEN, default=0, within=Reals)

model.frombus = Param(model.LINE)
model.tobus = Param(model.LINE)
model.constant = Param(model.LINE)
model.flowlimit = Param(model.LINE)

model.overgencost = Param(model.LOADZONES)
model.loadsheddingcost = Param(model.LOADZONES)

model.zonedemand = Param(model.TIMEPOINT,model.LOADZONES)

model.GENS_IN_ZONE = Set(
    model.LOADZONES,
    initialize=lambda m, lz: set(
        gen for gen in m.GEN if m.genzone[gen] == lz))

model.LINES_TO_ZONE = Set(
    model.LOADZONES,
    initialize=lambda m, lz: set(
        line for line in m.LINE if m.tobus[line] == lz))

model.LINES_FROM_ZONE = Set(
    model.LOADZONES,
    initialize=lambda m, lz: set(
        line for line in m.LINE if m.frombus[line] == lz))

model.VARIABLE_GENS = Set(
    initialize=lambda m: set(
        gen for gen in m.GEN if m.genisvariable[gen]))

model.VARIABLE_WATER_COST_GENS = Set(
    initialize=lambda m: set(
        gen for gen in m.GEN if m.genuseswatercost[gen]))

model.capacityfactor = Param(model.TIMEPOINT, model.VARIABLE_GENS)
model.variablewatercost = Param(model.TIMEPOINT, model.VARIABLE_WATER_COST_GENS)

model.GenCommit = Var(model.GEN, model.TIMEPOINT, domain=Binary)
model.GenStartUp = Var(model.GEN, model.TIMEPOINT, domain=Binary)
model.GenShutDown = Var(model.GEN, model.TIMEPOINT, domain=Binary)
model.GenPg = Var(model.GEN, model.TIMEPOINT, domain=NonNegativeReals)
model.PowerFlow = Var(model.LINE, model.TIMEPOINT, domain=Reals)
model.Theta = Var(model.LOADZONES, model.TIMEPOINT, domain=Reals)
model.OverGeneration = Var(model.LOADZONES, model.TIMEPOINT, domain=NonNegativeReals)
model.LoadShedding = Var(model.LOADZONES, model.TIMEPOINT, domain=NonNegativeReals)

def obj_expression(m):
    
    Total_Variable_Cost = 0.0
    Total_No_Load_Cost = 0.0
    Total_Start_Up_Cost = 0.0
    Total_Shut_Down_Cost = 0.0
    Total_Over_Gen_Cost = 0.0
    Total_Load_Shedding_Cost = 0.0
    
    for t in m.TIMEPOINT:
        for gen in m.GEN:
            Total_No_Load_Cost += m.noloadcost[gen]*m.GenCommit[gen,t]
            Total_Start_Up_Cost += m.startupcost[gen]*m.GenStartUp[gen,t] 
            Total_Shut_Down_Cost += m.shutdowncost[gen]*m.GenShutDown[gen,t] 
            if gen in m.VARIABLE_WATER_COST_GENS:
                Total_Variable_Cost += m.variablewatercost[t,gen]*m.GenPg[gen,t]
            else:
                Total_Variable_Cost += m.variablecost[gen]*m.GenPg[gen,t]
        for lz in m.LOADZONES:
            Total_Over_Gen_Cost += m.overgencost[lz]*m.OverGeneration[lz,t]
            Total_Load_Shedding_Cost += m.loadsheddingcost[lz]*m.LoadShedding[lz,t]
            
    return (Total_Variable_Cost 
            + Total_No_Load_Cost 
            + Total_Start_Up_Cost 
            + Total_Over_Gen_Cost
            + Total_Load_Shedding_Cost)
    
model.Obj = Objective(rule=obj_expression)  

def gen_p_min_rule(m, gen, t):
    if gen in m.VARIABLE_GENS:
        return (m.GenCommit[gen,t]*m.genpmin[gen]<= m.GenPg[gen,t])
    else:
        return (m.GenCommit[gen,t]*m.genpmin[gen]<= m.GenPg[gen,t])
model.Gen_P_Min = Constraint(model.GEN, model.TIMEPOINT, rule=gen_p_min_rule)

def gen_p_max_rule(m, gen, t):
    if gen in m.VARIABLE_GENS:
        return (m.GenPg[gen,t] <= m.GenCommit[gen,t]*m.genpmax[gen]*m.capacityfactor[t,gen])
    else:
        return (m.GenPg[gen,t] <= m.GenCommit[gen,t]*m.genpmax[gen])
model.Gen_P_Max = Constraint(model.GEN, model.TIMEPOINT, rule=gen_p_max_rule)

def on_off_rule(m, gen, t):
    if t>1:
        return m.GenCommit[gen,t]-m.GenCommit[gen,(t-1)] == m.GenStartUp[gen,t] - m.GenShutDown[gen,t]
    if t==1:
        return m.GenCommit[gen,t] -m.geninitstatus[gen]== m.GenStartUp[gen,t] - m.GenShutDown[gen,t]
model.Gen_On_Off = Constraint(model.GEN, model.TIMEPOINT, rule=on_off_rule)
    
def min_start_up_rule(m, gen, t):
    if (t <= len(m.TIMEPOINT) - m.minuptime[gen]+1):
        return sum(m.GenCommit[gen,tau] for tau in range(t,t+m.minuptime[gen])) >= m.minuptime[gen]*m.GenStartUp[gen,t]
    else:
        return Constraint.Feasible
model.Gen_Min_Start_Up = Constraint(model.GEN, model.TIMEPOINT, rule=min_start_up_rule)

def min_shut_down_rule(m, gen, t):
    if (t <= len(m.TIMEPOINT) - m.mindowntime[gen]+1):
        return sum((1-m.GenCommit[gen,tau]) for tau in range(t,t+m.mindowntime[gen])) >= m.mindowntime[gen]*m.GenShutDown[gen,t]
    else:
        return Constraint.Feasible
model.Gen_Min_Shut_Down = Constraint(model.GEN, model.TIMEPOINT, rule=min_shut_down_rule)

def min_start_up_bound_rule(m, gen, t):
    if (t >= len(m.TIMEPOINT) - m.minuptime[gen]+1):
        return sum(m.GenCommit[gen,tau]-m.GenStartUp[gen,t] for tau in range(t, len(m.TIMEPOINT)+1)) >=0
    else:
        return Constraint.Feasible
model.Gen_Min_Start_Up_Bound = Constraint(model.GEN, model.TIMEPOINT, rule=min_start_up_bound_rule)

def min_shut_down_bound_rule(m, gen, t):
    if (t >= len(m.TIMEPOINT) - m.mindowntime[gen]+1):
        return sum(1-m.GenCommit[gen,tau]-m.GenShutDown[gen,t] for tau in range(t,len(m.TIMEPOINT)+1)) >= 0 
    else:
        return Constraint.Feasible
model.Gen_Min_Shut_Down_Bound = Constraint(model.GEN, model.TIMEPOINT, rule=min_shut_down_bound_rule)

def lower_ramp_rule(m, gen, t):
    if t>1:
        return (-m.rampdown[gen]*m.GenCommit[gen,t] - m.shutdownramp[gen]*m.GenShutDown[gen,t] 
                <= m.GenPg[gen,t]-m.GenPg[gen,(t-1)] 
                )
    if t==1:
        return (-m.rampdown[gen]*m.GenCommit[gen,t] - m.shutdownramp[gen]*m.GenShutDown[gen,t] 
                <= m.GenPg[gen,t] - m.geninitpg[gen]
                )
model.Lower_Gen_Ramps = Constraint(model.GEN, model.TIMEPOINT, rule=lower_ramp_rule)

def upper_ramp_rule(m, gen, t):
    if t>1:
        return (m.GenPg[gen,t]-m.GenPg[gen,(t-1)] 
                <= m.rampup[gen]*m.GenCommit[gen,t] + m.startupramp[gen]*m.GenStartUp[gen,t])
    if t==1:
        return (m.GenPg[gen,t] - m.geninitpg[gen]
                <= m.rampup[gen]*m.GenCommit[gen,t] + m.startupramp[gen]*m.GenStartUp[gen,t])
model.Upper_Gen_Ramps = Constraint(model.GEN, model.TIMEPOINT, rule=upper_ramp_rule)

def power_flow_rule(m, line, t):
    frombus = m.frombus[line]
    tobus = m.tobus[line]
    return m.PowerFlow[line,t]== m.constant[line] * (m.Theta[frombus, t] - m.Theta[tobus,t])
model.DcPowerFlow = Constraint(model.LINE, model.TIMEPOINT, rule=power_flow_rule)

def flow_bound_rule(m,line,t):
    return m.PowerFlow[line, t]<= m.flowlimit[line]
model.FlowBound = Constraint(model.LINE, model.TIMEPOINT, rule=flow_bound_rule)

def zone_load_balance_rule(m, lz, t):
        return (
                m.zonedemand[t, lz] 
            + m.OverGeneration[lz,t]
            - m.LoadShedding[lz,t]
            == sum(m.GenPg[gen,t] for gen in m.GENS_IN_ZONE[lz]) 
            + sum(m.PowerFlow[line,t] for line in m.LINES_TO_ZONE[lz])
            - sum(m.PowerFlow[line,t] for line in m.LINES_FROM_ZONE[lz])
            )
model.Zone_Load_Balance = Constraint(model.LOADZONES, model.TIMEPOINT, rule=zone_load_balance_rule)

def theta_bound_rule(m, lz, t):
    return Constraint.Feasible
model.Theta_Bounds = Constraint(model.LOADZONES, model.TIMEPOINT, rule=theta_bound_rule)

data = DataPortal()
inputs_dir = 'uc_inputs'

data.load(filename=os.path.join(inputs_dir,'load_zones.tab'), 
          param=(model.overgencost, model.loadsheddingcost), 
          index=model.LOADZONES)

data.load(filename=os.path.join(inputs_dir,'timepoints.tab'), set=model.TIMEPOINT, format="set")

data.load(filename=os.path.join(inputs_dir,'gen.tab'), 
          param=(model.noloadcost, model.startupcost, model.shutdowncost, model.variablecost, 
                 model.mindowntime, model.minuptime, 
                 model.genpmin, model.genpmax, 
                 model.rampup, model.rampdown,
                 model.startupramp, model.shutdownramp,
                 model.genzone, model.genisvariable, model.genuseswatercost),
          index=model.GEN)

#data.load(filename=os.path.join(inputs_dir,'line.tab'), 
#          param=(model.constant, model.tobus, model.frombus, model.flowlimit), 
#          index=model.LINE)

data.load(filename=os.path.join(inputs_dir,'zone_demand.tab'),
          param=model.zonedemand,
          format='array')

#data.load(filename=os.path.join(inputs_dir,'variable_capacity_factors.tab'),
#          param=model.capacityfactor,
#          format='array')
#
#data.load(filename=os.path.join(inputs_dir,'variable_water_cost.tab'),
#          param=model.variablewatercost,
#          format='array')

instance = model.create_instance(data)
print "Model instance successfully created"

instance.preprocess()
solver = 'gurobi' # ipopt gurobi
if solver == 'gurobi':
    opt = SolverFactory(solver)
elif solver == 'ipopt':
    solver_io = 'nl'
    opt = SolverFactory(solver,solver_io=solver_io)
if opt is None:
    print("ERROR: Unable to create solver plugin for %s using the %s interface" % (solver, solver_io))
    exit(1)
        
stream_solver =True # True prints solver output to screen
keepfiles = False # True prints intermediate file names (.nl,.sol,...)
start = timer()
results = opt.solve(instance,keepfiles=keepfiles,tee=stream_solver)
end = timer()
print("Problem solved in: %.4fseconds" % (end-start))
time = end-start
print time

GEN_COMMIT = pd.DataFrame(data=[[instance.GenCommit[gen,t].value for gen in instance.GEN] for t in instance.TIMEPOINT], 
                          columns=instance.GEN, index=instance.TIMEPOINT)
GEN_START_UP = pd.DataFrame(data=[[instance.GenStartUp[gen,t].value for gen in instance.GEN] for t in instance.TIMEPOINT], 
                          columns=instance.GEN, index=instance.TIMEPOINT)
GEN_SHUT_DOWN = pd.DataFrame(data=[[instance.GenShutDown[gen,t].value for gen in instance.GEN] for t in instance.TIMEPOINT], 
                          columns=instance.GEN, index=instance.TIMEPOINT)
GEN_PG = pd.DataFrame(data=[[instance.GenPg[gen,t].value for gen in instance.GEN] for t in instance.TIMEPOINT], 
                          columns=instance.GEN, index=instance.TIMEPOINT)
LOAD_SHEDDING = pd.DataFrame(data=[[instance.LoadShedding[lz,t].value for lz in instance.LOADZONES] for t in instance.TIMEPOINT],
                             columns= instance.LOADZONES, index=instance.TIMEPOINT)
OVER_GEN = pd.DataFrame(data=[[instance.OverGeneration[lz,t].value for lz in instance.LOADZONES] for t in instance.TIMEPOINT],
                             columns= instance.LOADZONES, index=instance.TIMEPOINT)
POWER_FLOW = pd.DataFrame(data=[[instance.PowerFlow[line,t].value for line in instance.LINE] for t in instance.TIMEPOINT],
                             columns= instance.LINE, index=instance.TIMEPOINT)
THETA = pd.DataFrame(data=[[instance.Theta[lz,t].value for lz in instance.LOADZONES] for t in instance.TIMEPOINT],
                             columns= instance.LOADZONES, index=instance.TIMEPOINT)

script_dir = os.path.dirname(__file__)
results_dir = 'uc_outputs'

if not os.path.isdir(results_dir):
    os.makedirs(results_dir)
    
GEN_COMMIT.to_csv(os.path.join(results_dir,'gen_commit.tab'),sep='\t')
GEN_START_UP.to_csv(os.path.join(results_dir,'gen_start_up.tab'),sep='\t')
GEN_SHUT_DOWN.to_csv(os.path.join(results_dir,'gen_shut_down.tab'),sep='\t')
GEN_PG.to_csv(os.path.join(results_dir,'gen_pg.tab'),sep='\t')
LOAD_SHEDDING.to_csv(os.path.join(results_dir,'load_shedding.tab'),sep='\t')
OVER_GEN.to_csv(os.path.join(results_dir,'over_gen.tab'),sep='\t')
POWER_FLOW.to_csv(os.path.join(results_dir,'power_flow.tab'), sep='\t')
THETA.to_csv(os.path.join(results_dir,'theta.tab'), sep='\t')