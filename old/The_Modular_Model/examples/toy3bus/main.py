""" The birth of NEWEN Operation: MAIN"""

from __future__ import division
import pyomo.environ
from pyomo.opt import SolverFactory, SolverStatus
from pyomo.environ import *
import pandas as pd
import os
from timeit import default_timer as timer

import core_module

"""
This file is the central point of The Modular Model. It has a module section, where modules are loaded and the 
AbstractModel and DataPortal are constructed, then it has a unit commitment (UC) section, where an instance
is created and the problem is solved. Finally it has an economic dispatch (ED) section, where if specified an 
instance is created and the problem is solved.
"""

""" 
Module section
"""
#Primero, se generan los objetos del tipo AbstractModel y DataPortal 
model = AbstractModel()
data = DataPortal()

#Luego, se le pide a core_model que cree los componentes bases del modelo
model=core_module.build_model(model)
print "Core model initialized"

#Se lee el archivo modules.txt que es definido por el usuario, y dice los modulos a usar
imports = (pd.read_csv('modules.txt'))['MODULES']
modules = []

#Si se especifica correr un economic_dispatch, se cambia un boolean y esto se hara al final.
Post_Simulation = False
if 'basic_economic_dispatch' in imports.values:
    Post_Simulation = True
    post_imports = []
    imports = [name for name in imports if name != 'basic_economic_dispatch']
    post_imports.append('basic_economic_dispatch')
    post_modules = []

#Se trata de importar todos los modulos especificados. Deben estar en la misma carpeta
for x in imports:
    try:
        modules.append(__import__(x))
        print "Successfully imported ", x, '.'
    except ImportError:
        print "Error importing ", x, '.'

#Se le pide a cada uno de los modulos, que construya componentes del modelo.
for module in modules:
    model = module.build_model(model)
    print "Model successfully built from", module, '.'

#Se le pide al core_module que finalice la funcion objetivo y restricciones clave.
model=core_module.complete_model(model)
print "Core model completed"

#Se carga en el DataPortal los datos relativos a cada modulo.
for module in modules:
    data = module.load_data(model, data)
    print "Data successfully loaded from ", module, '.'
    
""" 
Main process for the unit commitment
"""

#Se combina el AbstractModel y el DataPortal para crear la instancia a resolver
instance = model.create_instance(data)
print "Model instance successfully created"

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
time = end-start
print time
#Es importante mencionar que los resultados ahora estan en instance.

#Con el problema ya resuelto, se le pide a cada modulo que genere sus propios outputs.
for module in modules:
    module.export_results(instance)
    print "Results successfully exported from", module, '.'

""" 
Main process for the economic dispatch
"""
#Si se declaro al principio, ahora ocurre el despacho con la solucion del commitment.
if Post_Simulation:
    #La estructura es similar al caso anterior. Se parte creando los objetos.
    post_model = AbstractModel()
    post_data = DataPortal()

    
    #Se trata de importar los modulos declarados (por ahora solo puede ir Economic Dispatch).
    for x in post_imports:
        try:
            post_modules.append(__import__(x))
            print "Successfully imported ", x, '.'
        except ImportError:
            print "Error importing ", x, '.'
    
    #Se construyen los componentes del modelo en el AbstractModel. Aqui no se depende del core aun.
    for module in post_modules:
        post_model = module.build_model(post_model)
        print "Model successfully built from", module, '.'
    
    #En el DataPortal se cargan los datos del modulo.
    for module in post_modules:
        post_data = module.load_data(post_model, post_data)
        print "Data successfully loaded from ", module, '.'
    
    #Se juntan el AbstractModel y el DataPortal y se crea la instancia
    post_instance = post_model.create_instance(post_data)
    print "Model instance successfully created"
    
    #Se resuelve el problema de optimizacion. Timer() se usa para medir el tiempo.
    post_instance.preprocess()
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
    results = opt.solve(post_instance,keepfiles=keepfiles,tee=stream_solver)
    end = timer()
    print("Problem solved in: %.4fseconds" % (end-start))
    time = end-start
    print time
    #Es importante mencionar que los resultados ahora estan en instance.
    
    #Con el problema ya resuelto, se le pide a cada modulo que genere sus propios outputs.
    for module in post_modules:
        module.export_results(post_instance)
        print "Results successfully exported from", module, '.'