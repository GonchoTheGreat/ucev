"""
-- NEWEN Operation Model -- (OCM-lab)
Developers: Cordova Samuel, Verastegui Felipe

This file is the central point of the model. It has a module section, where
modules are loaded and the AbstractModel and DataPortal are constructed, an
instance is created and the problem is solved.
"""

from __future__ import division
import pyomo.environ
from pyomo.opt import SolverFactory, SolverStatus
from pyomo.environ import *
import pandas as pd
import os
from timeit import default_timer as timer

import core_module

"""
Module section
"""
def execute(imports,inputs,output_dir,concat_dir):
    #Primero, se generan los objetos del tipo AbstractModel y DataPortal
    model = AbstractModel()
    data = DataPortal()

    #Luego, se le pide a core_model que cree los componentes bases del modelo
    model=core_module.build_model(model)
    print("Core model initialized")

    #Se crea lista de modulos a usar
    modules = []

    #Se trata de importar todos los modulos especificados. Deben estar en la misma carpeta
    for x in imports:
        try:
            modules.append(__import__(x))
            print("Successfully imported ", x)
        except ImportError:
            print("Error importing ", x)

    #Se le pide a cada uno de los modulos, que construya componentes del modelo.
    for module in modules:
        model = module.build_model(model)
        print("Model successfully built:", module)

    #Se le pide al core_module que finalice la funcion objetivo y restricciones clave.
    model=core_module.complete_model(model)
    print("Core model completed")

    #Mensajes adicionales (datos y salidas)
    for module,input_dir in zip(modules,inputs):
        data = module.load_data(model,data,input_dir)
        print("Data successfully loaded from", input_dir)

    print("Results will be exported to", output_dir, '.')
    flag_concat = False
    if isinstance(concat_dir,str):
        flag_concat = True
        print("Concatenating files will be generated in",concat_dir,".")

    """
    Main process for the unit commitment/economic dispatch
    """

    #Se combina el AbstractModel y el DataPortal para crear la instancia a resolver
    instance = model.create_instance(data)
    print("Model instance successfully created")

    #Se resuelve el problema de optimizacion. Timer() se usa para medir el tiempo.
    instance.preprocess()
    solver = 'gurobi'
    if solver == 'gurobi':
        opt = SolverFactory(solver)
    elif solver == 'ipopt':
        solver_io = 'nl'
        opt = SolverFactory(solver,solver_io=solver_io)
    if opt is None:
        print("ERROR: Unable to create solver plugin for %s using the %s interface" % (solver, solver_io))
        exit(1)
    stream_solver =True # Opcional, imprime el solver a la pantalla.
    keepfiles = False # Opcional, guarda archivos intermedios.
    start = timer()
    results = opt.solve(instance,keepfiles=keepfiles,tee=stream_solver)
    end = timer()
    print("Problem solved in: %.4fseconds" % (end-start))
    #Es importante mencionar que los resultados ahora estan en instance.

    #Con el problema ya resuelto, se le pide a cada modulo que genere sus propios outputs.
    for module in modules:
        module.export_results(instance,output_dir,flag_concat,concat_dir)
    print("Results successfully exported")

if __name__ == '__main__':

    param_csv = pd.read_csv('parameters.csv')
    imports = param_csv['Modules']
    inputs = param_csv['Input']
    output_dir = param_csv['Output'][0]
    concat_dir = param_csv['Concatenate'][0]

    execute(imports,inputs,output_dir,concat_dir)
