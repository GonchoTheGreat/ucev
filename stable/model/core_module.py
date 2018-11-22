""" The birth of NEWEN Operation: CORE MODULE """

from __future__ import division
import pyomo.environ
from pyomo.opt import SolverFactory, SolverStatus
from pyomo.environ import *
import pandas as pd
import os
from timeit import default_timer as timer

"""
This module defines basic components for the operational problemas that will be studied.
"""

#Se define una primera funcion encargada de definir listas dinamicas y sets basicos del modelo
def build_model(model):

    #Listas dinamicas de costos, inyecciones y retiros de energia. La idea es que todos los modulos puedan aportar a estas listas.
    model.Costs = []
    model.Zone_Power_Plus = []
    model.Zone_Power_Minus = []

    return model

#Se define una segunda funcion encargada de construir la funcion objetivo y el balance de energia.
def complete_model(model):

    #Una vez que todos los modulos hicieron sus contribuciones, se construye la funcion objetivo a partir de la lista Costs.
    def obj_expression(m):
        return sum(getattr(m, component) for component in m.Costs)
    model.Obj = Objective(rule=obj_expression)

    #Una vez que todos los modulos hicieron sus contribuciones, se construye el balance de demanda a partir de las listas ZPP-M.
    def balance_expression(m,lz,t):
        return (sum(
                getattr(m,component)[lz,t]
                for component in m.Zone_Power_Plus)
                ==
                sum(
                getattr(m,component)[lz,t]
                for component in m.Zone_Power_Minus))
    model.Zone_Energy_Balance = Constraint(model.LOADZONES, model.TIMEPOINT, rule=balance_expression)

    return model
