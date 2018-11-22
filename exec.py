"""
-- NEWEN Operation Model -- (OCM-lab)
Developers: Cordova Samuel, Verastegui Felipe

This is the execution files which calls both the main and the rest of the
modules indicated by the user for the electric system operation simulation
"""

import pandas as pd
import sys

# Reads parameters for the execution
model_csv = pd.read_csv('model_dir.csv')
param_csv = pd.read_csv('parameters.csv')

# Preliminary setup for the model
model_folder = model_csv['Model'][0]
stages = range(1,param_csv['Stage'].max()+1)
sys.path.insert(0,model_folder)
import main

# Starts simulating by stage
for s in stages:
    print("--- Simulating stage",s,"---")
    stage_df = param_csv.loc[param_csv['Stage']==s].reset_index()
    imports = stage_df['Modules']
    inputs = stage_df['Input']
    output_dir = stage_df['Output'][0]
    concat_dir = stage_df['Concatenate'][0]
    main.execute(imports,inputs,output_dir,concat_dir)
